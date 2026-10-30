# AgriPV India: yield-constrained potential (Week 2 pilot)

Pilot cell: R0214 (26.375 N, 73.125 E), ICAR-CAZRI Jodhpur, Rajasthan.

## Layout
- `src/grid.py` - 0.25 deg Rajasthan grid aligned with NEX-GDDP-CMIP6 (498 cells)
- `src/pv_shading.py` - 2D infinite-row view-factor model: daily ground-light factor per strip
- `src/dssat_inputs.py` - SoilGrids to DSSAT soil (Saxton and Rawls 2006); weather stations
- `src/dssat_pilot.py` - DSSAT 4.8 runs (CERES-Wheat, CROPGRO-Chickpea, CERES-Millet, CROPGRO-Peanut)
- `run_pilot.py` - open field + 3 configs x 5 GCR x 5 strips x 4 crops (300 runs)
- `plot_pilot.py` - relative yield vs GCR figure (PDF + 400 dpi PNG)
- `data/` - NASA POWER daily weather 1995-2014, SoilGrids profile, grid
- `results/` - strip yields, field RY per season, summary, light factors, figure

## Run
    pip install pvlib DSSATTools geopandas
    python src/grid.py && python run_pilot.py && python plot_pilot.py

## Metric
RY = sum(field yield) / sum(open-field yield) over seasons (ratio of means).
Field yield = mean of 5 strip yields x cultivated fraction. Spread (SD, P10)
uses seasons where open yield >= 20% of its mean (crop-failure seasons excluded
from the spread only).

## Week 3, part 1 additions
- `validate_cazri_light.py` - light model vs measured PPFD at CAZRI (Santra et al. 2021)
- `plot_validation.py` - modelled vs measured relative PPFD figure
- `run_pilot.py --soil {soilgrids,loamy_sand} --evapo {R,F}` - scenario runs into results/<soil>_<evapo>/
- `plot_pilot.py <scenario>` - figure per scenario
- Weather file now includes dew point, wind and RH (NASA POWER) for FAO-56 Penman-Monteith

## Week 3, parts 2-3
- `data/yields/` - ICRISAT DLD (Mendeley unapportioned; Kaggle apportioned incl. wheat), Rajasthan extracts
- `calibrate_dld.py` - N x irrigation grid search vs Jodhpur district yields 1995-2014
- `ry_farmer_practice.py` - relative yield under shade at calibrated farmer practice
- `results/calibration_dld_jodhpur.csv`, `results/ry_farmer_practice.csv`, `results/pearl_millet_ry_by_N.csv`
