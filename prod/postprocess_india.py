"""Yield-constrained APV potential for India from the summarised crop runs.

For each cell, climate model, crop and layout, the RY-GCR curve (RY = 1 at GCR 0) is
interpolated linearly and GCR_max(thr) is the first GCR where RY falls below thr, so
every GCR up to GCR_max meets the threshold. Potential is computed per climate model;
India and state totals are reported as the median and the min-max range over models.

Land:   eligible area = MapSPAM harvested area of the crop x share of the cell with
        terrain slope <= S % (S = 5 main; none and 10 as sensitivity cases).
Power:  capacity (MWp) = eligible ha x GCR_max x module efficiency x 10
        (GCR = module area / ground area, 1 kW per m2 at STC).
Energy: capacity x specific yield (kWh/kWp, energy_india.py) interpolated at GCR_max.
Crops combined without double counting land: wheat and chickpea (rabi) and pearl
millet and groundnut (kharif) can share a field across the year, so the overlap
min(A_rabi, A_kharif) is treated as double cropped and must satisfy both seasons
(lower of the two area-weighted GCR_max); the rest of each season's area uses its own.

Usage: python postprocess_india.py --summary <dir> --stage historical_current --grid grid.csv
       --slope slope_india.csv [--energy energy_historical.csv] --outdir results/potential
"""
import argparse
import os

import numpy as np
import pandas as pd

ETA = 0.22
THRS = [0.66, 0.8, 0.9]
SLOPE_RULES = {"none": None, "le5": "frac_slope_le5", "le10": "frac_slope_le10"}
RABI, KHARIF = ["wheat", "chickpea"], ["pearl_millet", "groundnut"]


def gcr_at_threshold(gcr, ry, thr):
    """First crossing of thr on the RY-GCR curve, starting from (0, 1)."""
    g = np.r_[0.0, gcr]
    r = np.r_[1.0, ry]
    below = np.nonzero(r < thr)[0]
    if len(below) == 0:
        return g[-1]
    k = below[0]
    if np.isnan(r[k]) or r[k - 1] == r[k]:
        return g[k - 1]
    return g[k - 1] + (r[k - 1] - thr) * (g[k] - g[k - 1]) / (r[k - 1] - r[k])


def gcr_table(ry):
    rows = []
    for key, d in ry.groupby(["cell", "model", "crop", "config"]):
        d = d.sort_values("gcr")
        gtop = d.gcr.max()
        for thr in THRS:
            gm = gcr_at_threshold(d.gcr.values, d.ry.values, thr)
            rows.append(key + (thr, gm, bool(gm >= gtop - 1e-9)))
    return pd.DataFrame(rows, columns=["cell", "model", "crop", "config", "thr", "gcr_max", "at_cap"])


