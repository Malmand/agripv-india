#!/bin/bash
# Builds the Zenodo deposit required by AGU (Open Research): the data behind every figure and table, and the code
# that produced the model output, the tables and the figures. Run after the final results are in (run_results.sh).
#   bash make_zenodo.sh            -> zenodo/AgriPV_India_data_and_code.zip  (+ zenodo/README.md shown on Zenodo)
# Left out on purpose: cloud orchestration (pipeline/launch/update shell scripts, status monitor), literature tools,
# third-party raw data (climate, soils, MapSPAM rasters, boundaries, the Jha et al. observations): cite those at source.
set -euo pipefail
cd "$(dirname "$0")"
OUT=zenodo; STG=$OUT/AgriPV_India; rm -rf $OUT; mkdir -p $STG/{data/results,data/inputs,data/simulation_summaries,code/simulation,code/analysis}

# ---- data: derived results behind the figures and tables
cp results/potential/*.csv results/potential/*.csv.gz results/potential/numbers.json $STG/data/results/
mkdir -p $STG/data/results/field_response $STG/data/results/economics $STG/data/results/validation
cp results/potential_field/* $STG/data/results/field_response/ 2>/dev/null || true
cp -r results/economics/* $STG/data/results/economics/
for f in benchmark_pvlib calib_state_yields calibration_dld_jodhpur pearl_millet_ry_by_N ry_farmer_practice \
         shade_field_correction shade_field_correction_c3 shade_field_correction_millet_c3 shade_field_correction_nosoy \
         shade_field_curves shade_light_reduction shade_response_check shade_validation_jha_bins validation_before_after \
         validation_cazri_light validation_india_states_farmer_open yieldgap_legumes; do
  cp results/$f.csv $STG/data/results/validation/
done
# simulation summaries: relative yield against GCR per cell, crop, layout, GCM and case; PV specific yield
cp runs/s1/summary/ry_crop_*.csv.gz runs/s1/summary/energy_*.csv runs/s1/summary/rad_factors.csv $STG/data/simulation_summaries/
mkdir -p $STG/data/simulation_summaries/rajasthan_pilot && cp runs/rajasthan_final/*.csv $STG/data/simulation_summaries/rajasthan_pilot/ 2>/dev/null || true
# inputs we derived (grid with MapSPAM 2010 crop areas and state, slope shares, calibrated nitrogen)
cp data/grid_india_025.csv data/slope_india.csv prod/calib_n.csv $STG/data/inputs/

# ---- code: simulation (DSSAT via DSSATTools, light model, PV energy) and analysis (tables, figures, numbers)
for f in sim_india.py run_cells_india.py dssat_inputs.py pv_shading.py energy_india.py postprocess_india.py summarise_india.py \
         fetch_india_inputs.py fetch_slope.py fetch_soil.py fast_soil.py get_nex_gddp.py nex_to_cells.py radiation_ref.py \
         season_check.py sim.py run_cells.py summarise.py dssat_pilot.py; do
  cp prod/$f $STG/code/simulation/
done
for f in build_india_grid.py grid.py calibrate_n.py benchmark_pvlib.py field_response.py shade_response_check.py \
         validate_shade_jha.py economics.py food_tradeoff.py reconcile.py results_summary.py make_numbers.py \
         fig_india.py fig_food.py fig_economics.py fig_supply.py fig_tornado.py fig_supp_validation.py; do
  cp src/$f $STG/code/analysis/
done
cp run_results.sh $STG/code/analysis/
cp zenodo_README.md $STG/README.md
cp zenodo_README.md $OUT/README.md
(cd $OUT && zip -qr AgriPV_India_data_and_code.zip AgriPV_India)
du -sh $OUT/AgriPV_India_data_and_code.zip; find $STG -type f | wc -l
