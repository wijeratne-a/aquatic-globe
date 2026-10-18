# Aquatic Species Globe — Research Plan

**Status:** Plan only (no build yet). Purpose: de-risk and sequence the build of a Google-Earth-style interactive 3D globe website where users search any aquatic species and see an illustrative range heatmap — optimized for social virality and programmatic SEO (one page per species).

**Core product thesis:** AquaMaps (33,500+ species range maps) and OBIS (occurrence records) already contain the data. No modern consumer UX exists on top of it — AquaMaps looks like 2006, OBIS is a research tool. The gap is experience, not science. Data is illustrative range only; labels must always say "illustrative range," never imply live tracking.

**Hard constraints for all tracks:**
- Every map carries an "illustrative range" label and a plain-language disclaimer that these are modeled ranges, not live animal positions.
- Honest labeling is non-negotiable: AquaMaps maps are "fairly reliable large-scale predictions, many not expert-verified" per their own disclaimer.
- Commercial-use licensing must be resolved BEFORE any public launch (Track 7 is the gating track).

---

## Track 1 — Globe rendering tech

Goal: pick the WebGL globe framework that delivers the "Google Earth feel" on desktop and mid-range mobile.

### Key questions
1. CesiumJS vs Three.js custom globe (globe.gl) vs deck.gl GlobeView vs MapLibre GL JS (globe projection): compare on (a) visual quality of search-zoom camera flights, (b) mobile frame rate on a mid-range Android, (c) heatmap tile overlay ease, (d) JS bundle size, (e) license/cost.
2. Can we get cinematic camera fly-to animations (search → spin → zoom to species centroid) out of the box, or do we need custom easing?
3. Which option supports atmosphere glow, day/night terminator, and bathymetry-styled oceans with the least custom shader work?
4. What is the WebGL fallback story for old browsers (graceful 2D fallback vs blank screen)?

### Where to look
- CesiumJS: Apache 2.0, free for commercial use — the paid part is only Cesium ion (hosted terrain/imagery/tiling); self-hosting our own tiles avoids ion entirely. Ion commercial plans start at $149/mo (100 GB storage, 150 GB streaming) if we ever want their curated imagery. Source: https://cesium.com/platform/cesium-ion/pricing/
- globe.gl (Three.js wrapper, MIT): purpose-built for exactly this "wow globe" UX — atmosphere, arcs, heatmaps via `Globe` layers. Check bundle size with tree-shaking and mobile FPS benchmarks. Source: github.com/turban/webgl-earth and globe.gl repos.
- deck.gl GlobeView: **experimental** per its own docs — no high-precision rendering above zoom 12, HeatmapLayer and ContourLayer do NOT work in GlobeView, TileLayer/MVTLayer support experimental, MaskExtension unsupported. Likely a disqualifier unless we only need low-zoom heatmaps. Source: https://deck.gl/docs/api-reference/core/globe-view
- MapLibre GL JS: open-source Mapbox fork, vector-tile native, has been adding globe projection — verify maturity and heatmap-in-globe support.
- Build a 2-day spike: same species heatmap + same camera flight in CesiumJS and globe.gl, measure FPS on a Pixel-class device and bundle KB.

### Definition of done
- One-page decision memo naming the framework, with measured FPS numbers, bundle size, and a yes/no on native fly-to animation quality. Prototype code committed.

---

## Track 2 — Data pipeline: AquaMaps SQLite → fast per-species tiles

Goal: a repeatable pipeline from raw AquaMaps data to web-served per-species heatmap tiles.

