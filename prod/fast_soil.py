"""Fast SoilGrids fetch for cells still missing, reading the SoilGrids v2.0 map files
(files.isric.org VRTs, same data as the REST API) directly and in parallel.

Each of the 42 layers (7 properties x 6 depths) is opened once and sampled at all
missing cell centres; results are written as soil/<cell_id>.json in the same format
as fetch_soil.py, with source "SoilGrids v2.0 VRT". Cells already present (from the
REST fetch running alongside) are skipped, so both can run at the same time.
"""
import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer

PROPS = {"bdod": ("bdod_kg_dm3", 100), "cec": ("cec_cmol_kg", 10), "clay": ("clay_pct", 10),
         "sand": ("sand_pct", 10), "silt": ("silt_pct", 10), "soc": ("soc_g_kg", 10), "phh2o": ("ph_h2o", 10)}
DEPTHS = ["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm"]
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "5")
os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "3")
os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")


def layer(job):
    p, d, xy = job
    url = f"/vsicurl/https://files.isric.org/soilgrids/latest/data/{p}/{p}_{d}_mean.vrt"
    with rasterio.open(url) as src:
        vals = np.array([v[0] for v in src.sample(xy)], dtype="float64")
        if src.nodata is not None:
            vals[vals == src.nodata] = np.nan
    return p, d, vals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", required=True)
    ap.add_argument("--out", default="soil")
    ap.add_argument("--threads", type=int, default=14)
    a = ap.parse_args()
    g = pd.read_csv(a.grid)
    have = [os.path.exists(os.path.join(a.out, f"{c}.json")) for c in g.cell_id]
    todo = g[[not h for h in have]]
    check = g[have].head(20)                     # cells already fetched by REST: cross-check
    todo = pd.concat([todo, check])
    print(f"{len(todo)} cells missing soil; sampling 42 layers with {a.threads} threads", flush=True)
    if todo.empty:
        return
    tr = Transformer.from_crs("EPSG:4326", "ESRI:54052", always_xy=True)
    xs, ys = tr.transform(todo.lon.values, todo.lat.values)
    xy = list(zip(xs, ys))
    res = {}
    with ThreadPoolExecutor(a.threads) as ex:
        for p, d, vals in ex.map(layer, [(p, d, xy) for p in PROPS for d in DEPTHS]):
            res[(p, d)] = vals
            print(f"  {p} {d} done", flush=True)
    n_ok = n_bad = 0
    diffs = []
    for i, r in enumerate(todo.itertuples()):
        path = os.path.join(a.out, f"{r.cell_id}.json")
        if os.path.exists(path):
            if r.cell_id in set(check.cell_id) and not np.isnan(res[("sand", "0-5cm")][i]):
                rest = json.load(open(path))
                diffs.append(abs(rest["sand_pct"][0] - res[("sand", "0-5cm")][i] / 10))
            continue
        out = {"source": "SoilGrids v2.0 VRT (files.isric.org), mean values", "lat": r.lat, "lon": r.lon,
               "depths_cm": [[0, 5], [5, 15], [15, 30], [30, 60], [60, 100], [100, 200]]}
        ok = True
        for p, (name, div) in PROPS.items():
            v = [res[(p, d)][i] for d in DEPTHS]
            if any(np.isnan(x) or (x <= 0 and p != "soc") for x in v):
                ok = False
                break
            out[name] = [round(x / div, 2) for x in v]
        if ok:
            tmp = path + ".part"
            json.dump(out, open(tmp, "w"))
            os.replace(tmp, path)
            n_ok += 1
        else:
            n_bad += 1   # left for the REST fetch / nearest-neighbour fill
    print(f"wrote {n_ok} cells; {n_bad} without data (left for the REST fetch to fill)", flush=True)
    if diffs:
        print(f"cross-check vs REST on {len(diffs)} cells: topsoil sand differs by {np.mean(diffs):.2f} points "
              f"on average (max {np.max(diffs):.2f})", flush=True)


if __name__ == "__main__":
    main()
