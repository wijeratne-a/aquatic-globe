# AquaMaps → SoCal slice pipeline

Batch pipeline for the Southern California Bight test slice: filter species from the AquaMaps SQLite database, export a web manifest, and pre-render static heatmap tiles (WebP, zoom 0–6).

## Prerequisites

- R (optional): `aquamapsdata` for `download_db()` — or download `am.db.bz2` manually
- Python 3 with `Pillow`

## Data download

```bash
# Option A: R package (≈2 GB download, ≈10 GB unpacked SQLite)
Rscript pipeline/download_db.R

# Option B: direct archive
curl -L -o data/am.db.bz2 https://archive.org/download/aquamapsdb/am.db.bz2
bunzip2 -k data/am.db.bz2   # → data/am.db
```

## SoCal species filter

Script: `filter_socal.py`

**Bounding box (cell centers):** latitude 32°N–35°N, longitude 121°W–117°W (Southern California Bight).

**Inclusion criteria:**

1. At least **2** half-degree cells inside the bbox with `Probability ≥ 0.08`
2. Sum of `Probability` over those bbox cells ≥ **0.75**
3. Rank by descending bbox probability mass; keep up to **100** species (target band **50–100**)

If fewer than 50 species pass, the script relaxes to `sum ≥ 0.375` with ≥1 cell (still capped at 100).

**Centroid** for camera fly-to: global probability-weighted mean of all native cells for the species (not bbox-only).

Outputs:

- `web/public/data/socal-species.json` — manifest + search index source
- `web/public/data/socal-species-ids.txt`

> Filter definition and resulting species count are updated in this README after each run (see **Last run** below).

## Tile render

```bash
python3 pipeline/filter_socal.py data/am.db
python3 pipeline/render_tiles.py data/am.db
```

- Format: WebP RGBA, 256×256, XYZ Web Mercator
- Zoom levels: **0–6** (native AquaMaps resolution is 0.5°; higher zooms add no detail)
- Output: `web/public/tiles/{slug}/{z}/{x}/{y}.webp`
- Stats: `web/public/tiles/tile-stats.json`

## Last run

- **Date:** 2026-10-18 (branch `cursor/aquatic-globe-socal-slice-790b`)
- **Species count:** 100 (bbox filter above; ranked by bbox probability mass, capped at 100)
- **Tiles:** 128,994 WebP files, 28.24 MiB total (`web/public/tiles/tile-stats.json`)
- **Zoom levels:** 0–6, 256×256 XYZ Web Mercator
