# AgriPV India: run state (2026-10-29 13:00 CET)

## Cloud (GCP project project-293bae4b-5e94-4c63-bac, bucket gs://project-293bae4b-5e94-4c63-bac-agripv)
- Rajasthan VM `agripv-raj`: TERMINATED, finished. Summaries in runs/rajasthan_final (historical farmer,
  ssp245 farmer, historical recommended). Can be deleted later (disk ~EUR 6/month).
- India VM `agripv-india` (e2-custom-12, europe-west1-b, 120 GB): data under /data on the VM, outputs to
  gs://.../india/out, status gs://.../india/status.txt (every 20 min), health HALT file on bad results.
  - Inputs done: NEX 1800 files, soil 2977 cells (108 nearest-neighbour filled; fast_soil VRT == REST, diff 0.00),
    15 climate .npy files.
  - test mode done: historical_farmer_open (all cells, 5 GCMs), 40-cell APV test (historical_recommended).
  - calib mode RUNNING: N sweep n30/n60/n90/n120 done, n180 resumed after false-alarm HALT
    (`bash update_india.sh calib ack`). Writes CALIB_DONE then shuts down.
- Code updates go via prod/make_update_india.sh -> update_india.sh <calib|full> [ack] (pushes metadata code,
  startup-script, mode, halt_ack, starts VM). Startup re-extracts code on every boot.

## Next steps
1. User attaches calib.zip (ry_system_historical_n*_open.csv.gz). Also use historical_farmer_open as N10 for millet
   (farmer millet = 10 kg N) and n60 wheat.
2. Per state x crop (wheat, pearl millet): pick N level whose 2-GCM mean open-field yield (area-weighted by
   SPAM, irr/rf share weighted) best matches ICRISAT 1995-2014 state mean (data/yields/kaggle_raw).
   Write prod/calib_n.csv (state,crop,n; plus ALL fallback). Check ranking vs ICRISAT N use
   (data/yields/state_n_use_1995_2014.csv: Punjab 157 ... Rajasthan 30 kg N/ha GCA).
3. Redo validation (before/after) -> results/validation_india_states_*.csv; figure.
4. Groundnut (sim/obs 2.66) and chickpea: state yield-gap factors for absolute production only (RY unaffected).
5. Rebuild update_india.sh (bash prod/make_update_india.sh, includes calib_n.csv) -> user runs
   `bash update_india.sh full`. Full stages: historical:current, ssp585:current, ssp245:current,
   historical:recommended (~36 h each, ~6 days, ~EUR 50).
6. Post-processing: slope rule = count only pixels with slope <= 5% (data/slope_india.csv frac_slope_le5),
   one rule, sensitivity 3/5/10%; hill cells disclosed in validation. Thresholds RY 0.66/0.8/0.9
   (DIN SPEC 91434 / Japan / France). PV energy + capacity via pvlib (bifacial glass-glass reference module).

## Key findings so far
- Light model reproduces pvlib view factors (results/benchmark_pvlib.csv): SVF mean within 0.0005, sunlit MAE 0.0015.
- Wheat RY>1 under farmer N60 is N-dilution artefact (N stress off -> RY 0.68 at 70% light); recommended N fixes.
- Rajasthan: SSP2-4.5 barely changes RY (+-0.03); legume yields +37% from CO2 (CROPGRO strong CO2 response; flag).
- India uncalibrated validation (farmer N): sim/obs wheat 0.92 r=0.01, chickpea 1.04, millet 1.08, groundnut 2.66.
- Docs artifact f705b55b-c8ae-4b03-9fce-8b45f9981520: tab "Introduction outline" (target Applied Energy; Table 1 vs
  Mehta & Betz 2026, Xia 2024, Curioni 2025, TERI 2026).

## 2026-10-29 14:00 calibration done
- prod/calib_n.csv written (src/calibrate_n.py). Wheat: r 0.01 -> 0.74, MAPE 0.29 -> 0.12, sim/obs 1.01.
  Millet: r 0.04 -> 0.28, MAPE 0.31 -> 0.24 (south India millet over-predicted even at N10).
  Spearman calibrated N vs state fertiliser use: wheat 0.33, millet 0.26 (all-crop averages, weak check).
- Legume yield-gap factors (results/yieldgap_legumes.csv): chickpea 1.09, groundnut 0.44 (area-weighted).
- Next: user runs `bash update_india.sh full` (update_india.sh rebuilt with calib_n.csv).

## 2026-10-29 15:10 full run, false-alarm HALT
- historical_current halted at 417 tasks: wheat median 739 < 800. Cause: tasks run south->north, first cells are
  Karnataka/Maharashtra wheat (calib N 90/30, obs ~1 t/ha); calib sweep predicts ~1.0 t/ha there, ~2.2 t/ha India-wide.
- status_india.py: strict yield range only after a full model pass (>=2977 files); coarse 200-9000 before.
- User resumes with `bash update_india.sh full ack`.

