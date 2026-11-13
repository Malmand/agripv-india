# AgriPV India: guidance for Claude sessions

Paper: *Yield-constrained agrivoltaic potential of India under current and mid-century climate*
(target Applied Energy). Author: MO (Mohamed Al-Mandhari). Read `STATE.md` first: it holds the run
state, decisions and findings. `TASKS.md` lists the open tasks, one per cloud session.

## Layout
- `prod/` simulation code run on the GCP machine (DSSAT via DSSATTools 3.0.2, pv_shading light model,
  energy_india.py, postprocess_india.py). Do not change files used by the running GCP pipeline
  (sim_india.py, run_cells_india.py, pipeline_india.sh, status_india.py) without telling MO.
- `src/` analysis and figure scripts (fig_india.py, results_summary.py, calibrate_n.py, benchmark_pvlib.py).
- `results/` validation tables (calibration, pvlib benchmark, CAZRI light) and figures.
- `runs/` small summaries: `india_test/it/summary` (40-cell test run), `calib/`, Rajasthan pilot.
- `data/` grid, slope, India state boundaries (`boundaries/Admin2.shp`), MapSPAM, yields.
- `paper/ef/` manuscript sources (Node `docx`), one set for both journals: `lib.js` (helpers, REF, citations;
  AGRIPV_STYLE=ae switches to numbered Elsevier references), `abstract.js`, `intro.js`, `build_methods.js`,
  `results.js`, `discussion.js`, `conclusions.js`, `sens_table.js`, `build_supp.js`, `cover_ef.js`, `highlights.js`,
  `fig1.py`, `fig2.py`. `node build_methods.js` etc. builds the Earth's Future version in paper/ef.
- `paper/methods/build_ae.sh` builds the Applied Energy version (manuscript, supplementary material, cover letter,
  highlights, graphical abstract `graphical_abstract_v3.py`) into paper/methods from the same sources.

## Rules from MO (always)
- Writing: no em dashes; mixed sentence lengths; plain, precise wording; define each equation symbol
  once, right after the equation; non-essential equations go to the Supplementary.
- Citations: peer-reviewed papers, standards, laws or official reports only. No theses, preprints
  or conference abstracts. Every reference needs a DOI or URL, checked online (Crossref) before use.
  Never invent a reference or a number; mark anything unverified as [verify].
- Figures: journal style. Black 0.5-1 pt L-frame axes, outward ticks, no gridlines, panel labels A, B, C
  (10-12 pt bold), axis titles 8-10 pt with units in brackets, tick/legend 6-8 pt, colour-blind safe
  (Okabe-Ito or viridis, no red-green), strictly 2D, one clear message per figure, export PDF (rasters
  300-600 dpi). Error bars or ranges on averages.
- Git: before the first commit run `git config user.name "Mohamed Al-Mandhari"` and
  `git config user.email "almandharimohammed90@gmail.com"`, so commits are authored by MO, not Claude.
  Commit and push to `main` of this repo (pull --rebase first). Commit messages must NOT contain Claude co-author or
  session trailers; Claude must not appear as a contributor.
- Results numbers in the text come from `results/potential/headline_numbers.md` once it exists;
  until then use placeholders like [X GW].
