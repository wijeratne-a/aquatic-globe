#!/usr/bin/env python3
"""Filter AquaMaps species globally with quality thresholds (no regional bbox)."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

# Half-degree cells must meet this suitability to count toward range mass
MIN_CELL_PROB = 0.08
# At least this many qualifying cells worldwide
MIN_CELLS = 2
# Sum of Probability over qualifying cells (global)
MIN_PROB_SUM = 0.75


def slug(species_id: str) -> str:
    return species_id.replace(" ", "-").lower()


def main() -> None:
    db_path = Path(sys.argv[1] if len(sys.argv) > 1 else "/workspace/data/am.db")
    out_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "/workspace/web/public/data")
    species_dir = out_dir / "species"
    out_dir.mkdir(parents=True, exist_ok=True)
    species_dir.mkdir(parents=True, exist_ok=True)

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
        SELECT
          SpeciesID,
          SUM(CenterLat * Probability) / SUM(Probability) AS clat,
          SUM(CenterLong * Probability) / SUM(Probability) AS clon,
          SUM(Probability) AS prob_sum,
          COUNT(*) AS cell_count
        FROM hcaf_species_native
        WHERE Probability >= ?
        GROUP BY SpeciesID
        HAVING prob_sum >= ? AND cell_count >= ?
        ORDER BY SpeciesID
        """,
        (MIN_CELL_PROB, MIN_PROB_SUM, MIN_CELLS),
    ).fetchall()

    search_entries: list[dict] = []
    for r in rows:
        sid = r["SpeciesID"]
        m = meta_by_id.get(sid, {})
        genus = m.get("Genus") or ""
        epithet = m.get("Species") or ""
        sci = f"{genus} {epithet}".strip() or sid
        common = (m.get("FBname") or "").strip()
        sp_slug = slug(sid)
        record = {
            "id": sid,
            "slug": sp_slug,
            "scientificName": sci,
            "commonName": common,
            "centroid": {"lat": float(r["clat"]), "lon": float(r["clon"])},
            "probMass": float(r["prob_sum"]),
            "cellCount": int(r["cell_count"]),
            "taxonomy": {
                "kingdom": m.get("Kingdom"),
                "phylum": m.get("Phylum"),
                "class": m.get("Class"),
                "order": m.get("Order"),
                "family": m.get("Family"),
            },
        }
        (species_dir / f"{sp_slug}.json").write_text(json.dumps(record))
        search_entries.append(
            {
                "id": sid,
                "slug": sp_slug,
                "scientificName": sci,
                "commonName": common,
            }
        )

    search_entries.sort(key=lambda e: e["scientificName"].lower())

    index = {
        "scope": "global",
        "filter": {
            "minCellProb": MIN_CELL_PROB,
            "minCells": MIN_CELLS,
            "minProbSum": MIN_PROB_SUM,
            "description": (
                "Species with at least minCells native cells at Probability >= minCellProb "
                "and sum(Probability) >= minProbSum over those cells"
            ),
        },
        "speciesCount": len(search_entries),
        "entries": search_entries,
    }

    index_path = out_dir / "species-search-index.json"
    index_path.write_text(json.dumps(index, separators=(",", ":")))
    ids_path = out_dir / "species-ids.txt"
    ids_path.write_text("\n".join(e["id"] for e in search_entries) + "\n")

    index_bytes = index_path.stat().st_size
    print(f"Wrote {len(search_entries)} species")
    print(f"Search index: {index_path} ({index_bytes / (1024 * 1024):.2f} MiB)")
    con.close()


if __name__ == "__main__":
    main()
