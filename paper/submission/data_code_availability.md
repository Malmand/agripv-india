# Data and code availability (draft)

## Statement for the manuscript

The code used in this study (light model, crop-model set-up, energy model, post-processing and figures) and the processed results (relative yield by cell, crop, layout and ground coverage ratio; GCR~max~ maps; state and national potential tables) are openly available on Zenodo at https://doi.org/[Zenodo DOI] and on GitHub at https://github.com/Malmand/agripv-india. All input data are public: NEX-GDDP-CMIP6 daily climate [Thrasher et al. 2022], SoilGrids 2.0 [Poggio et al. 2021], MapSPAM 2010 harvested area (https://doi.org/10.7910/DVN/PRFF8V) [Yu et al. 2020], the GGCMI Phase 3 crop calendar [Jägermeyr et al. 2021], ICRISAT District Level Data (https://doi.org/10.21421/D2/XFB1BZ) and the Copernicus GLO-90 elevation model (https://doi.org/10.5270/ESA-c5d3d65). Raw daily climate files and per-run crop-model outputs are not redistributed because of their size; they can be regenerated with the released code and are available from the corresponding author on reasonable request.

## Inputs and where the code gets them

| Input | Source | Fetched by | In the repository |
|---|---|---|---|
| Daily climate, 5 GCMs (GFDL-ESM4, IPSL-CM6A-LR, MPI-ESM1-2-HR, MRI-ESM2-0, UKESM1-0-LL), historical 1995-2014, SSP2-4.5 and SSP5-8.5 2041-2060 | NEX-GDDP-CMIP6, NASA NCCS THREDDS (https://ds.nccs.nasa.gov/thredds) | prod/get_nex_gddp.py, prod/nex_to_cells.py | No (too large) |
| Soil profiles | SoilGrids 2.0, ISRIC (https://files.isric.org/soilgrids/latest/) | prod/fetch_soil.py, prod/fast_soil.py | Pilot profile only (data/soil) |
| Harvested area and irrigated share | MapSPAM 2010 v2.0, Harvard Dataverse | prod/fetch_india_inputs.py | data/india_inputs/spam_india_harv_ha.csv |
| Sowing dates | GGCMI Phase 3 crop calendar (copy on the CESM input-data server) | prod/fetch_india_inputs.py | data/india_inputs/*.nc |
| Observed district and state yields 1995-2014 | ICRISAT District Level Data | manual download | data/yields/ (see licence note) |
| State nitrogen use | [MO: source of data/yields/state_n_use_1995_2014.csv, verify] | manual | data/yields/state_n_use_1995_2014.csv |
| Terrain slope | Copernicus DEM GLO-90 (AWS open data) | prod/fetch_slope.py | data/slope_india.csv |
| State boundaries | DataMeet India community, States/Admin2, https://github.com/datameet/maps (CC BY 4.0) | manual | data/boundaries/ |
| Pilot weather, Jodhpur | NASA POWER | src/dssat_inputs.py | data/weather/ |
| Measured PPFD, CAZRI Jodhpur | Santra et al. 2021, Table 4 (published values) | validate_cazri_light.py | results/validation_cazri_light.csv |

## Software

DSSAT 4.8 [Hoogenboom et al. 2021] through DSSATTools 3.0.2; pvlib 0.16.1 [Anderson et al. 2023]; Python 3.13 with
pandas 3.0.5, numpy 2.5.3, scipy, xarray, netCDF4, rasterio, pyproj, geopandas and matplotlib (versions as in
prod/startup_india.sh); manuscript builders use Node.js with the `docx` package.

---
Notes for MO (delete before submission):
- Before the Zenodo release: (1) choose licences, e.g. MIT for code and CC BY 4.0 for processed results [MO to decide],
  and add LICENSE; (2) check whether the redistributed third-party files may be shared: the ICRISAT DLD CSV in
  data/yields/kaggle_raw came from a Kaggle copy (licence unknown; safer to drop it and point to the ICRISAT DOI),
  MapSPAM and SoilGrids are CC BY 4.0 [verify], the DataMeet boundaries are CC BY 4.0; (3) make the GitHub
  repository public or link it to Zenodo via the GitHub integration, then paste the DOI here, in the cover letter
  and in README.md.
- Add the processed stage outputs (results/potential/, runs/*/summary) to the release once task D is done.
- Applied Energy encourages data statements and Research Elements articles [verify current policy].
