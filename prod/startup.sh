#!/bin/bash
# VM startup script: install once, then (re)start the pipeline in the background.
set -u
APP=/opt/agripv
md() { curl -s -H "Metadata-Flavor: Google" "http://metadata.google.internal/computeMetadata/v1/instance/attributes/$1"; }
[ -f /data/ALL_DONE ] && exit 0
mkdir -p $APP /data
if [ ! -f $APP/.installed ]; then
  apt-get update -q && apt-get install -y -q curl ca-certificates
  md code | base64 -d | tar -xz -C $APP
  curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh
  uv venv -q -p 3.13 $APP/venv
  VIRTUAL_ENV=$APP/venv uv pip install -q DSSATTools==3.0.2 pvlib==0.16.1 pandas==3.0.5 numpy==2.5.3 \
    scipy xarray netCDF4 rasterio pyproj
  touch $APP/.installed
fi
systemd-run --unit=agripv --collect bash $APP/pipeline.sh
