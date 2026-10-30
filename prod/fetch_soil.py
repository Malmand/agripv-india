"""Fetch SoilGrids v2.0 profiles (6 standard depths) for every grid cell.

Writes soil/<cell_id>.json in the format read by dssat_inputs.soil_from_soilgrids.
The ISRIC REST API allows about 5 requests per minute, so 498 cells take about
100 minutes; the script sleeps 12.5 s between calls, retries, and skips cells
already fetched (safe to restart). Cells with no data (water, rock, urban, or
outside the SoilGrids mask) get a copy of the nearest valid cell, recorded in
the 'filled_from' field. Poggio et al. (2021), SOIL 7, 217-240.
"""
import argparse
import json
import os
import sys
import time
import urllib.request

import numpy as np
import pandas as pd

URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
PROPS = ["bdod", "cec", "clay", "sand", "silt", "soc", "phh2o"]
DEPTHS = ["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm"]
# REST values are scaled integers: bdod cg/cm3, cec mmol(c)/kg, clay/sand/silt g/kg, soc dg/kg, pH*10
KEY = {"bdod": ("bdod_kg_dm3", 100), "cec": ("cec_cmol_kg", 10), "clay": ("clay_pct", 10),
       "sand": ("sand_pct", 10), "silt": ("silt_pct", 10), "soc": ("soc_g_kg", 10), "phh2o": ("ph_h2o", 10)}


def query(lat, lon, tries=6):
    q = "&".join([f"lon={lon}", f"lat={lat}"] + [f"property={p}" for p in PROPS]
                 + [f"depth={d}" for d in DEPTHS] + ["value=mean"])
    for i in range(tries):
        try:
            req = urllib.request.Request(f"{URL}?{q}", headers={"accept": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except Exception as e:
            if i == tries - 1:
                raise
            time.sleep(30 * (i + 1))   # 429 or server busy: back off


def parse(js, lat, lon):
    out = {"source": "SoilGrids v2.0 REST API, mean values", "lat": lat, "lon": lon,
           "depths_cm": [[0, 5], [5, 15], [15, 30], [30, 60], [60, 100], [100, 200]]}
    for layer in js["properties"]["layers"]:
        name, div = KEY[layer["name"]]
        div = layer.get("unit_measure", {}).get("d_factor", div)
        vals = {d["label"]: d["values"]["mean"] for d in layer["depths"]}
        v = [vals.get(d) for d in DEPTHS]
        if any(x is None for x in v):
            return None
        out[name] = [round(x / div, 2) for x in v]
    return out if all(KEY[p][0] in out for p in PROPS) else None


def cog_profile(lat, lon):
    """Fallback when the REST service is down: sample the SoilGrids COG/VRT files."""
    import rasterio
    from pyproj import Transformer
    x, y = Transformer.from_crs("EPSG:4326", "ESRI:54052", always_xy=True).transform(lon, lat)
    out = {"source": "SoilGrids v2.0 VRT (files.isric.org), mean values", "lat": lat, "lon": lon,
           "depths_cm": [[0, 5], [5, 15], [15, 30], [30, 60], [60, 100], [100, 200]]}
    for p in PROPS:
        name, div = KEY[p]
        vals = []
        for d in DEPTHS:
            url = f"/vsicurl/https://files.isric.org/soilgrids/latest/data/{p}/{p}_{d}_mean.vrt"
            with rasterio.open(url) as src:
                v = float(next(src.sample([(x, y)]))[0])
                if v == src.nodata or v <= 0 and p != "soc":
                    return None
            vals.append(round(v / div, 2))
        out[name] = vals
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", required=True)
    ap.add_argument("--out", default="soil")
    ap.add_argument("--sleep", type=float, default=12.5)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    g = pd.read_csv(a.grid)
    empty = []
    for k, r in enumerate(g.itertuples()):
        p = os.path.join(a.out, f"{r.cell_id}.json")
        if os.path.exists(p) or os.path.exists(p + ".empty"):
            continue
        try:
            d = parse(query(r.lat, r.lon, tries=3), r.lat, r.lon)
        except Exception as e:
            print(f"{r.cell_id} REST failed ({e}); trying VRT files", flush=True)
            try:
                d = cog_profile(r.lat, r.lon)
            except Exception as e2:
                print(f"{r.cell_id} VRT failed: {e2}", flush=True)
                continue
        if d is None:
            open(p + ".empty", "w").close()
        else:
            json.dump(d, open(p, "w"))
        if k % 25 == 0:
            print(f"{k + 1}/{len(g)} cells", flush=True)
        time.sleep(a.sleep)
    # fill cells without data from the nearest valid cell
    ok = g[[os.path.exists(os.path.join(a.out, f"{c}.json")) for c in g.cell_id]]
    for r in g.itertuples():
        p = os.path.join(a.out, f"{r.cell_id}.json")
        if os.path.exists(p) or not os.path.exists(p + ".empty"):
            continue
        dist = np.hypot(ok.lat - r.lat, (ok.lon - r.lon) * np.cos(np.radians(r.lat)))
        src = ok.cell_id.iloc[int(np.argmin(dist.values))]
        d = json.load(open(os.path.join(a.out, f"{src}.json")))
        d.update(filled_from=src, lat=r.lat, lon=r.lon)
        json.dump(d, open(p, "w"))
        empty.append(r.cell_id)
    missing = [c for c in g.cell_id if not os.path.exists(os.path.join(a.out, f"{c}.json"))]
    print(f"done: {len(g) - len(missing)} cells with soil ({len(empty)} filled from neighbours), "
          f"{len(missing)} missing", flush=True)
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