### Key questions
1. Using the `aquamapsdata` R package: confirm the download works today (~2 GB down, ~10 GB unpacked into SQLite), inspect schema (species IDs, 0.5° grid cells, probability values), and confirm coverage count (~33.5k species).
2. Tile format choice: pre-rendered raster tiles (PNG/WebP per species per zoom) vs vector MVT with client-side styling vs single global tileset with per-species filtering. Trade off storage size, first-paint speed, and style flexibility.
3. Storage math: work the numbers for all 33.5k species at zooms 0–8 as WebP (estimate per-species tile set size from a 100-species pilot; multiply). AquaMaps' native resolution is 0.5° cells, so very high zooms add nothing — cap zoom and quantify savings.
4. Tile server: self-hosted (e.g., static files on object storage + CDN — no tile server needed if tiles are pre-rendered) vs dynamic server (TiTiler / Martin / Tegola). Static pre-rendered + CDN is strongly preferred for cost.
5. Update cadence: AquaMaps releases roughly annually — design pipeline as a re-runnable batch job, not a live sync. Verify their release cadence and whether the R package tracks versions.
6. Occurrence dots layer: OBIS API / R package for per-species occurrence points (Darwin Core) — decide whether dots render client-side (GeoJSON, capped at N points) or as a second tile layer. GBIF API as backup source.

### Where to look
- `aquamapsdata` package docs and README (rdrr.io / GitHub raquamaps/aquamapsdata) — includes the CC-BY-NC terms and contacts (Rainer Froese, Kristin Kaschner).
- TiTiler docs (Cloud-Optimized GeoTIFF + dynamic tiling as an alternative to pre-rendering).
- Martin (PostGIS → MVT) and tippecanoe (vector tile generation) docs for the MVT route.
- OBIS API docs (api.obis.org) and the `robis` R package; GBIF API docs (api.gbif.org).
- Case studies: how Map of Life / eBird serve range tiles.

### Definition of done
- Working pipeline script that takes species IDs in and emits tiles out for a 100-species pilot, with measured per-species storage and render time, and a documented recommendation (raster vs vector, zoom cap, server vs static).

---

## Track 3 — Performance & cost at scale

Goal: know the infra bill at 1M and 10M monthly visitors before launch, and the CDN architecture that survives 100k concurrent users.

### Key questions
1. CDN strategy: Cloudflare (free CDN tier, R2 zero-egress storage) vs S3 + CloudFront vs alternatives. Quantify with our tile-size measurements from Track 2.
2. What does a typical visit cost in bytes? (initial page + globe framework + one species tile set + species page assets). Model: visitors × pages/visit × bytes.
3. Lazy loading: only load the globe on the homepage; species pages load a static preview image first, globe on interaction? Measure LCP impact.
4. Level of detail: low-zoom tiles only until user zooms; cap max zoom at the native 0.5° resolution — no wasted high-zoom tiles.
5. 100k concurrent: static tiles on CDN = trivially scalable; the only dynamic parts are search API and species page HTML — put both behind edge caching (Cloudflare Workers / Vercel Edge).
6. Cost model outputs: monthly infra $ at 1M visitors and 10M visitors, with the two biggest cost drivers named.

### Where to look (already partially answered — verify with our numbers)
- Cloudflare R2: $0.015/GB storage, $0.36/M read ops, **$0 egress** — vs S3+CloudFront ~$0.09/GB egress. Published comparison: 10 TB stored / 50 TB served per month ≈ $62–190 on R2 vs ~$4,379 on S3+CloudFront. Sources: https://leanopstech.com/blog/cloudflare-r2-vs-aws-s3-decision-framework-2026/ , https://devops-daily.com/posts/object-storage-free-egress-fine-print
- Cloudflare's free CDN tier terms: fine for HTML/small assets, but confirm the "disproportionate non-HTML" fair-use language doesn't bite for a tile-heavy site — R2 + paid plan may be the safer framing.
- WebPageTest / Lighthouse budgets for the species page template.

### Definition of done
- One-page cost model spreadsheet: bytes/visit → $/month at 1M and 10M visitors for R2+Cloudflare vs S3+CloudFront, plus a CDN architecture diagram. Go/no-go on "can we afford virality."

---

## Track 4 — Search & UX

Goal: instant species search across 33.5k+ species (scientific + common names + synonyms) and a "wow" selection moment.

