#!/bin/bash
# After the rice machine (VM mode rice, agripv-rice) finishes: brings rice into every number, figure and document.
#   bash finish_rice.sh <folder | zip with the rice summary files>
#   bash finish_rice.sh gs        # copy from gs://.../india_rice/out/summary (needs gsutil access)
# Files: ry_crop_historical_current_rice.csv.gz, ry_crop_historical_recommended_rice.csv.gz,
#        calib_rice_state_yields.csv, calib_n_with_rice.csv
# Steps: copy into runs/s1/summary -> run_results.sh (postprocess adds historical_current_robust_rice; make_numbers
# writes rice.* and sens.rice keys; tornado gains the rice bar) -> rebuild the Earth's Future documents -> Zenodo
# package -> print the rice numbers. The manuscript switches itself: rice sentences appear once rice.* keys exist.
set -euo pipefail
cd "$(dirname "$0")"
SUM=runs/s1/summary
FILES="ry_crop_historical_current_rice.csv.gz ry_crop_historical_recommended_rice.csv.gz calib_rice_state_yields.csv calib_n_with_rice.csv"
SRC=${1:?usage: bash finish_rice.sh <folder|zip|gs>}
for f in $FILES; do
  case "$SRC" in
    gs)    gsutil cp "gs://project-293bae4b-5e94-4c63-bac-agripv/india_rice/out/summary/$f" "$SUM/$f" ;;
    *.zip) unzip -o -j -q "$SRC" "*$f" -d "$SUM" ;;
    *)     cp "$SRC/$f" "$SUM/$f" ;;
  esac
done
python3 - "$SUM" <<'PY'
import sys, pandas as pd
s = sys.argv[1]
for m in ("current", "recommended"):
    d = pd.read_csv(f"{s}/ry_crop_historical_{m}_rice.csv.gz")
    print(f"rice {m}: {len(d)} rows, {d.cell.nunique()} cells, {d.model.nunique()} GCMs, configs {sorted(d.config.unique())}")
    if d.cell.nunique() < 1400 or d.model.nunique() < 5 or set(d.crop) != {"rice"}:
        sys.exit("STOP: incomplete rice stage")
PY
bash run_results.sh runs/s1
( cd paper/ef && node build_methods.js && node build_supp.js && node cover_ef.js )
bash paper/methods/build_ae.sh      # Applied Energy version from the same sources
bash make_zenodo.sh
python3 - <<'PY'
import json
v = json.load(open("results/potential/numbers.json"))["values"]
print("\nRice result")
for k in ["head.cap_twp_m", "rice.cap_twp", "rice.cap_twp_lo", "rice.cap_twp_hi", "rice.change_pct", "rice.energy_pwh",
          "rice.ov_mha", "rice.ov_share", "rice.gcr_rice", "rice.gcr_wheat", "rice.ry03_cur", "rice.ry03_rec",
          "rice.top_states", "rice.calib_err_pct", "rice.calib_n_range", "kh.nonrice_pct"]:
    print(f"  {k:24s} {v.get(k, 'MISSING')}")
PY
echo "Built paper/ef/*.docx. Check them, then commit (git add -A results paper/ef; git commit)."
