# AquaMaps → global species pipeline

Batch pipeline: filter all AquaMaps species with quality thresholds, export a split web manifest (compact search index + per-species JSON), and pre-render static heatmap tiles (WebP, zoom 0–5).

## Prerequisites

- R (optional): `aquamapsdata` for `download_db()` — or download `am.db.bz2` manually
- Python 3 with `Pillow`

## Data download

```bash
# Option A: R package (≈2 GB download, ≈10 GB unpacked SQLite)
Rscript pipeline/download_db.R

# Option B: direct archive
mkdir -p data
curl -L -o data/am.db.bz2 https://archive.org/download/aquamapsdb/am.db.bz2
bunzip2 -k data/am.db.bz2   # → data/am.db
```

## Global species filter

Script: `filter_species.py`

**Inclusion criteria (worldwide, no bounding box):**

1. Native half-degree cells with `Probability ≥ 0.08`
2. At least **2** such cells per species
3. Sum of `Probability` over those cells ≥ **0.75**

Species that fail are excluded (sparse or junk maps). There is no species count cap.

**Centroid** for camera fly-to: global probability-weighted mean of all qualifying cells (same `Probability ≥ 0.08` filter as above).

Outputs (gitignored; generated locally):

- `web/public/data/species-search-index.json` — compact search index (id, slug, scientific + common names only)
- `web/public/data/species/{slug}.json` — full record (centroid, taxonomy, cell counts), lazy-loaded by the web app
- `web/public/data/species-ids.txt`

```bash
python3 pipeline/filter_species.py data/am.db
```

## Tile render

```bash
python3 pipeline/filter_species.py data/am.db
python3 pipeline/render_tiles.py data/am.db -j "$(nproc)"
```

- Format: WebP RGBA, 256×256, XYZ Web Mercator
- Zoom levels: **0–5** (native AquaMaps resolution is 0.5°; z6+ adds little detail)
- Output: `web/public/tiles/{slug}/{z}/{x}/{y}.webp`
- Stats: `web/public/tiles/tile-stats.json`

**Resumable:** progress is stored in `web/public/tiles/render-checkpoint.json` (`completedSlugs`). Re-run the same command to continue after interruption.

**Parallel:** `-j N` (default: CPU count − 1). Checkpoint flush every 25 species (`--checkpoint-every`).

This is a multi-hour job for the full species set; do not run serially on a laptop without resume.

## Tile deploy artifacts

Rendered tiles are **not** committed. Package batches for CDN upload:

```bash
chmod +x pipeline/package_tiles.sh
BATCH_SIZE=500 pipeline/package_tiles.sh web/public/tiles web/public
```

Produces `web/public/tiles-batch-0001.tar.gz`, … each containing up to 500 species slug directories. Extract on the host or CDN origin:

```bash
tar -xzf tiles-batch-0001.tar.gz -C /var/www/tiles
```

The web app reads heatmaps from `VITE_TILES_BASE_URL` (default `/tiles`).

## Last run

- **Date:** 2026-10-19 (branch `cursor/aquatic-globe-global-40d1`, `data/am.db` from Archive.org)
- **Species count:** 23,696 (global filter above; 23,699 rows in `speciesoccursum_r`, 3 without qualifying native cells)
- **Search index size:** 2.40 MiB (`species-search-index.json`, compact names + slugs)
- **Per-species records:** 94 MiB total under `web/public/data/species/` (lazy-loaded JSON, not committed)
- **Tiles (partial):** full render was in progress at ~1,650 / 23,696 species → ~279k WebP files, ~61 MiB on disk; extrapolated full run ≈ **4.0M tiles / ~0.9 GiB** at z0–5 (see `render-checkpoint.json` + `tile-stats.json` when complete)
- **Zoom levels:** 0–5

**Resume tile render** (after clone + `am.db` + filter):

```bash
pip install Pillow
python3 pipeline/filter_species.py data/am.db
python3 pipeline/render_tiles.py data/am.db -j "$(nproc)"
```
