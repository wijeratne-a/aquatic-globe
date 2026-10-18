# Licensing Tracker (Track 7 — GATING)

Nothing public launches until every row below is resolved for commercial use.

## Data sources

| Source | License | Commercial use? | Status |
|---|---|---|---|
| AquaMaps range maps | CC-BY-NC 3.0 | No — needs written permission | TODO: send commercial-license request email (draft in `docs/COMMERCIAL_LICENSE_EMAIL_DRAFT.md`) |
| OBIS occurrences | Per-dataset: public domain / CC BY / CC BY-NC / permission-required | Only public-domain + CC BY datasets | TODO: quantify coverage after filtering |
| GBIF occurrences | Per-dataset: CC0 / CC BY / CC BY-NC | Only CC0 + CC BY datasets | TODO: confirm via GBIF data-use terms |
| FishBase/SeaLifeBase facts | CC-BY-NC (data) | No — needs permission or rewrite-from-source | TODO: verify against FishBase's own terms page |
| WoRMS taxonomy | Verify | TBD | TODO |
| Species photos | Per-image (Wikimedia Commons / iNaturalist / commissioned) | Only with verified license | TODO: define image pipeline rules |

## Attribution requirements (to implement on every species page)

- AquaMaps: "Range data: AquaMaps (Kaschner et al. 2019), aquamaps.org" + backlink, if licensed.
- OBIS/GBIF: per-dataset attribution strings, machine-readable.
- Photos: per-image credit line with license.

## Fallback if AquaMaps commercial use is denied

Build our own envelope models from OBIS public-domain/CC BY occurrence data (presence-only envelopes — fine for an illustrative product, not for science). Decision point documented in RESEARCH_PLAN.md Track 7.
