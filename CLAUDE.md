# CLAUDE.md – regenradar

Project rules and current status for Claude. Read this file and `ROADMAP.md` at the start of every session.

## What this is

Data pipeline for a Switzerland-wide precipitation layer based on MeteoSwiss Open Data:
radar (measured, −3 h … now) and nowcast (forecast, now … +6 h). The pipeline turns the
source files into transparent PNG images (Web Mercator) plus an `index.json` with time stamps.

**No own frontend.** The images are shown as a layer «Regen» in the map of
[maleanso/meteocam](https://github.com/maleanso/meteocam) (Leaflet). meteocam only reads the
public images via URL; the two repos stay independent.

Owner: Chris (maleanso). Repo is **public**, **no licence** (all rights reserved) – do not add a LICENSE file.

## Working rules (from the owner – always follow)

- Answer Chris in **German** (Swiss spelling, no «ß»).
- Explain steps in **small portions, one at a time** (he may need to upload a screenshot between steps).
- **No app code without the word «entwickle»** from Chris. Docs, plans and questions are fine.
- **Nothing lands on `main` without the word «deploy»** from Chris. Work on feature branches.
- Read `CLAUDE.md` and `ROADMAP.md` at the start of every session.
- Changes in meteocam (the «Regen» layer) follow meteocam's own rules and CLAUDE.md.

## Conventions

- Code, code comments, commit messages: **English**. Docs and UI texts: **German**.
- Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `test:`, `refactor:`, `ci:`), scopes `pipeline`, `docs`, `ci`.
- Semantic Versioning, `CHANGELOG.md` (Keep a Changelog), tag `vX.Y.Z` on every release.
- Architecture decisions as short ADRs in `docs/entscheide/`.
- Tests with pytest, small sample files in `pipeline/tests/data/`.
- Python only; no libraries with licence fees or watermarks (e.g. no WeatherLayers GL).

## Data and attribution

- Source must always be shown: **«Source: MeteoSwiss»** (CC BY).
- Colour scale: **same steps as MeteoSwiss** (mandatory, values documented in `docs/daten.md`).
- Note in every view: **not an official aviation weather product**.
- Formats, grids, projection and units are verified on real files and documented in `docs/daten.md`
  **before** processing is built.

## Security

- No secrets in the repo. R2 credentials only as GitHub Actions secrets; locally `.env` (gitignored), template `.env.example`.
- Public repo: workflows from forks get no secrets – keep it that way.
- The radar bucket is public-read and contains only derived MeteoSwiss images. meteocam's camera bucket stays private and is never touched by this repo.

## Architecture (short – details in docs/architektur.md)

- `/pipeline` – Python job: fetch newest files via STAC, convert to mm/h, reproject to EPSG:3857, render PNG with MeteoSwiss colour scale, write `index.json`, delete images outside −3 h.
- Runs every 5–10 min via GitHub Actions cron (ADR 0001).
- Output: own Cloudflare R2 bucket, public read (planned custom domain e.g. `radar.meteocam.ch`).
- Display: meteocam map layer (see ROADMAP «Integration meteocam»).

## Current status

- 2026-11-27: Repo was empty. Scope agreed with Chris: pipeline only, display in meteocam, public repo without licence. Branch `docs/grundstruktur`: docs scaffold, ADR 0001. No app code yet. Next: step 2 (analyse one radar and one nowcast file → `docs/daten.md`).
- 2026-11-27: Radar PRECIP verified on a real file (float64 mm/h, NaN = no data, 0 = no rain, 710×640 @ 1 km LV95, x 2255000–2965000, y 840000–1480000, row 0 north, asset prefix `rzc` lowercase, file time = interval end). INCA not open → ADR 0002 (pysteps extrapolation 0–2 h + ICON-CH1 TOT_PREC 2–6 h). pysteps has NO MeteoSwiss colour scale; Colour scale read from Chris' MeteoSwiss app legend screenshot (9 steps 0.2/1/2/4/6/10/20/40/60 mm/h, < 0.2 transparent, RGB in docs/daten.md), approved by Chris 2026-11-27. Domain data.geo.admin.ch allowed for the session shell. ICON-CH1: one STAC item per run×variable×horizon×ctrl/perturbed, search via POST /search with forecast:* fields; files on rgw.cscs.ch (signed URLs, domain allowed). Verified: GRIB2 via eccodes, tp kg m-2 accumulated since run start (hourly = diff of consecutive steps), unstructured grid 1147980 pts, coords tlon/tlat in horizontal constants (37 MB, uuidOfHGrid 17643da2…), run ready ~4 h after start. Step 2 complete. Chris wants a data-age warning + «nur für Versuchszwecke» in meteocam (ROADMAP R6). Next: step 3 pipeline after «entwickle».
- 2026-11-27: Chris «entwickle» → pipeline v0.1.0 on branch `feat/pipeline` (based on `docs/grundstruktur`): `pipeline/regenradar/{colors,grid,render,http,radar,icon,store,pipeline,cli}.py`, `python -m regenradar run --out DIR | --r2`, 18 tests (real radar sample in tests/data). Target grid Web Mercator 1486×1260, 720 m px, bounds 2.79–12.41° E / 43.70–49.30° N. Keys `radar/<end>.png`, `model/<run>/<end>.png`, `index.json` (see docs/architektur.md). Model frames start at now (`model_start` 0) until extrapolation (3b) exists. Real local run: 36 radar + 7 model frames in 27 s (2 s incremental); georeferencing checked against Natural Earth borders/lakes (22.11.2026 12:00 UTC). eccodes: `codes_grib_new_from_file` needs a real file → `split_messages` + `codes_new_from_message`. Shell cannot reach map tiles (swisstopo/OpenTopoMap); raw.githubusercontent.com works. Next: 3b extrapolation or step 4 meteocam layer (needs «entwickle» in meteocam), step 5 cron + R2 (needs «deploy»).
- 2026-11-27: Workflows `.github/workflows/pipeline.yml` (cron */5, R2 secrets, cache ~/.cache/regenradar) and `test.yml` on `feat/pipeline`; `docs/betrieb.md` = R2/CORS/token/secrets checklist. meteocam layer done on meteocam branch `dev/rr-regen-layer` (var RADAR_INDEX, ADR 0018 there), R1–R6 done; R2 = METAR moved left too. Deploy plan: merge to main here, set default branch main, Cloudflare bucket `regenradar` + custom domain radar.meteocam.ch + CORS + token, GitHub secrets, run workflow, then meteocam RADAR_INDEX + release 0.81.0.
- Empty repo note: `main` has no commit yet; the first pushed branch shows as default on GitHub until `main` exists (created on first «deploy»).
