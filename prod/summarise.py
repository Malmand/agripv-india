"""Summarise task CSVs into relative yield (RY) tables and maximum feasible GCR.

RY (land-area basis, ratio of means as in the pilot):
    RY = mean_seasons(mean_strips(Y_apv)) * cult_frac / mean_seasons(Y_open)
Farmer chickpea is the area-weighted irrigated/rainfed mix (0.26/0.74,
Jodhpur DLD); RY of the mix is weighted by open-field production.
Max feasible GCR = largest GCR with ensemble-median RY >= threshold (0 if none).
"""
import argparse
import glob
import os

import numpy as np
import pandas as pd

CHICKPEA_IRR_SHARE = 0.26


def _one(f):
    return ry_table(pd.read_csv(f))


def load_ry(out_dir):
    """RY per task file (one cell x model), in parallel; keeps memory small."""
    from multiprocessing import Pool
    files = glob.glob(os.path.join(out_dir, "*_*", "*", "*.csv"))
    with Pool() as p:
        return pd.concat(p.map(_one, files, chunksize=20), ignore_index=True)


def ry_table(df):
    key = ["cell", "model", "period", "mgmt", "system"]
    op = (df[df.config == "open"].groupby(key).hwam.agg(open_mean="mean", open_sd="std").reset_index())
    apv = df[df.config != "open"]
    # mean over strips within a season, then mean over seasons
    s = apv.groupby(key + ["config", "gcr", "season"]).agg(y=("hwam", "mean"), cf=("cult_frac", "first"))
    s = s.reset_index().groupby(key + ["config", "gcr"]).agg(y=("y", "mean"), cf=("cf", "first")).reset_index()
    t = s.merge(op, on=key)
    t["ry"] = t.y * t.cf / t.open_mean
    t = t.rename(columns={"y": "apv_mean", "cf": "cult_frac"})
    # farmer chickpea mix
    cp = t[t.system.isin(["chickpea_irrigated", "chickpea_rainfed"]) & (t.mgmt == "farmer")]
    if len(cp):
        k2 = ["cell", "model", "period", "mgmt", "config", "gcr"]
        w = cp.assign(w=np.where(cp.system == "chickpea_irrigated", CHICKPEA_IRR_SHARE,
                                 1 - CHICKPEA_IRR_SHARE) * cp.open_mean)
        mix = w.groupby(k2).apply(lambda g: pd.Series({
            "ry": (g.w * g.ry).sum() / g.w.sum(), "open_mean": g.w.sum(), "apv_mean": np.nan,
            "cult_frac": g.cult_frac.iloc[0],
            "open_sd": np.nan}), include_groups=False).reset_index()
        mix["system"] = "chickpea_mix"
        t = pd.concat([t, mix], ignore_index=True)
    return t


def gcr_max(t, thr):
    k = ["cell", "period", "mgmt", "system", "config", "gcr"]
    e = t.groupby(k).agg(ry_med=("ry", "median"), ry_min=("ry", "min"),
                         n_ok=("ry", lambda x: int((x >= thr).sum())), n=("ry", "size")).reset_index()
    rows = []
    for g, d in e.groupby(k[:-1]):
        d = d.sort_values("gcr")
        ok = d[d.ry_med >= thr]
        gm = float(ok.gcr.max()) if len(ok) else 0.0
        agree = int(ok[ok.gcr == gm].n_ok.iloc[0]) if len(ok) else 0  # models with RY >= thr at gcr_max
        rows.append(dict(zip(k[:-1], g), gcr_max=gm, models_agree=agree, n_models=int(d.n.iloc[0]),
                         ry_at_0p5=float(d[d.gcr == d.gcr.max()].ry_med.iloc[0])))
    return e, pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="run output folder")
    ap.add_argument("--grid", required=True)
    ap.add_argument("--thr", type=float, default=0.8)
    a = ap.parse_args()
    t = load_ry(a.out)
    g = pd.read_csv(a.grid)[["cell_id", "lat", "lon"]].rename(columns={"cell_id": "cell"})
    t.merge(g, on="cell").to_csv(os.path.join(a.out, "ry_all.csv"), index=False)
    e, m = gcr_max(t, a.thr)
    e.merge(g, on="cell").to_csv(os.path.join(a.out, "ry_ensemble.csv"), index=False)
    m.merge(g, on="cell").to_csv(os.path.join(a.out, "gcr_max.csv"), index=False)
    print(m.groupby(["period", "mgmt", "system", "config"]).gcr_max.describe()[["count", "mean", "50%", "min", "max"]]
          .round(2).to_string())
