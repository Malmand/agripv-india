"""Run in Google Cloud Shell: fetch crop-area and crop-calendar inputs for the India run.

1. MapSPAM 2010 v2.0 harvested area (IFPRI), GeoTIFF, 5 arcmin: wheat, pearl
   millet, chickpea, groundnut; all / irrigated / rainfed. Subset to India's
   bounding box and saved as one CSV of non-zero pixels.
2. GGCMI Phase 3 crop calendar v1.01 (Jaegermeyr et al. 2021), 0.5 deg,
   irrigated and rainfed: spring and winter wheat, millet, groundnut, pulses.
Output: india_inputs.zip (a few MB). Usage:
    pip3 install --user -q rasterio && python3 fetch_india_inputs.py
"""
import io
import os
import re
import urllib.request
import zipfile

import numpy as np
import rasterio
from rasterio.windows import from_bounds

# IFPRI MapSPAM on Harvard Dataverse (the old S3 bucket now returns 403)
DATAVERSE = "https://dataverse.harvard.edu"
SPAM_DOIS = ["doi:10.7910/DVN/PRFF8V",   # SPAM 2010 v2.0 (matches the 1995-2014 baseline best)
             "doi:10.7910/DVN/SWPENT"]   # SPAM 2020 v1.0 (fallback)
CAL = ("https://svn-ccsm-inputdata.cgd.ucar.edu/trunk/inputdata/lnd/clm2/cropdata/calendars/"
       "raw_ggcmi3_v1.01_cdf5/{c}_{w}_ggcmi_crop_calendar_phase3_v1.01.nc")
CROPS = ["WHEA", "PMIL", "CHIC", "GROU"]
BBOX = (68.0, 6.0, 97.5, 37.5)   # W, S, E, N
os.makedirs("india_inputs", exist_ok=True)

import json


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research data download)"})
    return urllib.request.urlopen(req, timeout=600)


for c in ["swh", "wwh", "mil", "nut", "pea"]:
    for w in ["ir", "rf"]:
        url = CAL.format(c=c, w=w)
        with get(url) as r, open(f"india_inputs/{os.path.basename(url)}", "wb") as f:
            f.write(r.read())
print("calendars downloaded", flush=True)

z = None
for doi in SPAM_DOIS:
    meta = json.load(get(f"{DATAVERSE}/api/datasets/:persistentId/?persistentId={doi}"))
    files = meta["data"]["latestVersion"]["files"]
    print(doi, "files:", [f["dataFile"]["filename"] for f in files], flush=True)
    pick = [f for f in files if re.search(r"harv", f["dataFile"]["filename"], re.I)
            and re.search(r"tif", f["dataFile"]["filename"], re.I)]
    if not pick:
        continue
    fid, fname = pick[0]["dataFile"]["id"], pick[0]["dataFile"]["filename"]
    print(f"downloading {fname} ({pick[0]['dataFile'].get('filesize', 0) // 2**20} MB) ...", flush=True)
    try:
        with get(f"{DATAVERSE}/api/access/datafile/{fid}") as r, open("spam_harv.zip", "wb") as f:
            while True:
                b = r.read(2**22)
                if not b:
                    break
                f.write(b)
        z = zipfile.ZipFile("spam_harv.zip")
        print("using", doi, fname, flush=True)
        open("india_inputs/spam_source.txt", "w").write(f"{doi} {fname}\n")
        break
    except Exception as e:
        print(f"  failed: {e}", flush=True)
if z is None:
    raise SystemExit("MapSPAM download failed; paste this output to Claude")
names = [n for n in z.namelist() if n.lower().endswith(".tif")]
want = [n for n in names if re.search(r"_H_(%s)_(A|I|R)\.tif$" % "|".join(CROPS), n, re.I)]
print(f"{len(names)} rasters in archive, using {len(want)}:", [os.path.basename(n) for n in want], flush=True)
cols, lon, lat = {}, None, None
for n in sorted(want):
    with rasterio.open(io.BytesIO(z.read(n))) as src:
        win = from_bounds(*BBOX, transform=src.transform)
        a = src.read(1, window=win).astype("float32")
        a[a < 0] = 0
        if lon is None:
            t = src.window_transform(win)
            lon = t.c + (np.arange(a.shape[1]) + 0.5) * t.a
            lat = t.f + (np.arange(a.shape[0]) + 0.5) * t.e
        key = re.search(r"_H_(\w+)_(\w)\.tif$", n, re.I)
        cols[f"{key.group(1).lower()}_{key.group(2).lower()}"] = a
LON, LAT = np.meshgrid(lon, lat)
total = sum(v for k, v in cols.items() if k.endswith("_a"))
m = total > 0
with open("india_inputs/spam_india_harv_ha.csv", "w") as f:
    keys = sorted(cols)
    f.write("lon,lat," + ",".join(keys) + "\n")
    for i, j in zip(*np.where(m)):
        f.write(f"{LON[i, j]:.5f},{LAT[i, j]:.5f}," + ",".join(f"{cols[k][i, j]:.1f}" for k in keys) + "\n")
print(f"SPAM: {m.sum()} pixels with any of {CROPS}", flush=True)

with zipfile.ZipFile("india_inputs.zip", "w", zipfile.ZIP_DEFLATED) as zz:
    for fn in sorted(os.listdir("india_inputs")):
        zz.write(f"india_inputs/{fn}", fn)
os.remove("spam_harv.zip")
print("wrote india_inputs.zip", os.path.getsize("india_inputs.zip") // 1024, "KB")
