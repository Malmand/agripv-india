"""Convert NEX-GDDP-CMIP6 yearly NetCDF subsets into per-cell daily weather arrays.

For one model and scenario it writes cells_<model>_<scen>.npz with
  dates : real calendar dates (YYYY-MM-DD strings), first to last year
  data  : float32 [cell, day, var] with vars
          srad MJ/m2/d, tmax C, tmin C, rain mm/d, dewp C, wind2 m/s
  cell_id, lat, lon

Calendar handling: model years of 360 (UKESM), 365 (noleap) or 366 days are
mapped onto the real calendar by nearest-index resampling, so a 360-day year
gains 5 or 6 repeated days spread evenly through the year and a noleap year
repeats one day in leap years. Wind is converted from 10 m to 2 m with the
FAO-56 log profile (u2 = u10 * 4.87 / ln(67.8 * 10 - 5.42)). Dew point comes
from daily mean temperature and relative humidity (Magnus formula).
"""
import argparse
import glob
import os
import re

import numpy as np
import pandas as pd
import xarray as xr

VARS = ["rsds", "tasmax", "tasmin", "pr", "hurs", "sfcWind"]
U2_FACTOR = 4.87 / np.log(67.8 * 10 - 5.42)


def year_of(path):
    return int(re.search(r"_(\d{4})(?:_v\d+\.\d+)?\.nc$", path).group(1))


def resample_year(arr, year):
    """arr [ndays_model, ncell] -> [ndays_real, ncell] by nearest index."""
    n_real = 366 if pd.Timestamp(year, 12, 31).dayofyear == 366 else 365
    n = arr.shape[0]
    if n == n_real:
        return arr
    idx = np.minimum(np.floor((np.arange(n_real) + 0.5) * n / n_real).astype(int), n - 1)
    return arr[idx]


def magnus_dewpoint(t_c, rh):
    a, b = 17.625, 243.04
    rh = np.clip(rh, 1.0, 100.0)
    g = np.log(rh / 100.0) + a * t_c / (b + t_c)
    return b * g / (a - g)


def convert(data_dir, model, scen, years, grid_csv, out_dir, fmt="npz"):
    grid = pd.read_csv(grid_csv)
    lat_i = lon_i = None
    per_var = {}
    for v in VARS:
        files = sorted(glob.glob(os.path.join(data_dir, model, scen, v, "*.nc")))
        files = [f for f in files if year_of(f) in years]
        if len(files) != len(years):
            raise RuntimeError(f"{model} {scen} {v}: {len(files)} files for {len(years)} years")
        chunks = []
        for f in files:
            with xr.open_dataset(f, decode_times=False) as ds:
                if lat_i is None:
                    lats, lons = ds.lat.values, ds.lon.values
                    lat_i = np.array([np.abs(lats - la).argmin() for la in grid.lat])
                    lon_i = np.array([np.abs(lons - lo).argmin() for lo in grid.lon])
                    err = max(np.abs(lats[lat_i] - grid.lat).max(), np.abs(lons[lon_i] - grid.lon).max())
                    if err > 0.01:
                        raise RuntimeError(f"grid mismatch {err}")
                a = ds[v].values[:, lat_i, lon_i].astype("float32")  # [t, cell]
            chunks.append(resample_year(a, year_of(f)))
        per_var[v] = np.concatenate(chunks, axis=0)
    srad = per_var["rsds"] * 0.0864
    tmax = per_var["tasmax"] - 273.15
    tmin = per_var["tasmin"] - 273.15
    lo, hi = np.minimum(tmax, tmin), np.maximum(tmax, tmin)
    rain = np.maximum(per_var["pr"] * 86400.0, 0.0)
    dewp = magnus_dewpoint((lo + hi) / 2.0, per_var["hurs"])
    dewp = np.minimum(dewp, lo)
    wind2 = per_var["sfcWind"] * U2_FACTOR
    data = np.stack([srad, hi, lo, rain, dewp, wind2], axis=-1).transpose(1, 0, 2)
    dates = pd.date_range(f"{years[0]}-01-01", f"{years[-1]}-12-31", freq="D")
    if len(dates) != data.shape[1]:
        raise RuntimeError(f"date length {len(dates)} != {data.shape[1]}")
    os.makedirs(out_dir, exist_ok=True)
    if fmt == "npy":   # uncompressed, memory-mapped by the workers (India: ~0.5 GB per file)
        out = os.path.join(out_dir, f"cells_{model}_{scen}.npy")
        tmp = out + ".part.npy"
        np.save(tmp, np.ascontiguousarray(data.astype("float32")))
        np.savez(os.path.join(out_dir, f"cells_{model}_{scen}_meta.npz"), dates=dates.strftime("%Y-%m-%d").values,
                 cell_id=grid.cell_id.values)
        os.replace(tmp, out)
        return out, data.shape
    out = os.path.join(out_dir, f"cells_{model}_{scen}.npz")
    np.savez_compressed(out, data=data.astype("float32"), dates=dates.strftime("%Y-%m-%d").values,
                        cell_id=grid.cell_id.values, lat=grid.lat.values, lon=grid.lon.values)
    return out, data.shape


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--scen", required=True)
    ap.add_argument("--grid", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--format", default="npz", choices=["npz", "npy"])
    a = ap.parse_args()
    yrs = list(range(1995, 2015)) if a.scen == "historical" else list(range(2041, 2061))
    path, shape = convert(a.data, a.model, a.scen, yrs, a.grid, a.out, a.format)
    print("wrote", path, shape)