def energy_at(en, g):
    """Specific yield at each row's GCR_max, interpolated per cell and layout."""
    if en is None:
        return pd.Series(np.nan, index=g.index)
    out = pd.Series(np.nan, index=g.index)
    lut = {k: (d.gcr.values, d.yield_kwh_kwp.values) for k, d in en.sort_values("gcr").groupby(["cell", "config"])}
    for (c, cfg), idx in g.groupby(["cell", "config"]).groups.items():
        if (c, cfg) in lut:
            x, y = lut[(c, cfg)]
            out.loc[idx] = np.interp(g.loc[idx, "gcr_max"].clip(lower=x[0]), x, y)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", required=True)
    ap.add_argument("--stage", required=True)
    ap.add_argument("--grid", required=True)
    ap.add_argument("--slope", required=True)
    ap.add_argument("--energy")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--robust-with", help="second stage (e.g. historical_recommended): GCR_max = min of both")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    grid = pd.read_csv(a.grid)
    slope = pd.read_csv(a.slope).set_index("cell_id")
    ry = pd.read_csv(os.path.join(a.summary, f"ry_crop_{a.stage}.csv.gz"))
    en = pd.read_csv(a.energy) if a.energy and os.path.exists(a.energy) else None

    g = gcr_table(ry)
    if a.robust_with:
        g2 = gcr_table(pd.read_csv(os.path.join(a.summary, f"ry_crop_{a.robust_with}.csv.gz")))
        k = ["cell", "model", "crop", "config", "thr"]
        g = g.merge(g2[k + ["gcr_max", "at_cap"]].rename(columns={"gcr_max": "g2", "at_cap": "c2"}), on=k, how="left")
        g["gcr_max"] = np.fmin(g.gcr_max, g.g2)
        g["at_cap"] = g.at_cap & g.c2.fillna(True).astype(bool)
        g = g.drop(columns=["g2", "c2"])
        a.stage = f"{a.stage}_robust"
    area = grid.melt(id_vars=["cell_id", "state"], value_vars=[f"{c}_ha" for c in RABI + KHARIF],
                     var_name="crop", value_name="area_ha")
    area["crop"] = area.crop.str.replace("_ha", "")
    g = g.merge(area.rename(columns={"cell_id": "cell"}), on=["cell", "crop"], how="left")
    g["yield_kwh_kwp"] = energy_at(en, g)
    long = []
    for rule, col in SLOPE_RULES.items():
        f = 1.0 if col is None else g.cell.map(slope[col]).fillna(0.0)
        x = g.copy()
        x["slope_rule"] = rule
        x["elig_ha"] = x.area_ha * f
        long.append(x)
    g = pd.concat(long, ignore_index=True)
    g["cap_mwp"] = g.elig_ha * g.gcr_max * ETA * 10
    g["energy_gwh"] = g.cap_mwp * g.yield_kwh_kwp / 1000
    g.to_csv(os.path.join(a.outdir, f"cell_crop_{a.stage}.csv.gz"), index=False, float_format="%.5g")

    # crops combined, double-cropped overlap counted once
    k = ["cell", "state", "model", "config", "thr", "slope_rule"]
    rows = []
    for key, d in g.groupby(k):
        s = {}
        for name, crops in (("rabi", RABI), ("kharif", KHARIF)):
            e = d[d.crop.isin(crops) & (d.elig_ha > 0)]
            A = e.elig_ha.sum()
            s[name] = (A, (e.gcr_max * e.elig_ha).sum() / A if A > 0 else 0.0,
                       (e.yield_kwh_kwp * e.elig_ha).sum() / A if A > 0 else np.nan)
        (Ar, gr, yr), (Ak, gk, yk) = s["rabi"], s["kharif"]
        ov = min(Ar, Ak)
        parts = [(ov, min(gr, gk)), (Ar - ov, gr), (Ak - ov, gk)]
        land = Ar + Ak - ov
        cap = sum(A_ * g_ for A_, g_ in parts) * ETA * 10
        ysp = np.nanmean([yr, yk]) if land > 0 else np.nan
        rows.append(key + (land, cap, cap * ysp / 1000 if land > 0 else 0.0))
    comb = pd.DataFrame(rows, columns=k + ["land_ha", "cap_mwp", "energy_gwh"])
    comb.to_csv(os.path.join(a.outdir, f"cell_combined_{a.stage}.csv.gz"), index=False, float_format="%.5g")

    # India and state totals: per model, then median and range over models
    def totals(df, by, val):
        t = df.groupby(by + ["model"])[val].sum().reset_index()
        return t.groupby(by)[val].agg(["median", "min", "max"]).add_prefix(val + "_").reset_index()

    by = ["crop", "config", "thr", "slope_rule"]
    ti = totals(g, by, "cap_mwp").merge(totals(g, by, "energy_gwh"), on=by) \
        .merge(totals(g, by, "elig_ha"), on=by)
    ti["cap_gw_median"] = ti.cap_mwp_median / 1000
    ti.to_csv(os.path.join(a.outdir, f"india_by_crop_{a.stage}.csv"), index=False, float_format="%.5g")
    by = ["config", "thr", "slope_rule"]
    tc = totals(comb, by, "cap_mwp").merge(totals(comb, by, "energy_gwh"), on=by).merge(totals(comb, by, "land_ha"), on=by)
    tc.to_csv(os.path.join(a.outdir, f"india_combined_{a.stage}.csv"), index=False, float_format="%.5g")
    ts = totals(comb, ["state"] + by, "cap_mwp").merge(totals(comb, ["state"] + by, "energy_gwh"), on=["state"] + by)
    ts.to_csv(os.path.join(a.outdir, f"state_combined_{a.stage}.csv"), index=False, float_format="%.5g")
    # map table: median GCR_max over models
    mp = g[g.slope_rule == "le5"].groupby(["cell", "crop", "config", "thr"]).agg(
        gcr_med=("gcr_max", "median"), gcr_min=("gcr_max", "min"), gcr_max=("gcr_max", "max"),
        elig_ha=("elig_ha", "first")).reset_index()
    mp.to_csv(os.path.join(a.outdir, f"map_gcr_{a.stage}.csv.gz"), index=False, float_format="%.4g")
    show = tc[(tc.slope_rule == "le5")].copy()
    show["GW"] = (show.cap_mwp_median / 1000).round(1)
    show["GW range"] = (show.cap_mwp_min / 1000).round(1).astype(str) + "-" + (show.cap_mwp_max / 1000).round(1).astype(str)
    show["Mha"] = (show.land_ha_median / 1e6).round(2)
    print(show[["config", "thr", "Mha", "GW", "GW range"]].to_string(index=False))
    print("wrote", a.outdir)


if __name__ == "__main__":
    main()
