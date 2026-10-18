# Aquatic Globe

An interactive Google-Earth-style 3D globe website: search any aquatic species (fish, marine mammals, invertebrates) and see an illustrative range heatmap — like the range maps in biology textbooks, but interactive, beautiful, and fast.

**Product thesis:** the data already exists (AquaMaps: 33,500+ species range maps; OBIS: occurrence records). No modern consumer UX exists on top of it. The gap is experience, not science. Traffic via social virality + programmatic SEO (one page per species).

**This is a separate project from FishAI** (the rigorous species-distribution modeling project). This globe is the illustrative/traffic product. It deliberately does not do science-grade modeling.

## Hard rules

1. **Illustrative only.** Every map is labeled "illustrative range." Never imply live animal positions or real-time tracking.
2. **Honest labeling.** AquaMaps maps are "fairly reliable large-scale predictions, many not expert-verified" (their words). Say so.
3. **Licensing gate.** AquaMaps is CC-BY-NC; FishBase/SeaLifeBase data is CC-BY-NC; OBIS/GBIF licenses vary per dataset. Nothing public launches until commercial-use licensing is resolved — see `docs/LICENSING.md`. This is Track 7 of the research plan and it gates everything.
4. **Mobile-first.** The globe must be fast and usable on a mid-range phone.

## Status

Early build. See `docs/RESEARCH_PLAN.md` for the full research plan (9 tracks) and `docs/PROJECT.md` for the agent build brief.

## Repo layout (planned)

- `web/` — the site (framework TBD by Track 1 spike: CesiumJS vs globe.gl)
- `pipeline/` — AquaMaps SQLite → per-species tiles (Track 2)
- `search/` — species name index (Track 4)
- `docs/` — research plan, licensing, project briefs
- `data/` — local only, never committed (see `.gitignore`)