## 2026-10-29 20:30 post-processing built (tested on 40-cell test run)
- prod/energy_india.py (VM): pvlib infinite_sheds bifacial (eta 0.22, bifi 0.80, gamma -0.30%/K, Faiman,
  14% loss, inverter 0.96, albedo 0.2), same hourly sky model as crop runs, every 5th year x 5 GCMs.
  Jodhpur check: south 25deg ~1990 kWh/kWp at GCR 0.05, vertical ~1475. ~27 s/cell -> ~2 h/period on 12 vCPU.
  pipeline_india.sh runs it once per period after each stage. update_india.sh rebuilt (includes it); push with
  `bash update_india.sh full` before stage 1 ends (Sunday).
- prod/postprocess_india.py (local): interpolated GCR_max (first crossing, RY=1 at GCR 0) per GCM; slope rules
  none/le5/le10; capacity = ha x GCR x 0.22 x 10 MWp; rabi/kharif overlap counted once; totals median + GCM range.
- src/fig_india.py: gcrmax map 4x3, capacity bars (TWp, GCM range, slope markers), top states, delta maps.
- Open points: slope le3 not in slope_india.csv (rerun fetch_slope with extra threshold if wanted);
  tilt fixed 25 deg everywhere (sim geometry); vertical/millet GCR_max hits 0.7 grid limit;
  technical potential is tens of TWp -> needs demand/grid framing in paper.

## 2026-10-29 21:00 Methods written (paper/methods/)
- build_methods.js (main, ~1850 words incl. tables, 4 eqs, Tables 1-2, Figs 1-2) + build_supp.js (SM S1-S7,
  Tables S1-S8, Eqs S1-S3); shared lib.js. Fig 1 graphical flowchart fig1.py; Fig 2 layouts fig2.py.
- Verified: cultivars (Yecora Rojo / JG 74 / ICMH 451 / TMV 2), MAFF 31 Mar 2013 (~20% drop vs local average),
  DIN SPEC 66% + 15% land loss (cat 2), decret 2024-318 90%, Copernicus DOI 10.5270/ESA-c5d3d65, ICRISAT DLD
  doi 10.21421/D2/XFB1BZ, ECS range via Meehl 2020 Sci Adv.
- Flag: vertical layout 0.5 m strip > DIN 15% land-loss limit above GCR 0.6.
- 2026-10-29 21:30: Introduction written (paper/methods/intro.js, ~1150 words + Table 1 of prior studies); manuscript
  now built as Manuscript_AgriPV_India.docx (title, 1 Intro, 2 Methods). All intro refs checked via Crossref/publisher.
  To confirm: MNRE solar figure (>160 GW mid-2026, taken from trade press), PLFS report title, PM-KUSUM guideline title.

## 2026-10-30 Discussion drafted (Task A)
- paper/methods/discussion.js: Section 4 (4.1-4.6, ~1500 words), called from build_methods.js after a Section 3
  Results placeholder. Result numbers are [X]; fill from results/potential/headline_numbers.md (Task D).
- Pilot evidence used: Rajasthan wheat south GCR 0.3 RY 1.13 (farmer N60) vs 0.90 (recommended), GCR 0.5 0.86 vs 0.51;
  Jodhpur millet texture test (SoilGrids vs loamy sand): open yield 886 vs 583 kg/ha, RY south GCR 0.3 1.02 vs 0.87.
- New refs (Crossref-checked): Justes 1994, Ainsworth & Long 2005, Long 2006, Marrou 2013, Weselek 2021, Folberth 2016,
  Lopez 2012 (NREL), MNRE PM-KUSUM FAQ (URL). Riaz 2021 DOI added.
- [verify] items in text: Mehta & Betz overlap share; CO2 x shade interaction in RY (check model output).
- postprocess_india.py does not drop vertical GCR > 0.6 (DIN 15% land loss); Discussion reports the share as [X].

## 2026-10-30 graphical abstract and highlights (task C)
- paper/methods/graphical_abstract.py redesigned: 13 x 5.2 cm, 3 panels (problem / method / result), PNG 600 dpi
  (3070 x 1228 px) + PDF. Result map and headline fill from results/potential/{map_gcr,india_combined}_<stage>
  when present (default historical_current, ew_fixed, tau 0.8, slope le5); otherwise marked placeholders.
  Fill path tested on the 40-cell test run. Rerun after task D: `cd paper/methods && python graphical_abstract.py`.
- paper/methods/highlights.txt: 5 highlights, each <= 85 characters, [X] placeholders.

## 2026-10-30 Supplementary validation figures (task B)
- src/fig_supp_validation.py -> results/figures/figS1_yield_calibration, figS2_light_vs_pvlib, figS3_light_vs_cazri (PDF + PNG).
  S1 numbers (obs_area >= 50 kha, area-weighted MAPE): wheat r 0.01 -> 0.74, MAPE 29 -> 12%; millet r 0.04 -> 0.28, MAPE 31 -> 24%.
  S3: whole system bias -0.044 / RMSE 0.053; below array +0.147 / 0.199.
- build_supp.js: new Section S8 with Figs. S1-S3; Santra et al. 2021 added to REF (DOI 10.1016/j.biosystemseng.2021.06.017
  confirmed via X-MOL and AGRIS; Crossref blocked from the session, volume/pages marked [verify]).
