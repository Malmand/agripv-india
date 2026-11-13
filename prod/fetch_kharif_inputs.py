"""Run in Google Cloud Shell: MapSPAM 2010 harvested area of the kharif crops that follow wheat and chickpea
(rice, maize, soybean, cotton, sorghum, pigeonpea, sugarcane; all / irrigated / rainfed) and the GGCMI Phase 3
rice calendar (ri1 = main season), for India. Same sources and method as fetch_india_inputs.py.
    pip3 install --user -q rasterio && python3 fetch_kharif_inputs.py      -> kharif_inputs.zip (~15 MB)
"""
import io, json, os, re, urllib.request, zipfile
import numpy as np
import rasterio
from rasterio.windows import from_bounds

DATAVERSE = "https://dataverse.harvard.edu"
DOI = "doi:10.7910/DVN/PRFF8V"   # SPAM 2010 v2.0, as for the four simulated crops
CAL = ("https://svn-ccsm-inputdata.cgd.ucar.edu/trunk/inputdata/lnd/clm2/cropdata/calendars/"
       "raw_ggcmi3_v1.01_cdf5/{c}_{w}_ggcmi_crop_calendar_phase3_v1.01.nc")
CROPS = ["RICE", "MAIZ", "SOYB", "COTT", "SORG", "PIGE", "SUGC"]
BBOX = (68.0, 6.0, 97.5, 37.5)
OUT = "kharif_inputs"
os.makedirs(OUT, exist_ok=True)
get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (research data download)"}), timeout=600)

for w in ["ir", "rf"]:
    u = CAL.format(c="ri1", w=w)
    with get(u) as r, open(f"{OUT}/{os.path.basename(u)}", "wb") as f:
        f.write(r.read())
print("rice calendars downloaded", flush=True)

if not os.path.exists("spam_harv.zip"):
    files = json.load(get(f"{DATAVERSE}/api/datasets/:persistentId/?persistentId={DOI}"))["data"]["latestVersion"]["files"]
    pick = [f["dataFile"] for f in files if re.search(r"harv", f["dataFile"]["filename"], re.I) and re.search(r"tif", f["dataFile"]["filename"], re.I)][0]
    print(f"downloading {pick['filename']} ({pick.get('filesize', 0) // 2**20} MB) ...", flush=True)
    with get(f"{DATAVERSE}/api/access/datafile/{pick['id']}") as r, open("spam_harv.zip.part", "wb") as f:
        while (b := r.read(2**22)):
            f.write(b)
    os.replace("spam_harv.zip.part", "spam_harv.zip")
z = zipfile.ZipFile("spam_harv.zip")
want = [n for n in z.namelist() if re.search(r"_H_(%s)_(A|I|R)\.tif$" % "|".join(CROPS), n, re.I)]
print(f"using {len(want)} rasters", flush=True)
cols, lon, lat = {}, None, None
for n in sorted(want):
    with rasterio.open(io.BytesIO(z.read(n))) as src:
        win = from_bounds(*BBOX, transform=src.transform)
        a = src.read(1, window=win).astype("float32"); a[a < 0] = 0
        if lon is None:
            t = src.window_transform(win)
            lon = t.c + (np.arange(a.shape[1]) + 0.5) * t.a; lat = t.f + (np.arange(a.shape[0]) + 0.5) * t.e
        k = re.search(r"_H_(\w+)_(\w)\.tif$", n, re.I)
        cols[f"{k.group(1).lower()}_{k.group(2).lower()}"] = a
LON, LAT = np.meshgrid(lon, lat)
m = sum(v for k, v in cols.items() if k.endswith("_a")) > 0
keys = sorted(cols)
with open(f"{OUT}/spam_india_kharif_harv_ha.csv", "w") as f:
    f.write("lon,lat," + ",".join(keys) + "\n")
    for i, j in zip(*np.where(m)):
        f.write(f"{LON[i, j]:.5f},{LAT[i, j]:.5f}," + ",".join(f"{cols[k][i, j]:.1f}" for k in keys) + "\n")
with zipfile.ZipFile("kharif_inputs.zip", "w", zipfile.ZIP_DEFLATED) as zz:
    for fn in sorted(os.listdir(OUT)):
        zz.write(f"{OUT}/{fn}", fn)
print(f"done: kharif_inputs.zip, {m.sum()} pixels; columns {keys}", flush=True)
