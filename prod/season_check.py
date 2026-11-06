"""Season-by-season yield rule (review comment M9).

The main analysis applies the threshold to the 20-year mean relative yield (ratio of mean yields). Regulations
judge each season. From the raw task files of a stage this script computes, per cell, GCM, crop, layout and
GCR, the relative yield of every season (crop level: irrigated and rainfed variants weighted as in
summarise_india.add_crop_level) and the fraction of seasons with RY >= --thr.

Outputs in <out>/summary:
  ry_crop_<stage>_season.csv.gz   same columns as ry_crop_<stage>.csv.gz, but "ry" holds the fraction of seasons
                                  with RY >= thr. postprocess_india.py on this file at threshold 0.80 gives the
                                  GCR_max at which at least 80% of seasons (16 of 20) keep RY >= thr.
  season_stats_<stage>.csv.gz     cell, model, crop, config, gcr, ry_mean, ry_p10, frac_ok
Usage (VM): python season_check.py --out /data/out --grid grid_india_025.csv --stage historical_current
"""
import argparse
import glob
import os
from multiprocessing import Pool

import numpy as np
import pandas as pd

import summarise_india as S

KEY = ["cell", "model", "period", "mgmt", "crop", "water"]
_G = {}


def init(grid, thr):
    crops = ["wheat", "chickpea", "groundnut", "pearl_millet"]
    g = pd.read_csv(grid)
    irr = g.melt(id_vars="cell_id", value_vars=[f"{c}_irr_share" for c in crops], var_name="crop", value_name="irr")
    irr["crop"] = irr.crop.str.replace("_irr_share", "")
    _G["irr"] = irr.rename(columns={"cell_id": "cell"})
    _G["thr"] = thr


def per_file(f):
    df = S.fix_rows(pd.read_csv(f))
    op = df[df.config == "open"].groupby(KEY + ["season"]).hwam.mean().rename("open").reset_index()
    apv = df[df.config != "open"]
    if apv.empty or op.empty:
        return None
    s = apv.groupby(KEY + ["config", "gcr", "season"]).agg(y=("hwam", "mean"), cf=("cult_frac", "first")).reset_index()
    s = s.merge(op, on=KEY + ["season"])
    s = s.merge(_G["irr"], on=["cell", "crop"], how="left")
    s["irr"] = s.irr.fillna(0.0)
    s["share"] = np.where(s.water == "ir", s.irr, 1 - s.irr)
    k7 = ["cell", "model", "period", "mgmt", "crop", "config", "gcr", "season"]
    s["share"] = s.share / s.groupby(k7).share.transform("sum")
    s["wa"] = s.share * s.y * s.cf
    s["wo"] = s.share * s.open
    c = s.groupby(k7).agg(apv=("wa", "sum"), open=("wo", "sum")).reset_index()
    c["ry"] = c.apv / c.open.where(c.open > 0)
    k6 = k7[:-1]
    out = c.groupby(k6).agg(apv_m=("apv", "mean"), open_m=("open", "mean"),
                            ry_p10=("ry", lambda x: np.nanpercentile(x, 10) if x.notna().any() else np.nan),
                            frac_ok=("ry", lambda x: float((x.dropna() >= _G["thr"]).mean()) if x.notna().any() else np.nan))
    out["ry_mean"] = out.apv_m / out.open_m.where(out.open_m > 0)
    return out.reset_index()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--grid", required=True)
    ap.add_argument("--stage", required=True)
    ap.add_argument("--thr", type=float, default=0.8)
    a = ap.parse_args()
    files = glob.glob(os.path.join(a.out, a.stage, "*", "*.csv"))
    with Pool(initializer=init, initargs=(a.grid, a.thr)) as p:
        t = pd.concat([x for x in p.imap_unordered(per_file, files, chunksize=20) if x is not None], ignore_index=True)
    sdir = os.path.join(a.out, "summary")
    os.makedirs(sdir, exist_ok=True)
    t[["cell", "model", "crop", "config", "gcr", "ry_mean", "ry_p10", "frac_ok"]].to_csv(
        os.path.join(sdir, f"season_stats_{a.stage}.csv.gz"), index=False, float_format="%.4g")
    r = t.rename(columns={"apv_m": "apv", "open_m": "open"}).assign(ry=t.frac_ok, water="all")
    r[["cell", "model", "period", "mgmt", "crop", "config", "gcr", "apv", "open", "ry", "water"]].to_csv(
        os.path.join(sdir, f"ry_crop_{a.stage}_season.csv.gz"), index=False, float_format="%.4g")
    print("wrote season files for", a.stage, len(t), "rows; median fraction of seasons with RY >=",
          a.thr, "at GCR 0.3 (ew):", t[(t.config == "ew_fixed") & (t.gcr.round(2) == 0.3)].frac_ok.median())
