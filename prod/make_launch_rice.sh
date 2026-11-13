#!/bin/bash
# Builds launch_rice.sh: one self-contained file for Google Cloud Shell that starts a SECOND machine (agripv-rice)
# for the rice stages (mode rice), writing to gs://<bucket>/india_rice. It never touches agripv-india or .../india.
set -e
cd "$(dirname "$0")"
FILES="sim.py sim_india.py run_cells_india.py summarise_india.py status_india.py fetch_soil.py nex_to_cells.py pv_shading.py \
dssat_inputs.py dssat_pilot.py get_nex_gddp.py pipeline_india.sh grid_india_025_kharif.csv \
calib_n.csv calibrate_rice.py rice_obs_state.csv"
CODE=$(tar -czf - $FILES | base64 -w0)
START=$(base64 -w0 startup_india.sh)
cat > launch_rice.sh <<LAUNCH
#!/bin/bash
# AgriPV India, rice after wheat/chickpea, on a second machine. In Cloud Shell: bash launch_rice.sh
set -e
PROJECT=project-293bae4b-5e94-4c63-bac
ZONE=europe-west1-b; VM=agripv-rice
BUCKET=\${PROJECT}-agripv
gcloud config set project \$PROJECT >/dev/null
TMP=\$(mktemp -d)
echo '$CODE' > \$TMP/code.b64
echo '$START' | base64 -d > \$TMP/startup.sh
gcloud compute instances create \$VM --zone \$ZONE --machine-type e2-custom-16-32768 \\
  --image-family debian-12 --image-project debian-cloud --boot-disk-size 80GB --boot-disk-type pd-balanced \\
  --scopes storage-rw --metadata bucket=\$BUCKET/india_rice,mode=rice,soilsrc=\$BUCKET/india/soil \\
  --metadata-from-file startup-script=\$TMP/startup.sh,code=\$TMP/code.b64
cat <<MSG

Rice machine started (agripv-rice). It downloads 1995-2014 climate data (a few hours), copies the soil profiles of
the main run, runs the rice nitrogen calibration and then the two rice stages, and switches itself off.
Progress and health:   gsutil cat gs://\$BUCKET/india_rice/status.txt
Calibration result:    gsutil cat gs://\$BUCKET/india_rice/out/summary/calib_n_with_rice.csv
Finished when:         gsutil ls gs://\$BUCKET/india_rice/RICE_DONE
Stopped by health check if this exists: gsutil cat gs://\$BUCKET/india_rice/HALT
MSG
LAUNCH
echo "launch_rice.sh $(wc -c < launch_rice.sh) bytes"
