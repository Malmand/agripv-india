# Data and code for: Yield-constrained agrivoltaic potential of India under current and mid-century climate

Mohamed Al-Mandhari (ORCID 0009-0000-8533-8702) and Aritra Ghosh (ORCID 0000-0001-9409-7592; corresponding author,
a.ghosh@exeter.ac.uk), Renewable Energy, Electric and Electronic Engineering, Faculty of Environment, Science and
Economy, University of Exeter, Penryn TR10 9FE, UK.

Related article: Al-Mandhari, M., & Ghosh, A. Yield-constrained agrivoltaic potential of India under current and
mid-century climate. Submitted to *Earth's Future* (AGU).

This deposit holds the data behind every figure and table of the article and its Supporting Information, and the
code that produced the model output, the tables and the figures.

## Licences
- Data (`data/`): Creative Commons Attribution 4.0 International (CC BY 4.0).
- Code (`code/`): MIT licence.

## Contents

### data/results
National, state and cell results for India (0.25° grid, 2977 cells), three array layouts (`south_fixed`, `ew_fixed`,
`vertical`), relative-yield thresholds τ = 0.66, 0.80, 0.90 (`thr`), slope rules (`slope_rule`: `le5`, `le10`, `none`)
and five climate models (`model`). Stage names: `historical_current` = 1995–2014 with calibrated nitrogen;
`historical_current_robust` = robust case (smaller GCR_max of calibrated and recommended nitrogen in each cell);
`ssp245_current`, `ssp585_current` = 2041–2060 with calibrated nitrogen; `ssp585_current_robust` = 2041–2060 robust
case (SSP5-8.5); `_season` = threshold met in at least 16 of 20 seasons; `_nodin` = vertical rows without the 0.6 cap;
`historical_current_robust_rice` = robust case with the rice that follows wheat or chickpea also held to the threshold
(present when the rice runs are included).

| File pattern | Content | Key columns and units |
|---|---|---|
| `cell_crop_<stage>.csv.gz` | per cell, crop, layout, threshold, model | `gcr_max` (–), `elig_ha` (ha), `cap_mwp` (MWp), `energy_gwh` (GWh yr⁻¹), `yield_kwh_kwp` (kWh kWp⁻¹ yr⁻¹), `at_cap` (GCR_max at the largest simulated GCR) |
| `cell_combined_<stage>.csv.gz` | per cell with crops combined (double-cropped land counted once) | `cap_mwp`, `energy_gwh`, `land_ha` |
| `india_combined_<stage>.csv`, `india_by_crop_<stage>.csv`, `state_combined_<stage>.csv` | national and state totals | `*_median`, `*_min`, `*_max` over the five models |
| `map_gcr_<stage>.csv.gz` | five-model median GCR_max per cell, crop and layout (maps) | `gcr_med` |
| `food_by_crop.csv`, `food_cell.csv.gz`, `food_curve.csv` | crop given up under the arrays (Fig. 6) | t, Mt, PJ, kg MWh⁻¹; `mgmt`: `cur` calibrated N, `rec` recommended N |
| `kharif_overlap_spam.csv`, `.json` | share of eligible rabi land followed by kharif crops other than pearl millet and groundnut (MapSPAM 2010) | %, ha |
| `reconcile.csv` | fixed-density to yield-constrained steps (reconciliation figure) | GWp, Mha |
| `numbers.json` | every number quoted in the article text | `values` (as printed), `raw` |
| `field_response/` | field-response scenario (shade response rescaled to observations) | as above |
| `economics/` | screening economics, cost-supply curves | Rs kWh⁻¹, Rs ha⁻¹ |
| `validation/` | calibration, light-model and shade-response checks (Tables 3, S2, S6–S7; Figs. S1–S3, S11–S12) | see column names |

### data/simulation_summaries
- `ry_crop_<period>_<management>.csv.gz`: simulated open-field and shaded yields and relative yield for each cell,
  model, crop system (`water`: irrigated, rainfed, `all` = combined by production), layout and GCR. Columns `open`,
  `apv` (kg ha⁻¹), `ry` (–). These curves give GCR_max for any threshold.
- `energy_<period>[_rc].csv`: PV specific yield per cell, layout and GCR (`_rc` = radiation corrected to NASA POWER).
- `rad_factors.csv`: monthly radiation correction factors per cell.
- `ry_crop_historical_<management>_rice.csv.gz`: as above for transplanted rice after wheat or chickpea (CERES-Rice);
  `calib_rice_state_yields.csv` and `calib_n_with_rice.csv`: rice nitrogen calibration against ICRISAT state yields.
- `rajasthan_pilot/`: Rajasthan pilot results (Text S9).

### data/inputs
- `grid_india_025.csv`: the 0.25° grid with state, crop harvested area and irrigated share (from MapSPAM 2010),
  and sowing dates (GGCMI Phase 3).
- `slope_india.csv`: share of each cell with terrain slope ≤ 5% and ≤ 10% (Copernicus GLO-90).
- `calib_n.csv`: calibrated nitrogen level by state and crop (Table S6).
- `grid_india_025_kharif.csv`: the grid with MapSPAM 2010 areas of rice, maize, soybean, cotton, sorghum, pigeonpea and
  sugarcane, rice irrigated share and rice transplanting day (GGCMI Phase 3, main rice season).

### code/simulation
Crop and light simulation run on a cloud machine: `sim_india.py`, `run_cells_india.py` (DSSAT runs per cell),
`dssat_inputs.py`, `pv_shading.py` (strip-resolved light model), `energy_india.py` (PV energy with pvlib),
`postprocess_india.py` (GCR_max, eligible land, capacity), `summarise_india.py`, input preparation
(`fetch_*.py`, `get_nex_gddp.py`, `nex_to_cells.py`, `fast_soil.py`, `radiation_ref.py`), the season test
(`season_check.py`) and the Rajasthan pilot (`sim.py`, `run_cells.py`, `summarise.py`, `dssat_pilot.py`).

### code/analysis
`run_results.sh` runs the whole analysis from the simulation summaries: tables, figures and `numbers.json`.
Scripts: `make_numbers.py`, `food_tradeoff.py`, `reconcile.py`, `economics.py`, `field_response.py`,
`calibrate_n.py`, validation (`benchmark_pvlib.py`, `shade_response_check.py`, `validate_shade_jha.py`) and figures
(`fig_*.py`).

## Software
Python 3.13 with DSSAT 4.8 through DSSATTools 3.0.2, pvlib 0.16.1, pandas 3.0.5 and numpy 2.5.3; geopandas and
matplotlib for maps and figures.

## Third-party data (not redistributed; cite and download at source)
NEX-GDDP-CMIP6 climate (Thrasher et al., 2022); MapSPAM 2010 (Yu et al., 2020); SoilGrids 2.0 (Poggio et al., 2021);
Copernicus DEM GLO-90 (European Space Agency, 2022); GGCMI Phase 3 crop calendar (Jägermeyr et al., 2021); ICRISAT
District Level Database (Swamikannu et al., 2021); NASA POWER; Indian Food Composition Tables 2017 (Longvah et al.,
2017); India state boundaries, DataMeet India Community (2021), CC BY 4.0; shade-response observations compiled by
Jha et al. (2026). Full references are in the article.
