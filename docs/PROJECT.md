# Aquatic Globe — Build Brief for Agents

## What we're building

A Google-Earth-style interactive 3D globe website. User searches/selects any aquatic species → sees a heatmap of where that species lives. One SEO page per species (33.5k eventually; ~500 charismatic species for MVP).

## Non-goals

- No science-grade modeling (that's the separate FishAI project).
- No live tracking, no real-time data. Illustrative ranges only.
- No user accounts, no mobile app, no non-English locales in MVP.

## Build order (from RESEARCH_PLAN.md)

1. **Licensing (Track 7) — FIRST, gates launch.** AquaMaps is CC-BY-NC. Draft the commercial-license request email; research the OBIS per-dataset-license fallback in parallel.
2. **Globe tech spike (Track 1).** Prototype the same species heatmap + camera fly-to in CesiumJS and globe.gl (Three.js). Measure FPS on a mid-range mobile device and JS bundle size. Pick one.
3. **Data pipeline pilot (Track 2).** `aquamapsdata` R package → SQLite (~2 GB download, ~10 GB unpacked) → per-species tiles for 100 species. Decide raster (WebP) vs vector (MVT), zoom cap (native res is 0.5° cells — high zooms are waste), static files + CDN (no tile server).
4. **Search (Track 4).** <50ms autocomplete over scientific + common names + synonyms (WoRMS taxonomy). Typesense/Meilisearch self-hosted vs client-side trie.
5. **Species pages + SEO (Track 6).** Page template, Bioschemas Taxon markup, sitemap architecture, OG images.
6. **Cost model (Track 3).** Bytes/visit → $/month at 1M and 10M visitors. Cloudflare R2 (zero egress) is the default hypothesis.
7. **Viral formats (Track 5)** and **rollout (Track 8)** run in parallel with the build.

## Conventions

- Repo is public. Code is ours; the licensing gate (docs/LICENSING.md) applies to data and launch, not to the code.
- Small PRs, one track per PR. No direct pushes to main.
- Every map UI ships with the "illustrative range" label — no exceptions.
- Cite data sources on every species page (AquaMaps: Kaschner et al. 2019, verify exact ref; OBIS; FishBase/SeaLifeBase; WoRMS).
- Cost policy: composer-2.5 for coding/execution, grok-4.7 for thinking/diagnosis/design.
