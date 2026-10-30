#!/bin/bash
# Builds launch.sh: one self-contained file for Google Cloud Shell.
set -e
cd "$(dirname "$0")"
FILES="sim.py run_cells.py summarise.py fetch_soil.py nex_to_cells.py pv_shading.py dssat_inputs.py dssat_pilot.py get_nex_gddp.py pipeline.sh grid_rajasthan_025.csv"
CODE=$(tar -czf - $FILES | base64 -w0)
START=$(base64 -w0 startup.sh)
cat > launch.sh <<LAUNCH
#!/bin/bash
# AgriPV Rajasthan run on Google Cloud. Paste into Cloud Shell: bash launch.sh
set -e
PROJECT=project-293bae4b-5e94-4c63-bac
REGION=europe-west1; ZONE=europe-west1-b; VM=agripv-raj
BUCKET=\${PROJECT}-agripv
gcloud config set project \$PROJECT
gcloud services enable compute.googleapis.com storage.googleapis.com
gcloud storage buckets describe gs://\$BUCKET >/dev/null 2>&1 || gcloud storage buckets create gs://\$BUCKET --location \$REGION
PNUM=\$(gcloud projects describe \$PROJECT --format='value(projectNumber)')
for i in 1 2 3 4 5 6; do
  gcloud storage buckets add-iam-policy-binding gs://\$BUCKET \\
    --member serviceAccount:\${PNUM}-compute@developer.gserviceaccount.com --role roles/storage.objectAdmin \\
    >/dev/null 2>&1 && break
  echo "waiting for the compute service account..."; sleep 20
done
TMP=\$(mktemp -d)
echo '$CODE' > \$TMP/code.b64
echo '$START' | base64 -d > \$TMP/startup.sh
gcloud compute instances create \$VM --zone \$ZONE --machine-type e2-custom-12-24576 \\
  --image-family debian-12 --image-project debian-cloud --boot-disk-size 60GB --boot-disk-type pd-balanced \\
  --scopes storage-rw --metadata bucket=\$BUCKET \\
  --metadata-from-file startup-script=\$TMP/startup.sh,code=\$TMP/code.b64
cat <<MSG

Started. The machine works on its own; you can close this tab.
Progress (updates every 20 min):   gsutil cat gs://\$BUCKET/pipeline.log | tail -5
Live view:                         gcloud compute ssh \$VM --zone \$ZONE --command 'tail -5 /data/pipeline.log'
Finished when this exists:         gsutil ls gs://\$BUCKET/ALL_DONE
Get results:                       gsutil -m cp -r gs://\$BUCKET/out .
Resume after a stop:               gcloud compute instances start \$VM --zone \$ZONE
MSG
LAUNCH
echo "launch.sh $(wc -c < launch.sh) bytes, code $(echo -n $CODE | wc -c) b64 bytes"
