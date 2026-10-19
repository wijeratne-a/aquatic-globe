#!/usr/bin/env python3
"""Render per-species heatmap XYZ tiles (WebP, zoom 0–6) from AquaMaps native cells."""

from __future__ import annotations

import json
import math
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image

ZMIN, ZMAX = 0, 6
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
            # Spread half-degree footprint to adjacent tiles at higher zoom
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


def main() -> None:
    db_path = Path(sys.argv[1] if len(sys.argv) > 1 else "/workspace/data/am.db")
    manifest_path = Path(
        sys.argv[2] if len(sys.argv) > 2 else "/workspace/web/public/data/socal-species.json"
    )
    tiles_root = Path(sys.argv[3] if len(sys.argv) > 3 else "/workspace/web/public/tiles")

    manifest = json.loads(manifest_path.read_text())
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)

    summary = {"species": [], "totalTiles": 0, "totalBytes": 0}
    for sp in manifest["species"]:
        cells = species_cells(con, sp["id"])
        slug = sp["slug"]
        st = write_tiles(cells, tiles_root, slug)
        st["id"] = sp["id"]
        st["slug"] = slug
        summary["species"].append(st)
        summary["totalTiles"] += st["tilesWritten"]
        summary["totalBytes"] += st["bytes"]
        print(f"{slug}: {st['tilesWritten']} tiles, {st['bytes'] / 1024:.1f} KiB")

    stats_path = tiles_root / "tile-stats.json"
    stats_path.write_text(json.dumps(summary, indent=2))
    print(f"Total: {summary['totalTiles']} tiles, {summary['totalBytes'] / (1024*1024):.2f} MiB")
    con.close()


if __name__ == "__main__":
    main()
