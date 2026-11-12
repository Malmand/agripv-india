#!/usr/bin/env bash
# Results pipeline (task D) in one command, run from anywhere:
#   bash run_results.sh /path/to/s1.zip      (zip of stage summaries)
#   bash run_results.sh runs/s1               (folder; uses <folder>/summary if it exists)
# If the folder holds no ry_crop_<stage>.csv.gz, every stage that already has
# results/potential/cell_crop_<stage>.csv.gz is rebuilt from that table (postprocess --from-cell-crop):
# this re-applies the DIN cap and the summaries without the crop runs (no open-field yield check).
# s1.zip holds the stage summaries from gs://.../india/out/summary, at least
#   ry_crop_historical_current.csv.gz and energy_historical.csv
# and optionally ry_crop_historical_recommended.csv.gz (robust case) and later stages
# (ry_crop_ssp245_current.csv.gz + energy_ssp245.csv, ...). Folders inside the zip are ignored.
# Steps: unzip -> runs/s1/summary, postprocess every *_current stage (with energy if present),
# robust case (min of calibrated and recommended N), figures, headline numbers, numbers.json
# (src/make_numbers.py, read by paper/methods/lib.js fill()), graphical abstract.
# Outputs: results/potential/ (tables, headline_numbers.md, numbers.json for the manuscript text),
# results/figures/fig_india_*.{pdf,png},
# paper/methods/graphical_abstract.{pdf,png}. Nothing is committed.
set -euo pipefail
SRC=${1:?usage: bash run_results.sh /path/to/s1.zip | runs/s1}
SRC=$(realpath -m "$SRC")
PY=${PY:-python3}
cd "$(dirname "$(realpath "$0")")"
SUM=runs/s1/summary
if [ -d "$SRC" ]; then SUM=$SRC; [ -d "$SRC/summary" ] && SUM=$SRC/summary; ZIP=""
elif [ -f "$SRC" ]; then ZIP=$SRC
else SUM=$SRC; ZIP=""; echo "NOTE: $SRC does not exist"; fi
DIN=${DIN_CAP:-0.6}   # vertical GCR_max cap (DIN SPEC 91434); uncapped totals go to *_nodin
PP=results/potential
FIG=results/figures
GRID=data/grid_india_025.csv

$PY -c "import numpy, pandas, matplotlib, geopandas" 2>/dev/null || {
  echo "missing Python packages: pip install numpy pandas matplotlib geopandas"; exit 1; }

mkdir -p "$PP" "$FIG"
if [ -n "$ZIP" ]; then mkdir -p "$SUM"; unzip -o -j -q "$ZIP" '*.csv' '*.csv.gz' -d "$SUM"; fi
echo "== files in $SUM"; ls -l "$SUM" 2>/dev/null || true
REBUILD=0
if [ ! -f "$SUM/ry_crop_historical_current.csv.gz" ]; then
  [ -f "$PP/cell_crop_historical_current.csv.gz" ] || { echo "no ry_crop_historical_current.csv.gz and no $PP/cell_crop table"; exit 1; }
  echo "NOTE: no ry_crop files in $SUM: rebuilding from the committed cell_crop tables in $PP"
  REBUILD=1
fi

