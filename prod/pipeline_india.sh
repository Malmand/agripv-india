#!/bin/bash
# AgriPV India pipeline on the VM. Idempotent: every step skips finished work, so a
# reboot (or re-running this script) resumes where it stopped.
# Metadata "mode": test  -> inputs, India-wide open-field validation, 40-cell APV test, then shut down
#                  full  -> the four production stages, then shut down
set -u
APP=/opt/agripv
DATA=/data
md() { curl -s -H "Metadata-Flavor: Google" "http://metadata.google.internal/computeMetadata/v1/instance/attributes/$1"; }
BUCKET=$(md bucket)
MODE=$(md mode); MODE=${MODE:-test}
PY=$APP/venv/bin/python
LOG=$DATA/pipeline.log
GRID=$APP/grid_india_025.csv
MODELS=(GFDL-ESM4 IPSL-CM6A-LR MPI-ESM1-2-HR MRI-ESM2-0 UKESM1-0-LL)
export PYTHONWARNINGS=ignore
export AGRIPV_BBOX="37.25,6.5,68.0,97.5"
mkdir -p $DATA/nex $DATA/cells $DATA/soil $DATA/out
exec >>"$LOG" 2>&1
say() { echo "[$(date -u +%F' '%T)] $*"; }
push() { gsutil -q -m rsync -r -x '.*\.part$' $DATA/out "gs://$BUCKET/out"; gsutil -q cp "$LOG" "gs://$BUCKET/pipeline.log"; }
status() {  # progress + health report to the bucket; halts the run if results look wrong
  $PY $APP/status_india.py; rc=$?
  gsutil -q cp $DATA/status.txt "gs://$BUCKET/status.txt"
  if [ $rc -eq 3 ]; then
    say "HALT: $(cat $DATA/HALT | tr '\n' ' ')"
    pkill -f run_cells_india; push
    gsutil -q cp $DATA/HALT "gs://$BUCKET/HALT"
    shutdown -h now
  fi
}

say "=== pipeline start ($(nproc) vCPU), mode=$MODE"
( sleep 300; status; while sleep 1200; do status; push; done ) &
SYNC_PID=$!
trap 'kill $SYNC_PID 2>/dev/null' EXIT

# 1. climate download and soil fetch in parallel (explicit PIDs: never a bare wait)
PIDS=""
if [ ! -f $DATA/nex/.done ]; then
  cp $APP/get_nex_gddp.py $DATA/nex/
  sed -i 's/^WORKERS = .*/WORKERS = 8/' $DATA/nex/get_nex_gddp.py
  ( cd $DATA/nex && for i in 1 2 3 4 5; do
      $PY get_nex_gddp.py | tee last_try.log | tail -3
      grep -q "Finished. 0 missing" last_try.log && touch .done && break
    done ) > $DATA/nex/download.log 2>&1 &
  PIDS="$PIDS $!"
fi
if [ ! -f $DATA/soil/.done ]; then
  ( for i in 1 2 3; do
      $PY $APP/fetch_soil.py --grid $GRID --out $DATA/soil && touch $DATA/soil/.done && break
    done ) > $DATA/soil/fetch.log 2>&1 &
  PIDS="$PIDS $!"
fi
for p in $PIDS; do wait $p; done
say "download: $(ls $DATA/nex/.done 2>/dev/null || echo INCOMPLETE), soil: $(ls $DATA/soil/.done 2>/dev/null || echo INCOMPLETE)"
tail -2 $DATA/nex/download.log $DATA/soil/fetch.log
gsutil -q cp $DATA/nex/download.log $DATA/soil/fetch.log "gs://$BUCKET/logs/"
gsutil -q -m rsync -r $DATA/soil "gs://$BUCKET/soil"
if [ ! -f $DATA/nex/.done ] || [ ! -f $DATA/soil/.done ]; then
  say "STOP: inputs incomplete, see logs. Machine shuts down; start it again to retry."
  push; shutdown -h now; exit 1
fi

# 2. NetCDF -> per-cell arrays (uncompressed .npy, memory-mapped by the workers)
for m in "${MODELS[@]}"; do for s in historical ssp245 ssp585; do
  [ -f $DATA/cells/cells_${m}_${s}.npy ] && continue
  echo "$m $s"
done; done | xargs -P 3 -L 1 bash -c \
  "$PY $APP/nex_to_cells.py --data $DATA/nex/data --model \$0 --scen \$1 --grid $GRID --out $DATA/cells --format npy"
say "cells: $(ls $DATA/cells/*.npy | grep -v part | wc -l)/15"

run() {  # run <period> <mgmt> [extra args]: one stage, retried once for failed tasks
  for try in 1 2; do
    say "stage $* (try $try)"
    $PY $APP/run_cells_india.py --cells $DATA/cells --grid $GRID --soil $DATA/soil --out $DATA/out \
      --period $1 --mgmt $2 "${@:3}" --workers $(nproc) && break
  done
}

if [ "$MODE" = "test" ]; then
  # 3a. India-wide open-field validation (farmer practice, all cells, all models; ~1/60 of a stage)
  run historical farmer --open-only
  $PY $APP/summarise_india.py --out $DATA/out --grid $GRID --stage historical_farmer_open | tail -3
  # 3b. full APV simulation on 40 test cells, recommended practice, all models
  run historical recommended --only $APP/test_cells.txt
  $PY $APP/summarise_india.py --out $DATA/out --grid $GRID --stage historical_recommended | tail -40
  status; push
  touch $DATA/TEST_DONE && gsutil -q cp $DATA/TEST_DONE "gs://$BUCKET/TEST_DONE"
  say "=== test finished; shutting down. Set metadata mode=full and start the machine for the full run."
  push; shutdown -h now; exit 0
