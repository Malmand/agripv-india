#!/usr/bin/env bash
# Results pipeline (task D) in one command, run from anywhere:
#   bash run_results.sh /path/to/s1.zip
# s1.zip holds the stage summaries from gs://.../india/out/summary, at least
#   ry_crop_historical_current.csv.gz and energy_historical.csv
# and optionally ry_crop_historical_recommended.csv.gz (robust case) and later stages
# (ry_crop_ssp245_current.csv.gz + energy_ssp245.csv, ...). Folders inside the zip are ignored.
# Steps: unzip -> runs/s1/summary, postprocess every *_current stage (with energy if present),
# robust case (min of calibrated and recommended N), figures, headline numbers, graphical abstract.
# Outputs: results/potential/ (tables, headline_numbers.md), results/figures/fig_india_*.pdf,
# paper/methods/graphical_abstract.{pdf,png}. Nothing is committed.
set -euo pipefail
ZIP=${1:?usage: bash run_results.sh /path/to/s1.zip}
ZIP=$(realpath "$ZIP")
PY=${PY:-python3}
cd "$(dirname "$(realpath "$0")")"
SUM=runs/s1/summary
PP=results/potential
FIG=results/figures
GRID=data/grid_india_025.csv

$PY -c "import numpy, pandas, matplotlib, geopandas" 2>/dev/null || {
  echo "missing Python packages: pip install numpy pandas matplotlib geopandas"; exit 1; }

mkdir -p "$SUM" "$PP" "$FIG"
unzip -o -j -q "$ZIP" '*.csv' '*.csv.gz' -d "$SUM"
echo "== files in $SUM"; ls -l "$SUM"
[ -f "$SUM/ry_crop_historical_current.csv.gz" ] || { echo "ry_crop_historical_current.csv.gz not in zip"; exit 1; }

# stages: historical_current first, then any other *_current (future) stages
STAGES=(historical_current)
for f in "$SUM"/ry_crop_*_current.csv.gz; do
  s=$(basename "$f" .csv.gz); s=${s#ry_crop_}
  [ "$s" = historical_current ] || STAGES+=("$s")
done
HAVE_REC=0; [ -f "$SUM/ry_crop_historical_recommended.csv.gz" ] && HAVE_REC=1

pp() {  # stage [extra args]
  local st=$1; shift
  local en="$SUM/energy_${st%%_*}.csv"
  [ -f "$en" ] || { echo "WARNING: $en missing, energy left empty for $st"; en=""; }
  $PY prod/postprocess_india.py --summary "$SUM" --stage "$st" --grid $GRID --slope data/slope_india.csv \
    ${en:+--energy "$en"} --outdir $PP "$@"
}
for st in "${STAGES[@]}"; do echo "== postprocess $st"; pp "$st"; done
SUMSTAGES=("${STAGES[@]}")
if [ $HAVE_REC = 1 ]; then
  echo "== postprocess historical_current, robust with historical_recommended"
  pp historical_current --robust-with historical_recommended
  SUMSTAGES=(historical_current historical_current_robust "${STAGES[@]:1}" historical_recommended)
fi

echo "== figures"
FUT=("${STAGES[@]:1}")
$PY src/fig_india.py --pp $PP --stage historical_current --grid $GRID --boundaries data/boundaries/Admin2.shp \
  --out $FIG ${FUT[@]:+--future "${FUT[@]}"}
[ $HAVE_REC = 1 ] && $PY src/fig_india.py --pp $PP --stage historical_current_robust --grid $GRID \
  --boundaries data/boundaries/Admin2.shp --out $FIG

echo "== headline numbers"
$PY src/results_summary.py --pp $PP --stages "${SUMSTAGES[@]}" --summary "$SUM" --grid $GRID > /dev/null
echo "wrote $PP/headline_numbers.md"

echo "== graphical abstract"
FUTGA=ssp245_current; [ -f "$PP/india_combined_ssp245_current.csv" ] || FUTGA=none
(cd paper/methods && $PY graphical_abstract.py --future $FUTGA)

cat <<EOF

Done. Check before writing Results (task D):
  - $PP/headline_numbers.md, section "Sanity checks": open-field yield sim/obs near 1 for wheat and
    millet (groundnut about 2.7 is known), capacity density = GCR x 2.2 MWp/ha, kWh/kWp in range
  - share of area at the simulated GCR limit (legumes simulated to GCR 0.5, cereals to 0.7)
  - figures: $FIG/fig_india_*historical_current*.pdf and paper/methods/graphical_abstract.png
EOF
