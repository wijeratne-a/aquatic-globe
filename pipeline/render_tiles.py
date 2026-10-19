#!/usr/bin/env python3
"""Render per-species heatmap XYZ tiles (WebP, zoom 0–5) from AquaMaps native cells."""

from __future__ import annotations

import argparse
import json
import math
import multiprocessing as mp
import sqlite3
import sys
import time
from collections import defaultdict
from pathlib import Path

from PIL import Image

ZMIN, ZMAX = 0, 5
TILE_SIZE = 256
ALPHA_FLOOR = 0.04


def heat_color(t: float) -> tuple[int, int, int, int]:
    """Orange-red heat with alpha scaled by suitability."""
    t = max(0.0, min(1.0, t))
    r = int(40 + 215 * t)
    g = int(180 * (1 - t) + 30 * t)
    b = int(220 * (1 - t))
    a = int(255 * (0.15 + 0.85 * t))
    return r, g, b, a


def lat_lon_to_tile(lat: float, lon: float, z: int) -> tuple[int, int]:
    n = 2**z
    x = int((lon + 180.0) / 360.0 * n)
    x = max(0, min(n - 1, x))
    lat_rad = math.radians(lat)
    y = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    y = max(0, min(n - 1, y))
    return x, y


def render_tile(max_prob: float) -> Image.Image:
    if max_prob < ALPHA_FLOOR:
        return Image.new("RGBA", (TILE_SIZE, TILE_SIZE), (0, 0, 0, 0))
    return Image.new("RGBA", (TILE_SIZE, TILE_SIZE), heat_color(min(1.0, max_prob)))


def species_cells(con: sqlite3.Connection, species_id: str) -> list[tuple[float, float, float]]:
    rows = con.execute(
        """
        SELECT CenterLat AS lat, CenterLong AS lon, Probability AS prob
        FROM hcaf_species_native
        WHERE SpeciesID = ? AND Probability > 0
        """,
        (species_id,),
    ).fetchall()
    return [(float(r[0]), float(r[1]), float(r[2])) for r in rows]


def write_tiles(cells: list[tuple[float, float, float]], out_root: Path, slug: str) -> dict:
    stats = {"tilesWritten": 0, "bytes": 0, "byZoom": {}}
    for z in range(ZMIN, ZMAX + 1):
        tile_max: dict[tuple[int, int], float] = defaultdict(float)
        for lat, lon, prob in cells:
            x, y = lat_lon_to_tile(lat, lon, z)
            key = (x, y)
            if prob > tile_max[key]:
                tile_max[key] = prob
            if z >= 3:
                for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    n = 2**z
                    if 0 <= nx < n and 0 <= ny < n:
                        k2 = (nx, ny)
                        if prob * 0.85 > tile_max[k2]:
                            tile_max[k2] = prob * 0.85

        z_count = 0
        z_bytes = 0
        for (x, y), mp in tile_max.items():
            if mp < ALPHA_FLOOR:
                continue
            tile_dir = out_root / slug / str(z) / str(x)
            tile_dir.mkdir(parents=True, exist_ok=True)
            path = tile_dir / f"{y}.webp"
            img = render_tile(mp)
            img.save(path, format="WEBP", quality=82, method=4)
            z_count += 1
            z_bytes += path.stat().st_size
        stats["byZoom"][str(z)] = {"tiles": z_count, "bytes": z_bytes}
        stats["tilesWritten"] += z_count
        stats["bytes"] += z_bytes
    return stats


def load_checkpoint(path: Path) -> dict:
    if path.is_file():
        return json.loads(path.read_text())
    return {"completedSlugs": [], "species": [], "totalTiles": 0, "totalBytes": 0}


def save_checkpoint(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(path)


def render_one(args: tuple[str, str, str, str]) -> dict:
    db_path, tiles_root, species_id, slug = args
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cells = species_cells(con, species_id)
    con.close()
    st = write_tiles(cells, Path(tiles_root), slug)
    st["id"] = species_id
    st["slug"] = slug
    return st


def main() -> None:
    parser = argparse.ArgumentParser(description="Render AquaMaps heatmap tiles")
    parser.add_argument("db_path", nargs="?", default="/workspace/data/am.db")
    parser.add_argument(
        "--index",
        default="/workspace/web/public/data/species-search-index.json",
        help="Species search index JSON",
    )
    parser.add_argument("--tiles-root", default="/workspace/web/public/tiles")
    parser.add_argument("-j", "--jobs", type=int, default=max(1, mp.cpu_count() - 1))
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=25,
        help="Flush checkpoint after this many species",
    )
    args = parser.parse_args()

    db_path = Path(args.db_path)
    index_path = Path(args.index)
    tiles_root = Path(args.tiles_root)
    tiles_root.mkdir(parents=True, exist_ok=True)
    checkpoint_path = tiles_root / "render-checkpoint.json"

    index = json.loads(index_path.read_text())
    all_species = [(e["id"], e["slug"]) for e in index["entries"]]

    checkpoint = load_checkpoint(checkpoint_path)
    done = set(checkpoint.get("completedSlugs", []))
    pending = [(sid, slug) for sid, slug in all_species if slug not in done]

    print(f"Species total: {len(all_species)}, already done: {len(done)}, pending: {len(pending)}")
    if not pending:
        print("Nothing to render.")
        stats_path = tiles_root / "tile-stats.json"
        if not stats_path.is_file() and checkpoint.get("species"):
            summary = {
                "species": checkpoint["species"],
                "totalTiles": checkpoint["totalTiles"],
                "totalBytes": checkpoint["totalBytes"],
            }
            stats_path.write_text(json.dumps(summary, indent=2))
        return

    species_stats = list(checkpoint.get("species", []))
    total_tiles = int(checkpoint.get("totalTiles", 0))
    total_bytes = int(checkpoint.get("totalBytes", 0))

    work = [(str(db_path), str(tiles_root), sid, slug) for sid, slug in pending]
    jobs = max(1, args.jobs)
    batch_size = max(1, args.checkpoint_every)

    with mp.Pool(processes=jobs) as pool:
        for i, st in enumerate(pool.imap_unordered(render_one, work, chunksize=1), start=1):
            species_stats.append(st)
            total_tiles += st["tilesWritten"]
            total_bytes += st["bytes"]
            done.add(st["slug"])
            print(f"[{len(done)}/{len(all_species)}] {st['slug']}: {st['tilesWritten']} tiles")

            if i % batch_size == 0 or len(done) == len(all_species):
                checkpoint = {
                    "completedSlugs": sorted(done),
                    "species": species_stats,
                    "totalTiles": total_tiles,
                    "totalBytes": total_bytes,
                    "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
                save_checkpoint(checkpoint_path, checkpoint)

    summary = {
        "species": species_stats,
        "totalTiles": total_tiles,
        "totalBytes": total_bytes,
        "zoomMin": ZMIN,
        "zoomMax": ZMAX,
    }
    stats_path = tiles_root / "tile-stats.json"
    stats_path.write_text(json.dumps(summary, indent=2))
    print(f"Total: {total_tiles} tiles, {total_bytes / (1024 * 1024):.2f} MiB")


if __name__ == "__main__":
    main()