fi

if [ "$MODE" = "calib" ]; then
  # 3c. nitrogen calibration sweep: open field, wheat and pearl millet, two climate models
  for n in 30 60 90 120 180; do
    run historical n$n --open-only --crops wheat,pearl_millet --models GFDL-ESM4,MPI-ESM1-2-HR
    $PY $APP/summarise_india.py --out $DATA/out --grid $GRID --stage historical_n${n}_open | tail -2
  done
  status; push
  touch $DATA/CALIB_DONE && gsutil -q cp $DATA/CALIB_DONE "gs://$BUCKET/CALIB_DONE"
  say "=== calibration sweep finished; shutting down"
  push; shutdown -h now; exit 0
fi

if [ "$MODE" = "extra" ]; then
  # 3d. review analyses after the four production stages (run once; each step skips finished work)
  #  (a) radiation bias factors against NASA POWER, (b) radiation-corrected PV energy for each period,
  #  (c) crop test with corrected radiation on 40 strongly biased cells, (d) season-by-season yield rule
  S=$DATA/out/summary
  [ -f $S/rad_factors.csv ] || ( cd $APP && $PY radiation_ref.py --cells $DATA/cells --grid $GRID --out $S ) | tail -3
  push
  for p in historical ssp585 ssp245; do
    [ -f $S/energy_${p}_rc.csv ] && continue
    [ -f $DATA/cells/cells_GFDL-ESM4_${p}.npy ] || continue
    say "energy $p, radiation-corrected"
    ( cd $APP && $PY energy_india.py --cells $DATA/cells --grid $GRID --period $p --out $S \
        --srad-factors $S/rad_factors.csv --tag _rc ) | tail -2
    push
  done
  if [ ! -f $S/ry_crop_historical_current_rc.csv.gz ]; then
    # 40 cells with the largest radiation bias among cells with at least 5000 ha of the four crops
    $PY - <<PYEOF > $DATA/rc_cells.txt
import pandas as pd
k = pd.read_csv("$S/rad_factors.csv").groupby("cell")[["nex_kwh", "ref_kwh"]].mean()
k = (k.ref_kwh / k.nex_kwh).rename("k")
g = pd.read_csv("$GRID").set_index("cell_id")
area = g[[c for c in g.columns if c.endswith("_ha")]].sum(axis=1)
c = k[k.index.isin(area[area >= 5000].index)].sort_values().head(40)
print("\n".join(c.index))
PYEOF
    say "radiation test on $(wc -l < $DATA/rc_cells.txt) cells"
    export AGRIPV_SRAD_FACTORS=$S/rad_factors.csv AGRIPV_STAGE_SUFFIX=_rc
    run historical current --only $DATA/rc_cells.txt
    unset AGRIPV_SRAD_FACTORS AGRIPV_STAGE_SUFFIX
    $PY $APP/summarise_india.py --out $DATA/out --grid $GRID --stage historical_current_rc | tail -3
    push
  fi
  for st in historical_current historical_recommended; do
    [ -f $S/ry_crop_${st}_season.csv.gz ] || ( cd $APP && $PY season_check.py --out $DATA/out --grid $GRID --stage $st ) | tail -2
  done
  status; push
  touch $DATA/EXTRA_DONE && gsutil -q cp $DATA/EXTRA_DONE "gs://$BUCKET/EXTRA_DONE"
  say "=== extra analyses finished; shutting down"
  push; shutdown -h now; exit 0
fi

if [ "$MODE" = "futrobust" ]; then
  # 3e. robust-nitrogen case for mid-century: recommended-N stages for SSP5-8.5 then SSP2-4.5
  #     (PV energy per period already exists from the production run; each step skips finished work)
  for p in ssp585 ssp245; do
    run $p recommended
    $PY $APP/summarise_india.py --out $DATA/out --grid $GRID --stage ${p}_recommended | tail -40
    status; push
    say "stage ${p}_recommended uploaded"
  done
  touch $DATA/FUTROBUST_DONE && gsutil -q cp $DATA/FUTROBUST_DONE "gs://$BUCKET/FUTROBUST_DONE"
  say "=== future robust stages finished; shutting down"
  push; shutdown -h now; exit 0
fi

# 4. production stages, most important first (a stop part-way still leaves usable results)
#    current = state-calibrated N (main case); recommended = adequate N (sensitivity)
for stage in historical:current ssp585:current historical:recommended ssp245:current; do
  p=${stage%:*}; g=${stage#*:}
  run $p $g
  $PY $APP/summarise_india.py --out $DATA/out --grid $GRID --stage ${p}_${g} | tail -40
  # PV specific yield for this climate period (once per period, ~2 h)
  if [ ! -f $DATA/out/summary/energy_${p}.csv ]; then
    say "energy $p"
    ( cd $APP && $PY energy_india.py --cells $DATA/cells --grid $GRID --period $p --out $DATA/out/summary ) | tail -2
  fi
  status; push
  say "stage ${p}_${g} uploaded"
done
say "=== pipeline finished; shutting down"
touch $DATA/ALL_DONE
push
gsutil -q cp $DATA/ALL_DONE "gs://$BUCKET/ALL_DONE"
shutdown -h now
