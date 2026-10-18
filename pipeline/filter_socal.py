#!/usr/bin/env python3
"""Filter AquaMaps species to Southern California Bight slice."""

from __future__ import annotations

import json
import math
import sqlite3
import sys
from pathlib import Path

# Southern California Bight bounding box (inclusive on cell centers)
LAT_MIN, LAT_MAX = 32.0, 35.0
LON_MIN, LON_MAX = -121.0, -117.0

# Meaningful probability mass: at least this sum of Probability in bbox cells
MIN_BBOX_PROB_SUM = 0.75
# At least this many half-degree cells with non-trivial suitability inside bbox
MIN_BBOX_CELLS = 2
MIN_CELL_PROB = 0.08

# Cap species count for the pilot slice
TARGET_MIN = 50
TARGET_MAX = 100


def slug(species_id: str) -> str:
    return species_id.replace(" ", "-").lower()


def main() -> None:
    db_path = Path(sys.argv[1] if len(sys.argv) > 1 else "/workspace/data/am.db")
    out_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "/workspace/web/public/data")
    out_dir.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row

    meta = con.execute(
        """
        SELECT SpeciesID, Genus, Species, FBname, Kingdom, Phylum, Class, `Order`, Family
        FROM speciesoccursum_r
        """
    ).fetchall()
    meta_by_id = {r["SpeciesID"]: dict(r) for r in meta}

    rows = con.execute(
        """
        SELECT SpeciesID, CenterLat AS lat, CenterLong AS lon, Probability AS prob
        FROM hcaf_species_native
        WHERE CenterLat BETWEEN ? AND ?
          AND CenterLong BETWEEN ? AND ?
          AND Probability >= ?
        """,
        (LAT_MIN, LAT_MAX, LON_MIN, LON_MAX, MIN_CELL_PROB),
    ).fetchall()

    bbox_stats: dict[str, dict] = {}
    for r in rows:
        sid = r["SpeciesID"]
        st = bbox_stats.setdefault(sid, {"prob_sum": 0.0, "cell_count": 0})
        st["prob_sum"] += float(r["prob"])
        st["cell_count"] += 1

    candidates = [
        sid
        for sid, st in bbox_stats.items()
        if st["prob_sum"] >= MIN_BBOX_PROB_SUM and st["cell_count"] >= MIN_BBOX_CELLS
    ]

    # Rank by bbox probability mass (charismatic SoCal relevance proxy)
    candidates.sort(key=lambda s: bbox_stats[s]["prob_sum"], reverse=True)

    if len(candidates) > TARGET_MAX:
        candidates = candidates[:TARGET_MAX]
    elif len(candidates) < TARGET_MIN:
        # Relax cell threshold once if we are short
        relaxed = [
            sid
            for sid, st in bbox_stats.items()
            if st["prob_sum"] >= MIN_BBOX_PROB_SUM * 0.5 and st["cell_count"] >= 1
        ]
        relaxed.sort(key=lambda s: bbox_stats[s]["prob_sum"], reverse=True)
        candidates = relaxed[:TARGET_MAX]

    species_list = []
    for sid in candidates:
        cells = con.execute(
            """
            SELECT CenterLat AS lat, CenterLong AS lon, Probability AS prob
            FROM hcaf_species_native
            WHERE SpeciesID = ?
            """,
            (sid,),
        ).fetchall()
        if not cells:
            continue
        total_p = sum(float(c["prob"]) for c in cells)
        clat = sum(float(c["lat"]) * float(c["prob"]) for c in cells) / total_p
        clon = sum(float(c["lon"]) * float(c["prob"]) for c in cells) / total_p
        m = meta_by_id.get(sid, {})
        genus = m.get("Genus") or ""
        epithet = m.get("Species") or ""
        sci = f"{genus} {epithet}".strip() or sid
        common = (m.get("FBname") or "").strip()
        species_list.append(
            {
                "id": sid,
                "slug": slug(sid),
                "scientificName": sci,
                "commonName": common,
                "centroid": {"lat": clat, "lon": clon},
                "bboxMass": bbox_stats[sid]["prob_sum"],
                "bboxCells": bbox_stats[sid]["cell_count"],
                "taxonomy": {
                    "kingdom": m.get("Kingdom"),
                    "phylum": m.get("Phylum"),
                    "class": m.get("Class"),
                    "order": m.get("Order"),
                    "family": m.get("Family"),
                },
            }
        )

    species_list.sort(key=lambda s: s["scientificName"].lower())

    manifest = {
        "region": "Southern California Bight",
        "bbox": {"latMin": LAT_MIN, "latMax": LAT_MAX, "lonMin": LON_MIN, "lonMax": LON_MAX},
        "filter": {
            "minBboxProbSum": MIN_BBOX_PROB_SUM,
            "minBboxCells": MIN_BBOX_CELLS,
            "minCellProb": MIN_CELL_PROB,
            "targetSpeciesRange": [TARGET_MIN, TARGET_MAX],
            "ranking": "descending sum(Probability) for cells with center inside bbox",
        },
        "speciesCount": len(species_list),
        "species": species_list,
    }

    out_path = out_dir / "socal-species.json"
    out_path.write_text(json.dumps(manifest, indent=2))
    ids_path = out_dir / "socal-species-ids.txt"
    ids_path.write_text("\n".join(s["id"] for s in species_list) + "\n")

    print(f"Wrote {len(species_list)} species to {out_path}")
    con.close()


if __name__ == "__main__":
    main()
