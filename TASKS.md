# Tasks for parallel cloud sessions

Start each as its own Claude Code cloud session on this repository and paste the prompt.
Each session reads CLAUDE.md and STATE.md, works in its own files, and pushes to `main`
(pull/rebase before pushing, since other sessions push too).

## A. Discussion section (start now)
> Read CLAUDE.md, STATE.md and the manuscript builders in paper/methods/. Draft Section 4 "Discussion"
> (about 1300-1600 words) as a new module paper/methods/discussion.js called from build_methods.js after
> the Methodology (leave a Results placeholder section 3 with a one-line note). Cover: (4.1) what the
> yield-constrained potential means against the national estimates (TERI 1.2-2.1 TW, Fraunhofer/EY/CSTEP
> 3.2-13.8 TW, Mehta and Betz 2026) and why they differ (crop filter, fixed power density); (4.2) why
> management matters: low nitrogen hides shade loss (N dilution), with the Rajasthan pilot evidence in
> STATE.md and the robust (minimum of calibrated and recommended N) estimate; (4.3) crops and layouts:
> legumes shade-sensitive (Laub et al. 2022), cereals tolerant, east-west vs south vs vertical; the DIN
> SPEC 91434 15% land-loss limit for the vertical layout above GCR 0.6; (4.4) climate change and the CO2
> caveat (CROPGRO legumes respond strongly to CO2; mid-century gains include CO2 fertilisation); (4.5)
> policy: PM-KUSUM component A, DIN/Japan/France thresholds, what India could adopt; (4.6) limitations:
> light-only shading (no microclimate), fixed tilt, soil sampled at cell centre and texture sensitivity
> for rainfed millet, Yecora Rojo cultivar, groundnut over-estimate, harvested-area overlap assumption,
> hill states, technical not economic potential. Use [X] placeholders for result numbers. Verify every
> new reference on Crossref and add it to REF in lib.js. Rebuild the docx (node build_methods.js) and push.

## B. Supplementary validation figures (start now)
> Read CLAUDE.md and STATE.md. Make three journal-style PDF figures in results/figures/ and add them to the
> Supplementary (paper/methods/build_supp.js) as Figs. S1-S3 with captions: (S1) state yields simulated vs
> observed, before and after N calibration, wheat and pearl millet panels, 1:1 line, r and MAPE in each
> panel (results/validation_before_after.csv, states with obs_area >= 50); (S2) light model vs pvlib:
> mean sky view factor and hourly sunlit fraction vs GCR for both layouts (results/benchmark_pvlib.csv);
> (S3) light model vs CAZRI measured PPFD (results/validation_cazri_light.csv, case "broadband diffuse"):
> whole-system and below-array relative PPFD, modelled vs measured, by block and time; report bias and
> RMSE (whole system -0.044 / 0.053; below array +0.147 / 0.199) and state honestly in the caption that
> below-array light is over-estimated for low winter sun. Rebuild the Supplementary docx and push.

## C. Graphical abstract and highlights (start now)
> Read CLAUDE.md and STATE.md. paper/methods/graphical_abstract.py is a draft. Redesign it to Elsevier
> specs (landscape, at least 1328 x 531 px, aspect about 5:2, readable at 13 x 5 cm, no long text). Panels:
> problem (solar vs farmland), method (light + crop model, yield threshold), result (India map of
> GCR_max at RY >= 0.8 with headline GW). Leave the map and numbers as clearly marked placeholders that a
> script fills from results/potential/ when available. Write paper/methods/highlights.txt: 3-5 highlights,
> each at most 85 characters including spaces, with [X] placeholders for numbers. Push.

## D. Results pipeline (Monday, when stage 1 is done)
> MO uploads s1.zip (ry_crop_historical_current.csv.gz and energy_historical.csv from the GCP bucket).
> Put the files in runs/s1/summary/. Run prod/postprocess_india.py for historical_current (with energy),
> src/fig_india.py and src/results_summary.py (see headers). If ry_crop_historical_recommended exists, also
> run postprocess with --robust-with historical_recommended. Check numbers for sanity (open-field yields
> vs calibration, share of area at the GCR limit, capacity density). Draft Section 3 Results
> (paper/methods/results.js) from results/potential/headline_numbers.md with the figures. Push.

## E. Independent review (3-4 November, after D)
> Act as a critical Applied Energy reviewer who has not seen how the work was made. Read the built
> manuscript and supplementary (rebuild them first) and write review/review_round1.md: summary, major
> and minor comments, every claim that lacks support or a citation, every number that does not match
> the tables, reference problems (check DOIs on Crossref), and a recommendation. Do not edit the
> manuscript. Push.

## F. Rehearse task D (tonight)
> Read CLAUDE.md. Rehearse task D: build a fake runs/s1/summary from runs/india_test/it/summary (ry_crop
> for historical_current and historical_recommended, plus a synthetic energy_historical.csv with plausible
> kWh/kWp by layout and GCR: south ~1900-1750, ew ~1850-1680, vertical ~1480-1080 from GCR 0.05 to 0.7).
> Run prod/postprocess_india.py (plain and --robust-with historical_recommended), src/fig_india.py,
> src/results_summary.py and paper/methods/graphical_abstract.py. Fix every error, check every figure
> visually against the figure rules, write a one-command script run_results.sh (input: path to s1.zip)
> for Monday, then delete the fake data so nothing fake stays in the repo. Push.

## G. Reconcile national estimates (waterfall figure)
> Read CLAUDE.md and STATE.md. Write src/reconcile.py: on our grid and four crops compute capacity
> (1) with a fixed 0.42 and 0.75 MW/ha on all crop area (TERI / Fraunhofer style, no yield check),
> (2) plus the slope <= 5% rule, (3) plus double-cropped land counted once, (4) with our yield-constrained
> GCR_max (calibrated N), (5) with the robust management case. Produce a journal-style waterfall figure
> results/figures/fig_reconcile.pdf (one message: which assumption explains the gap). Test on the 40-cell
> data so it runs unchanged on stage 1 data. Push.

## H. Novelty audit
> Read CLAUDE.md. Search the literature (2024-2026) for national or regional agrivoltaic potential studies
> that use process-based crop models, a yield threshold or future climate, with special attention to
> India. Check whether the Nagaraju et al. SSRN preprint (India APV national assessment) is now published
> in a journal. Write review/novelty_audit.md: each study, what it does, how it compares with Table 1 in
> paper/methods/intro.js, and whether any "first" claim must be softened. Verify every DOI. Push.

## I. Submission package
> Read CLAUDE.md and the manuscript. Draft paper/submission/: cover letter to the Applied Energy editor
> (novelty in three sentences, no overclaiming), CRediT statement with two authors only: Mohamed
> Al-Mandhari (Conceptualization, Methodology, Software, Formal analysis, Investigation, Data curation,
> Visualization, Writing - original draft) and Aritra Ghosh, University of Exeter (Conceptualization,
> Supervision, Writing - review & editing) [MO to confirm roles with Aritra], data and code availability
> statement, declaration of competing interests, and a repo README suitable for a Zenodo release. Push.
