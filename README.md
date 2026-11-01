# AgriPV India: yield-constrained agrivoltaic potential

Code and processed results for the paper

> Al-Mandhari M, Ghosh A. *Yield-constrained agrivoltaic potential of India under current and mid-century climate.*
> Submitted to Applied Energy [year; DOI when published].

Archived release: https://doi.org/[Zenodo DOI] (version [vX.Y]).

## What the code does

The study maps how much Indian cropland can host agrivoltaics (APV) while crop yield stays at or above 66%, 80% or
90% of the open-field yield, and at what ground coverage ratio (GCR).

1. **Light model** (`prod/pv_shading.py`). Two-dimensional infinite-row view-factor model. Gives the daily light
   factor of five ground strips below three layouts: elevated south-facing (tilt 25°), elevated east-west (tilt 10°)
   and vertical bifacial rows. Checked against pvlib (`src/benchmark_pvlib.py`) and against PPFD measured at
   ICAR-CAZRI Jodhpur (`validate_cazri_light.py`).
2. **Crop model** (`prod/sim_india.py`, `prod/run_cells_india.py`). DSSAT 4.8 through DSSATTools 3.0.2:
   CERES-Wheat, CROPGRO-Chickpea, CERES-Millet and CROPGRO-Peanut, irrigated and rainfed, on 2977 cells of a
   0.25° grid. Nitrogen calibrated by state against ICRISAT yields (`src/calibrate_n.py`, `prod/calib_n.csv`).
3. **Climate**. NEX-GDDP-CMIP6, five GCMs (GFDL-ESM4, IPSL-CM6A-LR, MPI-ESM1-2-HR, MRI-ESM2-0, UKESM1-0-LL),
   1995-2014 and 2041-2060 under SSP2-4.5 and SSP5-8.5.
4. **Energy** (`prod/energy_india.py`). pvlib infinite-sheds bifacial model, Faiman temperature model, PVWatts.
5. **Potential** (`prod/postprocess_india.py`). GCR_max per cell, crop, layout and threshold; eligible land
   (slope ≤ 5%); rabi and kharif area counted once; capacity and energy as the five-GCM median and range.

## Repository layout

| Folder | Content |
|---|---|
| `prod/` | Simulation pipeline as run on a cloud VM (input fetching, crop runs, energy, post-processing) |
| `src/` | Analysis and figure scripts (calibration, pvlib benchmark, maps, summary tables) |
| `data/` | 0.25° grid, slope shares, MapSPAM extract, GGCMI crop calendars, observed yields, boundaries |
| `results/` | Validation tables and figures; `results/potential/` holds the potential tables and headline numbers |
| `runs/` | Compact run summaries (calibration sweep, 40-cell test, Rajasthan pilot, stage outputs) |
| `paper/methods/` | Manuscript and Supplementary builders (Node.js `docx`), Figs. 1-2, graphical abstract |
| `paper/submission/` | Cover letter, CRediT, data availability and declarations |
| root `*.py` | Week 1-3 single-cell pilot at Jodhpur (R0214) |

## Software

- Python 3.13: DSSATTools 3.0.2 (bundles DSSAT 4.8), pvlib 0.16.1, pandas 3.0.5, numpy 2.5.3, scipy, xarray,
  netCDF4, rasterio, pyproj, geopandas, matplotlib.
- Node.js with the `docx` package (manuscript builders only).

```bash
pip install DSSATTools==3.0.2 pvlib==0.16.1 pandas==3.0.5 numpy==2.5.3 scipy xarray netCDF4 rasterio pyproj geopandas matplotlib
```

## Reproducing the results

The full India run takes about 36 h per climate period on a 12-vCPU machine. Steps and options are in the header
of each script.

1. Inputs: `prod/fetch_india_inputs.py` (MapSPAM, crop calendars), `prod/get_nex_gddp.py` and
   `prod/nex_to_cells.py` (climate), `prod/fetch_soil.py` or `prod/fast_soil.py` (SoilGrids),
   `prod/fetch_slope.py` (Copernicus GLO-90 slope).
2. Crop and energy runs: `prod/pipeline_india.sh` (calls `run_cells_india.py`, `summarise_india.py`,
   `energy_india.py`).
3. Potential: `prod/postprocess_india.py --summary <dir> --stage historical_current --grid data/grid_india_025.csv
   --slope data/slope_india.csv --energy <energy csv> --outdir results/potential`.
4. Figures and tables: `src/fig_india.py`, `src/results_summary.py`, `src/fig_supp_validation.py`.
5. Numbers and manuscript: `python src/make_numbers.py`, then `node paper/methods/build_methods.js` and
   `node paper/methods/build_supp.js` (needs `npm install docx`).

## Updating after a new stage

```bash
bash run_results.sh sX.zip && node paper/methods/build_methods.js
```

`sX.zip` holds the stage summaries from the GCP bucket (`ry_crop_<stage>.csv.gz`, `energy_<period>.csv`).
`run_results.sh` post-processes every stage in the zip, makes the figures (PDF for the journal, PNG for the
docx), `results/potential/headline_numbers.md` and `results/potential/numbers.json`, and redraws the graphical
abstract. `build_methods.js` then rebuilds `Manuscript_AgriPV_India.docx` and `highlights.txt`.

No result number is typed into the manuscript. `src/make_numbers.py` writes every number used in the Results,
Discussion, highlights and graphical abstract to `numbers.json`, for each stage present (current climate,
robust nitrogen case, SSP2-4.5, SSP5-8.5). The builders write `{key}` placeholders (for example
`{main.cap_twp}`), and `fill()` in `paper/methods/lib.js` replaces them. Sentences in `{? ... ?}` need a stage
that may not exist yet (robust case, 2050) and are left out until it does; any other missing key prints as
`[pending]`, and the build lists those keys. The key scheme is in the header of `src/make_numbers.py`;
highlights are written from `paper/methods/highlights_template.txt` (85-character check included).

## Data sources

All inputs are public; please cite the original sources.

- NEX-GDDP-CMIP6: Thrasher et al. (2022), Sci Data 9:262, https://doi.org/10.1038/s41597-022-01393-4
- SoilGrids 2.0: Poggio et al. (2021), SOIL 7:217-240, https://doi.org/10.5194/soil-7-217-2021
- MapSPAM 2010 v2.0: Yu et al. (2020), Earth Syst Sci Data 12:3545-3572, https://doi.org/10.5194/essd-12-3545-2020;
  data https://doi.org/10.7910/DVN/PRFF8V
- GGCMI Phase 3 crop calendar: Jägermeyr et al. (2021), Nat Food 2:873-885, https://doi.org/10.1038/s43016-021-00400-y
- ICRISAT District Level Data: https://doi.org/10.21421/D2/XFB1BZ
- Copernicus DEM GLO-90: https://doi.org/10.5270/ESA-c5d3d65
- CAZRI light measurements: Santra et al. (2021), Biosyst Eng 209:74-93, https://doi.org/10.1016/j.biosystemseng.2021.06.017
- State boundaries (`data/boundaries/Admin2.shp`): [source and licence to add]

## Licence

[To be chosen before release, e.g. MIT for code and CC BY 4.0 for processed results. Third-party data in `data/`
keep their own licences.]

## Citation

If you use this code or the results, please cite the paper above and the Zenodo release
(https://doi.org/[Zenodo DOI]).

## Contact

Mohamed Al-Mandhari, [affiliation], almandharimohammed90@gmail.com
