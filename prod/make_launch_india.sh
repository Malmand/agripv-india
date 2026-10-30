#!/bin/bash
# Builds launch_india.sh: one self-contained file for Google Cloud Shell.
set -e
cd "$(dirname "$0")"
FILES="sim.py sim_india.py run_cells_india.py summarise_india.py status_india.py fetch_soil.py nex_to_cells.py pv_shading.py \
dssat_inputs.py dssat_pilot.py get_nex_gddp.py pipeline_india.sh grid_india_025.csv test_cells.txt"
CODE=$(tar -czf - $FILES | base64 -w0)
START=$(base64 -w0 startup_india.sh)
cat > launch_india.sh <<LAUNCH
#!/bin/bash
# AgriPV India run on Google Cloud. In Cloud Shell: bash launch_india.sh
# Creates the machine in TEST mode: inputs + India-wide validation + 40-cell test, then it stops.
set -e
PROJECT=project-293bae4b-5e94-4c63-bac
REGION=europe-west1; ZONE=europe-west1-b; VM=agripv-india
BUCKET=\${PROJECT}-agripv
gcloud config set project \$PROJECT
TMP=\$(mktemp -d)
echo '$CODE' > \$TMP/code.b64
echo '$START' | base64 -d > \$TMP/startup.sh
gcloud compute instances create \$VM --zone \$ZONE --machine-type e2-custom-12-24576 \\
  --image-family debian-12 --image-project debian-cloud --boot-disk-size 120GB --boot-disk-type pd-balanced \\
  --scopes storage-rw --metadata bucket=\$BUCKET/india,mode=test \\
  --metadata-from-file startup-script=\$TMP/startup.sh,code=\$TMP/code.b64
# budget alerts at 60% and 80% of 250 EUR (emails to the billing account owner; skipped if not permitted)
BA=\$(gcloud billing projects describe \$PROJECT --format='value(billingAccountName)' 2>/dev/null | sed 's#.*/##')
[ -n "\$BA" ] && gcloud billing budgets create --billing-account=\$BA --display-name=agripv-india \\
  --budget-amount=250EUR --threshold-rule=percent=0.6 --threshold-rule=percent=0.8 >/dev/null 2>&1 \\
  && echo "budget alerts set" || echo "(budget alert not set; not essential)"
cat <<MSG

Started in TEST mode. It downloads climate data and soil for India (several hours),
runs the India-wide open-field validation and the 40-cell test, then switches itself off.
Check any time (progress, ETA, sanity numbers, health):
    gsutil cat gs://\$BUCKET/india/status.txt
Test done when this exists:  gsutil ls gs://\$BUCKET/india/TEST_DONE
Stopped by a health check if this exists:  gsutil cat gs://\$BUCKET/india/HALT
MSG
LAUNCH
echo "launch_india.sh $(wc -c < launch_india.sh) bytes"
