#!/bin/bash
# Builds update_india.sh: pushes new code + startup script to the existing India machine,
# sets its mode (calib | full) and starts it. Usage in Cloud Shell: bash update_india.sh <mode>
set -e
cd "$(dirname "$0")"
FILES="sim.py sim_india.py run_cells_india.py summarise_india.py status_india.py fetch_soil.py nex_to_cells.py pv_shading.py \
dssat_inputs.py dssat_pilot.py get_nex_gddp.py energy_india.py radiation_ref.py season_check.py pipeline_india.sh grid_india_025.csv test_cells.txt"
[ -f calib_n.csv ] && FILES="$FILES calib_n.csv"
CODE=$(tar -czf - $FILES | base64 -w0)
START=$(base64 -w0 startup_india.sh)
cat > update_india.sh <<UPD
#!/bin/bash
set -e
MODE=\${1:?usage: bash update_india.sh calib|full|extra|futrobust [ack]}
ACK=no; [ "\${2:-}" = "ack" ] && ACK=yes   # ack = resume after a health-check stop
gcloud config set project project-293bae4b-5e94-4c63-bac >/dev/null
TMP=\$(mktemp -d)
echo '$CODE' > \$TMP/code.b64
echo '$START' | base64 -d > \$TMP/startup.sh
gcloud compute instances add-metadata agripv-india --zone europe-west1-b --metadata mode=\$MODE,halt_ack=\$ACK \\
  --metadata-from-file code=\$TMP/code.b64,startup-script=\$TMP/startup.sh
gcloud compute instances start agripv-india --zone europe-west1-b
echo "Machine started in mode \$MODE. Check: gsutil cat gs://project-293bae4b-5e94-4c63-bac-agripv/india/status.txt"
UPD
echo "update_india.sh $(wc -c < update_india.sh) bytes; files: $FILES"