# stages: historical_current first, then any other *_current (future) stages
STAGES=(historical_current)
PRE=ry_crop_; DIR=$SUM; [ $REBUILD = 1 ] && { PRE=cell_crop_; DIR=$PP; }
for f in "$DIR"/${PRE}*_current.csv.gz; do
  [ -f "$f" ] || continue
  s=$(basename "$f" .csv.gz); s=${s#$PRE}
  [ "$s" = historical_current ] || STAGES+=("$s")
done
HAVE_REC=0; [ -f "$SUM/ry_crop_historical_recommended.csv.gz" ] && HAVE_REC=1
[ $REBUILD = 1 ] && [ -f "$PP/cell_crop_historical_current_robust.csv.gz" ] && HAVE_REC=2
TMPCC=$(mktemp -d)

pp() {  # stage [extra args]
  local st=$1; shift
  local en="$SUM/energy_${st%%_*}.csv"
  # radiation-corrected energy (radiation_ref.py, extra VM mode) is the main case when present; ENERGY_RC=0 skips it
  [ "${ENERGY_RC:-1}" = 1 ] && [ -f "$SUM/energy_${st%%_*}_rc.csv" ] && en="$SUM/energy_${st%%_*}_rc.csv"
  [ -f "$en" ] || { [ $REBUILD = 1 ] || echo "WARNING: $en missing, energy left empty for $st"; en=""; }
  local src=(--summary "$SUM")
  if [ $REBUILD = 1 ]; then   # copy first: the table is overwritten by its own rebuild
    local stn=$st; [ "${1:-}" = --robust-with ] && { stn=${st}_robust; shift 2; }
    cp "$PP/cell_crop_$stn.csv.gz" "$TMPCC/"; src=(--from-cell-crop "$TMPCC/cell_crop_$stn.csv.gz"); st=$stn
  fi
  $PY prod/postprocess_india.py "${src[@]}" --stage "$st" --grid $GRID --slope data/slope_india.csv \
    ${en:+--energy "$en"} --din-cap "$DIN" --outdir $PP "$@"
}
for st in "${STAGES[@]}"; do echo "== postprocess $st"; pp "$st"; done
SUMSTAGES=("${STAGES[@]}")
if [ $HAVE_REC != 0 ]; then
  echo "== postprocess historical_current, robust with historical_recommended"
  pp historical_current --robust-with historical_recommended
  SUMSTAGES=(historical_current historical_current_robust "${STAGES[@]:1}")
  [ $HAVE_REC = 1 ] && SUMSTAGES+=(historical_recommended)
fi
# robust nitrogen at mid-century (VM mode futrobust): ssp585_current with ssp585_recommended
FUTROB=0
[ $HAVE_REC != 0 ] && [ -f "$SUM/ry_crop_ssp585_recommended.csv.gz" ] && [ -f "$SUM/ry_crop_ssp585_current.csv.gz" ] && FUTROB=1
[ $REBUILD = 1 ] && [ -f "$PP/cell_crop_ssp585_current_robust.csv.gz" ] && FUTROB=1
if [ $FUTROB = 1 ]; then
  echo "== postprocess ssp585_current, robust with ssp585_recommended"
  pp ssp585_current --robust-with ssp585_recommended
  SUMSTAGES+=(ssp585_current_robust)
fi
if [ -f "$SUM/ry_crop_historical_current_season.csv.gz" ] && [ $REBUILD = 0 ]; then
  # season-by-season yield rule (season_check.py): "ry" is the share of seasons with RY >= 0.80
  echo "== postprocess season rule"
  pp historical_current_season > /dev/null
  [ -f "$SUM/ry_crop_historical_recommended_season.csv.gz" ] && \
    pp historical_current_season --robust-with historical_recommended_season > /dev/null
fi

echo "== figures"
FUT=("${STAGES[@]:1}")
$PY src/fig_india.py --pp $PP --stage historical_current --grid $GRID --boundaries data/boundaries/Admin2.shp \
  --out $FIG ${FUT[@]:+--future "${FUT[@]}"} \
  $([ $FUTROB = 1 ] && echo --future-robust ssp585_current_robust --robust-base historical_current_robust)
[ $HAVE_REC != 0 ] && $PY src/fig_india.py --pp $PP --stage historical_current_robust --grid $GRID \
  --boundaries data/boundaries/Admin2.shp --out $FIG --calib historical_current

$PY src/fig_supply.py --pp $PP --out $FIG

echo "== headline numbers"
$PY src/results_summary.py --pp $PP --stages "${SUMSTAGES[@]}" --summary "$SUM" --grid $GRID > /dev/null
echo "wrote $PP/headline_numbers.md"

if [ $REBUILD = 0 ]; then
  echo "== reconciliation waterfall (fixed density -> yield-constrained)"
  $PY src/reconcile.py --summary "$SUM" --stage historical_current --robust-with historical_recommended \
    --din-cap "$DIN" | tail -3
fi

echo "== field-response scenario (uses the committed observed curves; picks up the radiation-corrected energy table if present)"
[ -d runs/s1/summary ] && { $PY src/field_response.py 2>&1 | tail -3; }

echo "== food given up under the arrays (observed state yields x (1 - RY) at the robust GCR_max)"
if [ -f "$PP/cell_crop_historical_current_robust.csv.gz" ] && [ -f "$SUM/ry_crop_historical_current.csv.gz" ] \
   && [ -f "$SUM/ry_crop_historical_recommended.csv.gz" ]; then
  $PY src/food_tradeoff.py --pp $PP --summary "$SUM" | tail -2
  $PY src/fig_food.py --pp $PP --out $FIG --grid $GRID
fi

echo "== manuscript numbers"
$PY src/make_numbers.py --pp $PP
echo "  (build the manuscript and highlights with: node paper/methods/build_methods.js)"

echo "== graphical abstract"
FUTGA=ssp585_current; [ -f "$PP/india_combined_ssp585_current.csv" ] || FUTGA=none
(cd paper/methods && $PY graphical_abstract.py --future $FUTGA && $PY graphical_abstract_simple.py --future $FUTGA && $PY graphical_abstract_v3.py --future $FUTGA)

cat <<EOF

Done. Check before writing Results (task D):
  - $PP/headline_numbers.md, section "Sanity checks": open-field yield sim/obs near 1 for wheat and
    millet (groundnut about 2.7 is known), capacity density = GCR x 2.2 MWp/ha, kWh/kWp in range
  - share of area at the simulated GCR limit (legumes simulated to GCR 0.5, cereals to 0.7)
  - figures: $FIG/fig_india_*historical_current*.pdf and paper/methods/graphical_abstract.png
EOF
