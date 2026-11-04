"""Summarise India task CSVs: relative yield (RY) per crop system and per crop, ensemble, max GCR.

RY (land-area basis, ratio of means, as in the Rajasthan run):
    RY = mean_seasons(mean_strips(Y_apv)) * cult_frac / mean_seasons(Y_open)
Crop-level RY combines irrigated and rainfed systems weighted by MapSPAM area share
times open-field yield (i.e. by production):  RY_crop = sum(w_s Y_apv,s) / sum(w_s Y_open,s).
Also reported: irrigation applied (mm per season) open vs APV, for water-saving analysis.
Max feasible GCR = largest GCR with ensemble-median RY >= threshold (0 if none).
"""
import argparse
import glob
import os
from multiprocessing import Pool

import numpy as np
import pandas as pd

import pv_shading as ps

GRID = None
KEY = ["cell", "model", "period", "mgmt", "crop", "water"]


_CF = {}


def fix_rows(df):
    """Repair two effects of sim_india.py writing task CSVs with float_format "%.1f" (fixed 4 Nov 2026):
    (1) GCR 0.05 (chickpea, groundnut) was written as 0.1. Within a task file the 0.05 rows of a
        (crop, water, config, strip, season) come before the 0.1 rows (GCRs run in ascending order),
        so where a key occurs twice at 0.1, the first occurrence is relabelled 0.05.
    (2) cult_frac was rounded to one decimal (vertical layout). It depends only on layout and GCR,
        so it is recomputed from the geometry."""
    apv = df.config != "open"
    leg = apv & df.crop.isin(["chickpea", "groundnut"]) & np.isclose(df.gcr, 0.1)
    if leg.any():
        k = ["cell", "model", "period", "mgmt", "crop", "water", "config", "strip", "season"]
        sub = df[leg]
        n = sub.groupby(k).cumcount()
        size = sub.groupby(k).season.transform("size")
        df.loc[n.index[(n == 0) & (size == 2)], "gcr"] = 0.05
    df["gcr"] = df.gcr.round(2)
    for (cfgname, g), idx in df[apv].groupby(["config", "gcr"]).groups.items():
        if (cfgname, g) not in _CF:
            _CF[(cfgname, g)] = ps.strip_geometry(ps.make_config(cfgname), g)["cult_frac"]
        df.loc[idx, "cult_frac"] = _CF[(cfgname, g)]
    return df


def ry_file(f):
    df = fix_rows(pd.read_csv(f))
    op = df[df.config == "open"].groupby(KEY).agg(open_mean=("hwam", "mean"), open_sd=("hwam", "std"),
                                                  open_irri=("irri", "mean")).reset_index()
    apv = df[df.config != "open"]
    if apv.empty:
        return op
    s = apv.groupby(KEY + ["config", "gcr", "season"]).agg(y=("hwam", "mean"), irri=("irri", "mean"),
                                                         cf=("cult_frac", "first"))
    s = s.reset_index().groupby(KEY + ["config", "gcr"]).agg(apv_mean=("y", "mean"), apv_irri=("irri", "mean"),
                                                            cult_frac=("cf", "first")).reset_index()
    t = s.merge(op, on=KEY)
    t["ry"] = t.apv_mean * t.cult_frac / t.open_mean.where(t.open_mean > 0)
    return t


def add_crop_level(t, grid):
    crops = ["wheat", "chickpea", "groundnut", "pearl_millet"]
    irr = grid.melt(id_vars="cell_id", value_vars=[f"{c}_irr_share" for c in crops],
                    var_name="crop", value_name="irr")
    irr["crop"] = irr.crop.str.replace("_irr_share", "")
    t = t.merge(irr.rename(columns={"cell_id": "cell"}), on=["cell", "crop"], how="left")
    t["irr"] = t.irr.fillna(0.0)
    t["share"] = np.where(t.water == "ir", t.irr, 1 - t.irr)
    # renormalise over the simulated variants of each crop in each cell
    t["share"] = t.share / t.groupby(["cell", "model", "period", "mgmt", "crop", "config", "gcr"]).share.transform("sum")
    t["w_apv"] = t.share * t.apv_mean * t.cult_frac
    t["w_open"] = t.share * t.open_mean
    c = t.groupby(["cell", "model", "period", "mgmt", "crop", "config", "gcr"]).agg(
        apv=("w_apv", "sum"), open=("w_open", "sum")).reset_index()
    c["ry"] = c.apv / c.open.where(c.open > 0)
    c["water"] = "all"
    return c


def gcr_max(e, thr, keys):
    rows = []
    for g, d in e.groupby(keys):
        ok = d[d.ry_med >= thr]
        gm = float(ok.gcr.max()) if len(ok) else 0.0
        rows.append(dict(zip(keys, g), gcr_max=gm,
                         models_agree=int(ok[ok.gcr == gm].n_ok.iloc[0]) if len(ok) else 0))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--grid", required=True)
    ap.add_argument("--stage", default="*", help="stage folder glob, e.g. historical_recommended")
    ap.add_argument("--thr", type=float, nargs="+", default=[0.8, 0.66, 0.9])
    a = ap.parse_args()
    grid = pd.read_csv(a.grid)
    files = glob.glob(os.path.join(a.out, a.stage, "*", "*.csv"))
    with Pool() as p:
        t = pd.concat(p.map(ry_file, files, chunksize=20), ignore_index=True)
    tag = a.stage.replace("*", "all")
    sdir = os.path.join(a.out, "summary")
    os.makedirs(sdir, exist_ok=True)
    t.to_csv(os.path.join(sdir, f"ry_system_{tag}.csv.gz"), index=False, float_format="%.4g")
    if "gcr" in t:
        t = t.dropna(subset=["gcr"])
        c = add_crop_level(t, grid)
        c.to_csv(os.path.join(sdir, f"ry_crop_{tag}.csv.gz"), index=False, float_format="%.4g")
        k = ["cell", "period", "mgmt", "crop", "config", "gcr"]
        for thr in a.thr:
            e = c.groupby(k).agg(ry_med=("ry", "median"), ry_min=("ry", "min"), ry_max=("ry", "max"),
                                 n_ok=("ry", lambda x: int((x >= thr).sum())), n=("ry", "size")).reset_index()
            m = gcr_max(e, thr, k[:-1])
            m.to_csv(os.path.join(sdir, f"gcr_max_thr{int(thr * 100)}_{tag}.csv"), index=False)
            if thr == a.thr[0]:
                e.to_csv(os.path.join(sdir, f"ry_ensemble_{tag}.csv.gz"), index=False, float_format="%.4g")
                print(m.groupby(["period", "mgmt", "crop", "config"]).gcr_max.describe()[["count", "mean", "50%"]]
                      .round(2).to_string())
    print("wrote", sdir)
