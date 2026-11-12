#!/bin/bash
# After the VM mode "futrobust" finishes: brings the robust-nitrogen SSP5-8.5 stage into every number, figure and
# document of the Earth's Future version, in one command.
#   bash finish_futrobust.sh <ry_crop_ssp585_recommended.csv.gz | folder or zip containing it>
#   bash finish_futrobust.sh gs     # copy it from the GCP bucket (needs gsutil with access to the project)
# Steps: copy into runs/s1/summary -> run_results.sh (postprocess incl. ssp585_current_robust, figures, numbers.json)
# -> rebuild the Earth's Future manuscript, supporting information and cover letter -> print the new key numbers.
# The manuscript text switches itself: sentences that need ssp585r.* / fut.* keys appear once they exist
# (see paper/ef/*.js and src/make_numbers.py future_headline). Nothing is committed; check, then commit.
set -euo pipefail
cd "$(dirname "$0")"
SUM=runs/s1/summary
F=ry_crop_ssp585_recommended.csv.gz
SRC=${1:?usage: bash finish_futrobust.sh <file|folder|zip|gs>}
case "$SRC" in
  gs)    gsutil cp "gs://project-293bae4b-5e94-4c63-bac-agripv/india/out/summary/$F" "$SUM/$F" ;;
  *.zip) unzip -o -j -q "$SRC" "*$F" -d "$SUM" ;;
  *)     if [ -d "$SRC" ]; then cp "$SRC/$F" "$SUM/$F"; else cp "$SRC" "$SUM/$F"; fi ;;
esac
python3 - "$SUM/$F" <<'PY'
import sys, pandas as pd
d = pd.read_csv(sys.argv[1])
ok = set(d.period) == {"ssp585"} and set(d.mgmt) == {"recommended"}
print(f"{sys.argv[1]}: {len(d)} rows, {d.cell.nunique()} cells, {d.model.nunique()} GCMs, crops {sorted(d.crop.unique())}")
if not ok or d.cell.nunique() < 2900 or d.model.nunique() < 5:
    sys.exit("STOP: file is not a complete ssp585 recommended stage")
PY
bash run_results.sh runs/s1
( cd paper/ef && node build_methods.js && node build_supp.js && node cover_ef.js )
python3 - <<'PY'
import json
v = json.load(open("results/potential/numbers.json"))["values"]
keys = ["head.cap_twp_m", "ssp585.change_pct", "ssp585r.change_pct", "ssp585r.change_lo", "ssp585r.change_hi",
        "ssp585r.energy_change_pct", "ssp585r.n_diff_pp", "fut.size", "fut.kp_phrase", "fut.n_compare",
        "ssp585r.gcr_wheat_delta", "ssp585r.gcr_pearl_millet_delta", "ssp585r.gcr_chickpea_delta",
        "ssp585r.gcr_groundnut_delta"]
print("\nRobust mid-century result")
for k in keys:
    print(f"  {k:32s} {v.get(k, 'MISSING')}")
PY
echo "Built paper/ef/*.docx. Check them, then commit (git add -A results paper/ef; git commit)."
