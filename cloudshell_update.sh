#!/usr/bin/env bash
# Update the whole paper after a new stage, entirely inside Google Cloud Shell (free, no Claude needed).
# Pulls the stage summaries straight from the bucket, runs the results pipeline, fills every number in the
# manuscript, rebuilds the Word files and pushes them to GitHub.
#
# One-time setup in Cloud Shell:   gh auth login      (GitHub.com, HTTPS, login with browser)
#                                  gh auth setup-git
# Every update after a new stage:  bash ~/agripv-india/cloudshell_update.sh
#   (first time: gh repo clone Malmand/agripv-india ~/agripv-india && bash ~/agripv-india/cloudshell_update.sh)
set -euo pipefail
BUCKET=gs://project-293bae4b-5e94-4c63-bac-agripv/india/out/summary
REPO=~/agripv-india
[ -d $REPO/.git ] || gh repo clone Malmand/agripv-india $REPO
cd $REPO
git pull -q --rebase

echo "== dependencies (first run takes a few minutes)"
python3 -c "import geopandas" 2>/dev/null || pip install -q --user geopandas
(cd paper/methods && [ -d node_modules/docx ] || npm install --silent --no-save docx)

echo "== stage summaries from the bucket"
TMP=$(mktemp -d)
gsutil -q -m cp "$BUCKET/ry_crop_*_current.csv.gz" "$BUCKET/energy_*.csv" "$TMP/" || true
# recommended-N stage: only when it covers India (the 40-cell test run has the same file name)
if gsutil -q cp "$BUCKET/ry_crop_historical_recommended.csv.gz" "$TMP/" 2>/dev/null; then
  n=$(python3 -c "import pandas as p;print(p.read_csv('$TMP/ry_crop_historical_recommended.csv.gz',usecols=['cell']).cell.nunique())")
  if [ "$n" -lt 2500 ]; then echo "recommended-N stage covers only $n cells (test run): ignored"; rm "$TMP/ry_crop_historical_recommended.csv.gz"; fi
fi
ls -l "$TMP"
(cd "$TMP" && zip -q stages.zip *.csv *.csv.gz)

echo "== results pipeline"
bash run_results.sh "$TMP/stages.zip"
node paper/methods/build_methods.js
node paper/methods/build_supp.js

echo "== save to GitHub"
git config user.name "Mohamed Al-Mandhari"
git config user.email "almandharimohammed90@gmail.com"
git add -A results paper/methods
git commit -qm "Update results from stages: $(ls "$TMP" | grep -o 'ry_crop_[a-z0-9_]*' | sed 's/ry_crop_//' | tr '\n' ' ')" || echo "nothing new"
git push -q
cp paper/methods/Manuscript_AgriPV_India.docx paper/methods/Supplementary_Methods_AgriPV_India.docx ~/
echo "Done. Download ~/Manuscript_AgriPV_India.docx (menu ⋮ → Download). Check [pending] keys listed above."
