#!/bin/bash
# AgriPV Rajasthan pipeline on the VM. Idempotent: every step skips finished work,
# so a reboot (or re-running this script) resumes where it stopped.
set -u
APP=/opt/agripv
DATA=/data
BUCKET=$(curl -s -H "Metadata-Flavor: Google" \
  "http://metadata.google.internal/computeMetadata/v1/instance/attributes/bucket")
PY=$APP/venv/bin/python
LOG=$DATA/pipeline.log
MODELS=(GFDL-ESM4 IPSL-CM6A-LR MPI-ESM1-2-HR MRI-ESM2-0 UKESM1-0-LL)
export PYTHONWARNINGS=ignore
mkdir -p $DATA/nex $DATA/cells $DATA/soil $DATA/out
exec >>"$LOG" 2>&1
say() { echo "[$(date -u +%F' '%T)] $*"; }
push() { gsutil -q -m rsync -r $DATA/out "gs://$BUCKET/out"; gsutil -q cp "$LOG" "gs://$BUCKET/pipeline.log"; }

say "=== pipeline start ($(nproc) vCPU)"
( while sleep 1200; do gsutil -q cp "$LOG" "gs://$BUCKET/pipeline.log"; done ) &

# 1. climate download and soil fetch in parallel
if [ ! -f $DATA/nex/.done ]; then
  cp $APP/get_nex_gddp.py $DATA/nex/
  sed -i 's/^WORKERS = .*/WORKERS = 8/' $DATA/nex/get_nex_gddp.py
  ( cd $DATA/nex && for i in 1 2 3 4; do
      $PY get_nex_gddp.py | tee last_try.log | tail -3
      grep -q "Finished. 0 missing" last_try.log && touch .done && break
    done ) > $DATA/nex/download.log 2>&1 &
  PID_NEX=$!
fi
if [ ! -f $DATA/soil/.done ]; then
  ( $PY $APP/fetch_soil.py --grid $APP/grid_rajasthan_025.csv --out $DATA/soil && touch $DATA/soil/.done ) \
    > $DATA/soil/fetch.log 2>&1 &
  PID_SOIL=$!
fi
for p in ${PID_NEX:-} ${PID_SOIL:-}; do wait $p; done  # not a bare wait: the log-upload loop never ends
say "download: $(ls $DATA/nex/.done 2>/dev/null || echo INCOMPLETE), soil: $(ls $DATA/soil/.done 2>/dev/null || echo INCOMPLETE)"
tail -2 $DATA/nex/download.log $DATA/soil/fetch.log
gsutil -q cp $DATA/nex/download.log $DATA/soil/fetch.log "gs://$BUCKET/logs/"
gsutil -q -m rsync -r $DATA/soil "gs://$BUCKET/soil"
if [ ! -f $DATA/nex/.done ] || [ ! -f $DATA/soil/.done ]; then
  say "STOP: inputs incomplete, see logs. Machine shuts down; restart it to retry."
  push; shutdown -h now; exit 1
fi

# 2. NetCDF -> per-cell arrays (4 conversions at a time)
for m in "${MODELS[@]}"; do for s in historical ssp245 ssp585; do
  [ -f $DATA/cells/cells_${m}_${s}.npz ] && continue
  echo "$m $s"
done; done | xargs -P 4 -L 1 bash -c \
  "$PY $APP/nex_to_cells.py --data $DATA/nex/data --model \$0 --scen \$1 --grid $APP/grid_rajasthan_025.csv --out $DATA/cells"
say "cells: $(ls $DATA/cells/*.npz | wc -l)/15"

# 3. crop simulations, stage by stage; each stage retried once for failed tasks
for stage in historical:farmer ssp245:farmer ssp585:farmer historical:recommended \
             ssp245:recommended ssp585:recommended; do
  p=${stage%:*}; g=${stage#*:}
  for try in 1 2; do
    say "stage $p $g (try $try)"
    $PY $APP/run_cells.py --cells $DATA/cells --soil $DATA/soil --out $DATA/out --period $p --mgmt $g \
      --workers $(nproc) && break
  done
  $PY $APP/summarise.py --out $DATA/out --grid $APP/grid_rajasthan_025.csv | tail -30
  push
done

say "=== pipeline finished; shutting down"
touch $DATA/ALL_DONE
push
gsutil -q cp $DATA/ALL_DONE "gs://$BUCKET/ALL_DONE"
shutdown -h now