### Key questions
1. Search index: 33.5k species × multiple common names (FishBase alone has 332k common names) × synonyms — options: hosted (Algolia/Typesense Cloud), self-hosted (Typesense/Meilisearch on a $10 VM), or client-side (prebuilt trie shipped with the app). Compare latency, cost, and typo tolerance.
2. Taxonomy backbone: WoRMS for accepted names + synonym resolution — how to keep the index in sync, and how to handle name changes.
3. Autocomplete UX: sub-50ms results, scientific name + common name + thumbnail in the dropdown, keyboard navigable, works on mobile.
4. The "wow" animation: on select → camera flies from current view to species range centroid with an ease curve, heatmap fades/scales in. Storyboard the exact 2–3 second sequence.
5. Mobile-first: globe must be touch-usable and readable on a phone; species info as a bottom sheet, not a sidebar.
6. Accessibility baseline: keyboard operation, reduced-motion respect for the fly-to.

### Where to look
- Typesense and Meilisearch docs (typo tolerance, faceting, self-host cost).
- WoRMS API (marinespecies.org) for taxonomy/synonyms.
- Framer-motion / camera easing references; study Google Earth's search-zoom feel frame by frame.

### Definition of done
- Search prototype hitting <50ms autocomplete over the full name index, plus a recorded video of the select→fly-to animation on desktop and mobile. UX storyboard signed off.

---

## Track 5 — Viral UI patterns

Goal: learn what makes map/globe content go viral on TikTok/Reels/Shorts, and bake shareability into the product.

### Key questions
1. What are the proven viral formats? (Hypotheses: "where do great white sharks actually live?" hook + 3D zoom reveal; range-map reaction duets; "animal you didn't know lived near you" geo-personalization.) Validate against real examples.
2. Which ocean/nature accounts get the most shares, and what do their top 10 videos have in common (hook in first 2 seconds, captions, sound, length)?
3. Product features for shareability: one-tap "share as video" (render the fly-to as an MP4/GIF client-side?), deep links that open the globe mid-animation, embeddable iframe widget for bloggers/newsletters.
4. Watermarking: subtle brand mark on shared videos that survives re-uploads.
5. What is the daily content engine? (Track 8 builds on this — here just define the repeatable video template.)

### Where to look
- TikTok Creative Center top-ads/trending (organic, not paid); manual survey of ocean-education accounts.
- Case studies: how "The Pudding"-style visual essays and map-Tok accounts grew.
- Libraries for client-side canvas→video capture (MediaRecorder API on the WebGL canvas).

### Definition of done
- Memo with 5 validated viral formats (each with 2–3 real example videos linked), plus a spec for the in-product "share as video" feature and the embed widget.

---

## Track 6 — Species pages & programmatic SEO

Goal: 33.5k indexable species pages that rank for "where does X live" queries.

### Key questions
1. URL structure: `/species/<scientific-name-slug>` vs `/species/<common-name>` — pick one canonical, handle synonyms with redirects.
2. Content per page (must be unique enough to avoid thin-content penalties): interactive globe embed, static OG map image, facts (taxonomy, size, habitat, depth range from FishBase/SeaLifeBase), 2–4 images, "related species" internal links, FAQ block targeting long-tail queries.
3. Structured data: Bioschemas Taxon profile (schema.org has no native Species type — verify) + FAQPage + ImageObject; validate with Google's Rich Results Test.
4. Programmatic SEO mechanics: sitemap index (33.5k URLs chunked), crawl budget management, internal linking graph (taxonomy browse pages: by family, by region, by "charisma"), prerendering/SSR for crawlers.
5. Image pipeline: one hero image per species — source, license check (Track 7), resize/WebP, OG tags.
6. Launch order: MVP pages for ~500 charismatic species first (Track 9), then expand — how to avoid Google seeing 33k thin pages on day one.

### Where to look
- Bioschemas (bioschemas.org) Taxon profile spec.
- Programmatic SEO playbooks (e.g., how iNaturalist, Animalia.bio, or similar structured-data sites scaled pages).
- Next.js/Astro ISR docs for 33k-page static generation strategy.

### Definition of done
- Page template built and validated (Lighthouse, Rich Results Test, OG preview), sitemap architecture documented, and a content-uniqueness checklist per page.

---

