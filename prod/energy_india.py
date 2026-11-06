"""PV specific yield (kWh per kWp per year) per grid cell, layout and GCR, with pvlib.

Same weather and sky model as the crop runs: daily NEX-GDDP rsds -> hourly GHI by
clear-sky scaling, Erbs DNI/DHI split (pv_shading.hourly_from_daily). Module plane
irradiance, front and rear, from pvlib's 2D infinite-sheds model (row-to-row shading
and ground view at each GCR). Reference module: bifacial glass-glass n-type (TOPCon),
efficiency 22.0%, bifaciality 0.80, power temperature coefficient -0.30 %/K, Faiman
cell temperature. System losses 14% (PVWatts default) and inverter efficiency 96%.

Layout geometry follows pv_shading.make_config:
  south_fixed  tilt 25 deg, azimuth 180, 2 m slant width, lower edge 3 m
  ew_fixed     ridge, two faces tilt 10 deg, azimuth 90 and 270, lower edge 3 m
  vertical     tilt 90 deg, faces east/west, 2 m high, lower edge 0.8 m
Years sampled every --step years from each climate model (default 5 -> 4 years x 5
models = 20 model-years per period), which keeps the run to minutes.
Output: energy_<period>.csv  cell, config, gcr, yield_kwh_kwp, poa_front, rear_gain
Usage (on the VM):
  python energy_india.py --cells /data/cells --grid grid_india_025.csv --period historical --out /data/out/summary
"""
import argparse
import os
from multiprocessing import Pool

import numpy as np
import pandas as pd
import pvlib
from pvlib.bifacial import infinite_sheds

import pv_shading as ps

MODELS = ["GFDL-ESM4", "IPSL-CM6A-LR", "MPI-ESM1-2-HR", "MRI-ESM2-0", "UKESM1-0-LL"]
VARS = ["srad_MJ", "tmax_C", "tmin_C", "rain_mm", "dewp_C", "wind_ms"]
GCRS = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
ETA = 0.22             # module efficiency (STC), for capacity density
BIFI = 0.80
GAMMA = -0.0030
LOSS = 0.14
INV = 0.96
ALBEDO = 0.20          # cropland, between bare soil and green canopy
# (tilt, [azimuths], module width m, centre height m)
LAYOUT = {"south_fixed": (25.0, [180.0], 2.0, 3.0 + np.sin(np.radians(25.0))),
          "ew_fixed": (10.0, [90.0, 270.0], 2.0, 3.0 + np.sin(np.radians(10.0))),
          "vertical": (90.0, [90.0], 2.0, 1.8)}
_G = {}


def hourly_temp(h, tmax, tmin):
    """Hourly air temperature: cosine between daily minimum (06 h) and maximum (15 h)."""
    hr = h.index.tz_localize(None).hour.values + 0.5
    tx = pd.Series(tmax, index=_G["dates"]).reindex(h.day.values).values
    tn = pd.Series(tmin, index=_G["dates"]).reindex(h.day.values).values
    w = np.where((hr >= 6) & (hr <= 15), 0.5 - 0.5 * np.cos(np.pi * (hr - 6) / 9),
                 0.5 + 0.5 * np.cos(np.pi * ((hr - 15) % 24) / 15))
    return tn + w * (tx - tn)


def cell_energy(args):
    i, lat, lon, cid = args
    res = {}
    for model, (data, dates, keep) in _G["clim"].items():
        _G["dates"] = dates[keep]
        d = pd.DataFrame(np.asarray(data[i])[keep], columns=VARS)
        if _G.get("k") is not None:          # radiation bias factors per calendar month (radiation_ref.py)
            d["srad_MJ"] = d.srad_MJ.values * _G["k"].get(cid, np.ones(12))[dates[keep].month.values - 1]
        h = ps.hourly_from_daily(lat, lon, pd.Series(dates[keep]), d.srad_MJ)
        h = h[h.day.isin(set(dates[keep]))]
        t_air = hourly_temp(h, d.tmax_C.values, d.tmin_C.values)
        wind = pd.Series(d.wind_ms.values, index=dates[keep]).reindex(h.day.values).values
        for cfg, (tilt, azs, width, height) in LAYOUT.items():
            for gcr in GCRS:
                pdc = front = rear = 0.0
                for az in azs:
                    irr = infinite_sheds.get_irradiance(tilt, az, h.zen, h.az, gcr, height, width / gcr,
                                                        h.ghi, h.dhi, h.dni, ALBEDO, bifaciality=BIFI)
                    poa = irr["poa_global"].fillna(0).values
                    tc = pvlib.temperature.faiman(irr["poa_front"].fillna(0).values, t_air, wind)
                    pdc += np.sum(pvlib.pvsystem.pvwatts_dc(poa, tc, 1.0, GAMMA)) / len(azs)   # kWh per kWp
                    front += irr["poa_front"].fillna(0).sum() / 1000.0 / len(azs)
                    rear += irr["poa_back"].fillna(0).sum() / 1000.0 / len(azs)
                k = (cfg, gcr)
                acc = res.setdefault(k, [0.0, 0.0, 0.0, 0])
                acc[0] += pdc; acc[1] += front; acc[2] += rear; acc[3] += keep.sum() / 365.25
    rows = []
    for (cfg, gcr), (pdc, front, rear, ny) in res.items():
        rows.append((cid, cfg, gcr, pdc * (1 - LOSS) * INV / ny, front / ny,
                     BIFI * rear / front if front > 0 else np.nan))
    return rows


def init(cells_dir, period, step, factors=None):
    _G["k"] = None
    if factors:
        f = pd.read_csv(factors).sort_values(["cell", "month"])
        _G["k"] = {c: d.k.values for c, d in f.groupby("cell")}
    _G["clim"] = {}
    for m in MODELS:
        npy = os.path.join(cells_dir, f"cells_{m}_{period}.npy")
        meta = np.load(npy.replace(".npy", "_meta.npz"), allow_pickle=True)
        dates = pd.to_datetime(meta["dates"])
        years = sorted(set(dates.year))
        keep = np.isin(dates.year, years[::step])
        _G["clim"][m] = (np.load(npy, mmap_mode="r"), dates, keep)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", required=True)
    ap.add_argument("--grid", required=True)
    ap.add_argument("--period", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--step", type=int, default=5)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--limit", type=int, default=0, help="first N cells only (testing)")
    ap.add_argument("--srad-factors", default="", help="rad_factors.csv: scale daily radiation by k(cell, month)")
    ap.add_argument("--tag", default="", help="suffix of the output file, e.g. _rc")
    a = ap.parse_args()
    g = pd.read_csv(a.grid)
    if a.limit:
        g = g.head(a.limit)
    jobs = [(i, r.lat, r.lon, r.cell_id) for i, r in enumerate(g.itertuples())]
    with Pool(a.workers, initializer=init, initargs=(a.cells, a.period, a.step, a.srad_factors or None)) as p:
        rows = [r for rs in p.imap(cell_energy, jobs, chunksize=4) for r in rs]
    os.makedirs(a.out, exist_ok=True)
    out = os.path.join(a.out, f"energy_{a.period}{a.tag}.csv")
    pd.DataFrame(rows, columns=["cell", "config", "gcr", "yield_kwh_kwp", "poa_front_kwh_m2", "rear_gain"]) \
        .to_csv(out, index=False, float_format="%.4g")
    print("wrote", out, len(rows), "rows")
