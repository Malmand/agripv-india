"""Radiation bias factors for the NEX-GDDP climate data (review comment M5).

NEX-GDDP-CMIP6 shortwave radiation is bias-corrected to a reanalysis-based reference that does not carry
the aerosol and winter-fog dimming of the Indo-Gangetic plain, so simulated irradiance there is too high.
This script compares, per 0.25 deg cell and calendar month, the 1995-2014 mean of the five GCMs with the
NASA POWER all-sky surface shortwave climatology (CERES-based satellite product, 2001-2020) and writes the
ratio k = POWER / NEX. energy_india.py --srad-factors and sim_india.py (env AGRIPV_SRAD_FACTORS) multiply the
daily radiation by k of the cell and month; future periods use the same factors (delta approach).

Output: <out>/rad_factors.csv  cell, month, nex_kwh, ref_kwh, k   (daily means, kWh m-2 d-1)
        <out>/rad_ref_power.csv  the POWER climatology per query point (cache, reused on rerun)
Usage (VM): python radiation_ref.py --cells /data/cells --grid grid_india_025.csv --out /data/out/summary
"""
import argparse
import json
import os
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

MODELS = ["GFDL-ESM4", "IPSL-CM6A-LR", "MPI-ESM1-2-HR", "MRI-ESM2-0", "UKESM1-0-LL"]
URL = ("https://power.larc.nasa.gov/api/temporal/climatology/point?parameters=ALLSKY_SFC_SW_DWN"
       "&community=RE&longitude={lon:.3f}&latitude={lat:.3f}&format=JSON")
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
K_MIN, K_MAX = 0.5, 1.3


def power_point(pt):
    lat, lon = pt
    for attempt in range(6):
        try:
            with urllib.request.urlopen(URL.format(lat=lat, lon=lon), timeout=60) as r:
                v = json.load(r)["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]
            return [lat, lon] + [float(v[m]) for m in MONTHS]
        except Exception as e:  # noqa: BLE001  (network: retry with back-off)
            err = e
            time.sleep((20 if "429" in str(e) else 5) * (attempt + 1))   # rate limit: wait longer
    print("POWER failed", lat, lon, err)
    return [lat, lon] + [np.nan] * 12


def nex_monthly(cells_dir, n):
    """1995-2014 mean daily radiation per cell and month over the five GCMs, kWh m-2 d-1."""
    acc = np.zeros((n, 12)); cnt = 0
    for m in MODELS:
        npy = os.path.join(cells_dir, f"cells_{m}_historical.npy")
        meta = np.load(npy.replace(".npy", "_meta.npz"), allow_pickle=True)
        mon = pd.to_datetime(meta["dates"]).month.values
        data = np.load(npy, mmap_mode="r")
        srad = np.asarray(data[:, :, 0], dtype="float64") / 3.6          # MJ -> kWh
        for k in range(12):
            acc[:, k] += srad[:, mon == k + 1].mean(axis=1)
        cnt += 1
    return acc / cnt


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", required=True)
    ap.add_argument("--grid", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    g = pd.read_csv(a.grid)
    # query POWER on a 0.5 deg lattice (its solar data are at 1 deg; 0.5 deg keeps the call count low)
    g["qlat"] = (np.round(g.lat * 2) / 2).round(2)
    g["qlon"] = (np.round(g.lon * 2) / 2).round(2)
    cache = os.path.join(a.out, "rad_ref_power.csv")
    cols = ["qlat", "qlon"] + MONTHS
    have = pd.read_csv(cache) if os.path.exists(cache) else pd.DataFrame(columns=cols)
    have = have.dropna()
    pts = sorted(set(zip(g.qlat, g.qlon)) - set(zip(have.qlat, have.qlon)))
    print(f"POWER: {len(pts)} points to fetch ({len(have)} cached)")
    with ThreadPoolExecutor(a.workers) as ex:
        new = list(ex.map(power_point, pts))
    ref = pd.concat([have, pd.DataFrame(new, columns=cols)], ignore_index=True).dropna()
    os.makedirs(a.out, exist_ok=True)
    ref.to_csv(cache, index=False, float_format="%.3f")
    nex = nex_monthly(a.cells, len(g))
    r = g[["cell_id", "qlat", "qlon"]].merge(ref, on=["qlat", "qlon"], how="left")
    rows = []
    for i, row in enumerate(r.itertuples(index=False)):
        for k, m in enumerate(MONTHS):
            refv = getattr(row, m)
            kk = np.clip(refv / nex[i, k], K_MIN, K_MAX) if np.isfinite(refv) and nex[i, k] > 0 else 1.0
            rows.append((row.cell_id, k + 1, nex[i, k], refv, kk))
    out = pd.DataFrame(rows, columns=["cell", "month", "nex_kwh", "ref_kwh", "k"])
    out.to_csv(os.path.join(a.out, "rad_factors.csv"), index=False, float_format="%.4g")
    ann = out.groupby("cell")[["nex_kwh", "ref_kwh"]].mean()
    print("wrote rad_factors.csv; annual k (ref/NEX) percentiles 5/50/95:",
          np.nanpercentile(ann.ref_kwh / ann.nex_kwh, [5, 50, 95]).round(3))