## Track 7 — Licensing & legal (GATING TRACK — do first)

Goal: a commercial-use-clean data and media stack, with every attribution requirement documented. **Nothing launches until this is resolved.**

### Key questions
1. **AquaMaps is CC-BY-NC 3.0** ("for non-commercial use... clearly identified as coming from AquaMaps, with a backward link"). An ad-supported or monetized traffic site is commercial use. Options to research: (a) contact the AquaMaps team (Rainer Froese rfroese@geomar.de, Kristin Kaschner) to negotiate a commercial license — the `aquamapsdata` README explicitly invites contact; (b) operate the site non-commercially (no ads — kills the business model); (c) build our own envelope models from OBIS occurrence data instead of using AquaMaps rasters. Get a written answer, not an assumption.
2. OBIS occurrence data: licenses are **per-dataset** (public domain, CC BY, CC BY-NC, or permission-required). For commercial use, filter to public-domain/CC BY datasets only — quantify how much coverage remains after filtering. OBIS-SEAMAP's FAQ documents the per-dataset options. Source: https://seamap.env.duke.edu/content/user_faq
3. GBIF: same per-dataset filtering (CC0/CC BY/CC BY-NC) — confirm via GBIF's data-use terms.
4. FishBase/SeaLifeBase data: CC-BY-NC per Wikipedia's summary — same commercial-use problem as AquaMaps for facts content; media (photos) is case-by-case licensing. Verify against FishBase's own terms page rather than relying on Wikipedia.
5. Species photos: build a license-clean image pipeline — options: Wikimedia Commons (verify each image's license), iNaturalist (per-observation licenses, many CC), commissioned illustrations. No hotlinking FishBase photos (their copyright statement says photos belong to indicated persons/organizations).
6. Attribution system: every species page needs machine-readable attribution (source, license, link-back) — design the footer/credits component now.
7. Privacy/TOS: standard website privacy policy, cookie consent, terms of use for the embed widget.

### Where to look
- AquaMaps terms (via aquamaps.org and the `aquamapsdata` README copyright section); direct email to the AquaMaps team for commercial licensing.
- OBIS-SEAMAP FAQ (per-dataset license table); GBIF data use agreement.
- FishBase/SeaLifeBase terms pages; a media-licensing consult or qualified IP lawyer for the final sign-off before launch.

### Definition of done
- Written licensing decision: which datasets are cleared for commercial use (with the actual permission emails/licenses filed), per-species-page attribution spec, and image pipeline license rules. If AquaMaps commercial use is denied, the pivot (OBIS-derived envelopes) is decided here.

---

## Track 8 — Rollout plan

Goal: launch sequence and content engine that convert the build into traffic.

### Key questions
1. Launch sequence: soft launch (500 species, SEO indexing begins) → social content engine starts → PR/launch moment (Product Hunt? Hacker News "we put 33k species on a globe"?) → scale to full catalog.
2. Social content engine: daily species video template (hook + globe zoom + 1 fact + CTA), posting cadence per platform, who produces (founder-shot vs hired editor vs automated rendering pipeline).
3. Can video generation be automated? (Script renders the fly-to headlessly → MP4 → scheduled posts.) Research headless WebGL rendering options.
4. Metrics to watch: organic search impressions/clicks per page cohort, social follower growth, share rate, return-visitor rate, pages/session, infra cost per 1k visitors. Define the dashboard before launch.
5. Monetization timing: when do ads/affiliates/sponsorships turn on without hurting growth? (Note: monetization choice interacts with Track 7 licensing.)
6. Moat: what stops a clone? (Brand, content library, SEO authority, data pipeline speed — be honest about how thin the moat is.)

### Where to look
- Launch postmortems from programmatic-SEO + social-loop products.
- Headless Chrome/WebGL video rendering tooling (e.g., puppeteer + MediaRecorder, or server-side rendering services).

### Definition of done
- Dated launch checklist, 30-day content calendar template, metrics dashboard spec, and a monetization decision with timing.

---

## Track 9 — Build sequencing (MVP → full)

Goal: phased milestones so something shippable exists in weeks, not quarters.

### Key questions
1. What is the MVP? Proposed: globe + search + ~500 charismatic species pages (sharks, whales, turtles, game fish, aquarium species) with heatmaps, facts, images, and shareable video export. Everything else is phase 2.
2. How are the 500 chosen? (Search volume for "where does X live" + social virality potential + data completeness in AquaMaps.)
3. Phase 2: expand to 5k species, add occurrence dots, embed widget.
4. Phase 3: full 33.5k, taxonomy browse, region pages, API for developers?
5. What is deliberately cut from MVP? (User accounts, live data, mobile app, non-English locales.)

### Definition of done
- Milestone list with scope per phase and ship criteria; the 500-species seed list.

---

## Prioritized order of operations

1. **Track 7 — Licensing & legal (3–5 days, FIRST).** This gates everything: if AquaMaps can't be used commercially, the data strategy changes completely. Send the commercial-license email to the AquaMaps team on day one; research the OBIS-filtered fallback in parallel.
2. **Track 1 — Globe tech spike (1–2 weeks).** Framework decision with measured numbers. Runs in parallel with waiting on the licensing email.
3. **Track 2 — Data pipeline pilot (1–2 weeks).** 100-species tile pilot → storage math → format decision. Starts as soon as Track 7 gives a provisional data-source answer.
4. **Track 4 — Search prototype (3–5 days).** Can run parallel to Track 2.
5. **Track 6 — Species page template + SEO architecture (1 week).** Needs Track 7's image-licensing rules.
6. **Track 3 — Cost model (2–3 days).** Needs Track 2's byte measurements. Answers "can we afford to go viral."
7. **Track 5 — Viral format research (1 week, parallel anytime).** Feeds Track 8.
8. **Track 8 — Rollout plan (3–5 days).** Last — it depends on all of the above.
9. **Track 9 — Sequencing (2–3 days).** Written alongside Track 8; the 500-species list needs Track 2 data + keyword research.

**Total research effort: roughly 6–9 weeks for one person, compressible to ~4 weeks with parallel tracks (legal + tech spike + viral research concurrently).** Build effort estimate comes after the research — do not commit to build timelines until Tracks 1–3 report.

## Key findings already established (shortcuts for the research)

- CesiumJS is Apache 2.0 and free for commercial use; only Cesium ion's hosted services are paid (from $149/mo). Self-hosted tiles avoid ion. — https://cesium.com/platform/cesium-ion/pricing/
- deck.gl's GlobeView is experimental with hard limitations (no HeatmapLayer/ContourLayer, no precision above zoom 12) — likely disqualified. — https://deck.gl/docs/api-reference/core/globe-view
- AquaMaps content is CC-BY-NC 3.0 — commercial use requires permission. Contacts: Rainer Froese (rfroese@geomar.de), Kristin Kaschner. — `aquamapsdata` README (rdrr.io)
- OBIS data licenses vary per dataset (public domain / CC BY / CC BY-NC / permission required) — commercial use requires filtering. — https://seamap.env.duke.edu/content/user_faq
- FishBase data is CC-BY-NC; SeaLifeBase CC-BY-NC; photos licensed case-by-case. — https://en.wikipedia.org/wiki/FishBase
- Tile serving: Cloudflare R2 ($0.015/GB storage, $0 egress) vs S3+CloudFront (~$0.09/GB egress) — at 10 TB stored / 50 TB served per month, roughly $62–190 vs ~$4,379. — https://leanopstech.com/blog/cloudflare-r2-vs-aws-s3-decision-framework-2026/
- `aquamapsdata` R package: ~2 GB download, ~10 GB unpacked SQLite. Citation: Kaschner et al. 2019 (verify exact reference before publishing).

## Open questions for the founder

- Is the business model ad-supported traffic (which forces the commercial-licensing question), or is there a non-commercial/grant-funded framing that sidesteps CC-BY-NC?
- Budget tolerance for infra at viral scale (Track 3 will put numbers on this)?
- Who makes the daily social videos — founder, hired editor, or automated pipeline?
