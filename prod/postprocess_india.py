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

DIN cap (main case): DIN SPEC 91434 limits the land lost to the structure to 15%. The vertical layout
keeps a 0.5 m uncultivated strip under each row, which exceeds 15% above GCR 0.6, so vertical GCR_max is
capped at --din-cap (default 0.6; 0 switches the cap off). cell_crop keeps the uncapped values (gcr_raw,
yield_raw) and the flag din_capped; the uncapped totals are written as the sensitivity case
india_combined_<stage>_nodin.csv (also india_by_crop_* and state_combined_*).

Usage: python postprocess_india.py --summary <dir> --stage historical_current --grid grid.csv
       --slope slope_india.csv [--energy energy_historical.csv] --outdir results/potential [--din-cap 0.6]
Rebuild without the crop runs (e.g. to change the DIN cap): --from-cell-crop results/potential/cell_crop_<stage>.csv.gz
       (uses gcr_raw/yield_raw if present; without --energy the specific yield at the capped GCR is interpolated
       from the (GCR_max, kWh/kWp) pairs of the same cell and layout in that table, flat beyond their range)
"""
import argparse
import os

import numpy as np
import pandas as pd

ETA = 0.22
THRS = [0.66, 0.8, 0.9]
DIN_LAYOUT = "vertical"
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


def energy_from_pairs(c, rows):
    """Specific yield at rows.gcr_max from the (gcr_raw, yield_raw) pairs of the same cell and layout in c."""
    out = pd.Series(np.nan, index=rows.index)
    pairs = c[c.yield_raw.notna()].drop_duplicates(["cell", "config", "gcr_raw"])
    lut = {k: (d.gcr_raw.values, d.yield_raw.values) for k, d in pairs.sort_values("gcr_raw").groupby(["cell", "config"])}
    for (cl, cfg), idx in rows.groupby(["cell", "config"]).groups.items():
        if (cl, cfg) in lut:
            x, y = lut[(cl, cfg)]
            out.loc[idx] = np.interp(rows.loc[idx, "gcr_max"], x, y)
    return out


def apply_din_cap(g, cap, en, from_table):
    """Cap vertical GCR_max at cap; recompute specific yield for the capped rows."""
    g["gcr_raw"], g["yield_raw"] = g.gcr_max, g.yield_kwh_kwp
    g["din_capped"] = (g.config == DIN_LAYOUT) & (g.gcr_max > cap + 1e-9) if cap > 0 else False
    if cap <= 0 or not g.din_capped.any():
        return g
    m = g.din_capped
    g.loc[m, "gcr_max"] = cap
    if en is not None:
        g.loc[m, "yield_kwh_kwp"] = energy_at(en, g.loc[m])
    elif from_table and g.yield_raw.notna().any():
        g.loc[m, "yield_kwh_kwp"] = energy_from_pairs(g, g.loc[m])
    else:
        g.loc[m, "yield_kwh_kwp"] = np.nan
    print(f"DIN cap {cap}: {m.mean():.1%} of cell-crop rows capped (vertical layout)")
    return g


def write_outputs(g, stage, outdir, has_energy, full=True):
    g = g.copy()
    g["cap_mwp"] = g.elig_ha * g.gcr_max * ETA * 10
    g["energy_gwh"] = g.cap_mwp * g.yield_kwh_kwp / 1000
    if full:
        g.to_csv(os.path.join(outdir, f"cell_crop_{stage}.csv.gz"), index=False, float_format="%.5g")

    # crops combined, double-cropped overlap counted once (vectorised over cell x model x layout x thr x rule)
    k = ["cell", "state", "model", "config", "thr", "slope_rule"]
    e = g[g.elig_ha > 0].assign(season=lambda d: np.where(d.crop.isin(RABI), "rabi", "kharif"))
    e = e.assign(ga=e.gcr_max * e.elig_ha, ya=e.yield_kwh_kwp * e.elig_ha)
    s = e.groupby(k + ["season"]).agg(A=("elig_ha", "sum"), ga=("ga", "sum"), ya=("ya", "sum")).unstack("season")
    s.columns = [f"{v}_{c}" for v, c in s.columns]
    for c in ("rabi", "kharif"):
        for v in ("A", "ga", "ya"):
            s[f"{v}_{c}"] = s.get(f"{v}_{c}", pd.Series(0.0, index=s.index)).fillna(0.0)
        A = s[f"A_{c}"]
        s[f"g_{c}"] = np.where(A > 0, s[f"ga_{c}"] / A.where(A > 0, 1), 0.0)
        # area-weighted specific yield of the season (NaN if no energy table)
        s[f"y_{c}"] = np.where(A > 0, s[f"ya_{c}"] / A.where(A > 0, 1), np.nan) if has_energy else np.nan
    ov = np.minimum(s.A_rabi, s.A_kharif)
    # overlap: both seasons on one field, lower GCR_max; its yield is that of the limiting season
    rabi_lim = s.g_rabi <= s.g_kharif
    g_ov = np.minimum(s.g_rabi, s.g_kharif)
    y_ov = np.where(rabi_lim, s.y_rabi, s.y_kharif)
    cap_parts = [ov * g_ov, (s.A_rabi - ov) * s.g_rabi, (s.A_kharif - ov) * s.g_kharif]
    y_parts = [y_ov, s.y_rabi, s.y_kharif]
    s["land_ha"] = s.A_rabi + s.A_kharif - ov
    s["cap_mwp"] = sum(cap_parts) * ETA * 10
    s["energy_gwh"] = sum(np.nan_to_num(c * ETA * 10 * y / 1000) for c, y in zip(cap_parts, y_parts)) \
        if has_energy else 0.0
    comb = s[["land_ha", "cap_mwp", "energy_gwh"]].reset_index()
    if full:
        comb.to_csv(os.path.join(outdir, f"cell_combined_{stage}.csv.gz"), index=False, float_format="%.5g")

    # India and state totals: per model, then median and range over models
    def totals(df, by, val):
        t = df.groupby(by + ["model"])[val].sum().reset_index()
        return t.groupby(by)[val].agg(["median", "min", "max"]).add_prefix(val + "_").reset_index()

    by = ["crop", "config", "thr", "slope_rule"]
    ti = totals(g, by, "cap_mwp").merge(totals(g, by, "energy_gwh"), on=by) \
        .merge(totals(g, by, "elig_ha"), on=by)
    ti["cap_gw_median"] = ti.cap_mwp_median / 1000
    ti.to_csv(os.path.join(outdir, f"india_by_crop_{stage}.csv"), index=False, float_format="%.5g")
    by = ["config", "thr", "slope_rule"]
    tc = totals(comb, by, "cap_mwp").merge(totals(comb, by, "energy_gwh"), on=by).merge(totals(comb, by, "land_ha"), on=by)
    tc.to_csv(os.path.join(outdir, f"india_combined_{stage}.csv"), index=False, float_format="%.5g")
    ts = totals(comb, ["state"] + by, "cap_mwp").merge(totals(comb, ["state"] + by, "energy_gwh"), on=["state"] + by)
    ts.to_csv(os.path.join(outdir, f"state_combined_{stage}.csv"), index=False, float_format="%.5g")
    if full:   # map table: median GCR_max over models
        mp = g[g.slope_rule == "le5"].groupby(["cell", "crop", "config", "thr"]).agg(
            gcr_med=("gcr_max", "median"), gcr_min=("gcr_max", "min"), gcr_max=("gcr_max", "max"),
            elig_ha=("elig_ha", "first")).reset_index()
        mp.to_csv(os.path.join(outdir, f"map_gcr_{stage}.csv.gz"), index=False, float_format="%.4g")
    show = tc[(tc.slope_rule == "le5")].copy()
    show["GW"] = (show.cap_mwp_median / 1000).round(1)
    show["GW range"] = (show.cap_mwp_min / 1000).round(1).astype(str) + "-" + (show.cap_mwp_max / 1000).round(1).astype(str)
    show["Mha"] = (show.land_ha_median / 1e6).round(2)
    print(f"== {stage}")
    print(show[["config", "thr", "Mha", "GW", "GW range"]].to_string(index=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary")
    ap.add_argument("--stage", required=True)
    ap.add_argument("--grid", required=True)
    ap.add_argument("--slope", required=True)
    ap.add_argument("--energy")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--robust-with", help="second stage (e.g. historical_recommended): GCR_max = min of both")
    ap.add_argument("--din-cap", type=float, default=0.6,
                    help="cap on vertical GCR_max (DIN SPEC 91434, 15%% land loss); 0 = no cap")
    ap.add_argument("--from-cell-crop", help="rebuild from an existing cell_crop_<stage>.csv.gz instead of ry_crop")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    en = pd.read_csv(a.energy) if a.energy and os.path.exists(a.energy) else None

    if a.from_cell_crop:
        g = pd.read_csv(a.from_cell_crop)
        if "gcr_raw" in g:
            g["gcr_max"], g["yield_kwh_kwp"] = g.gcr_raw, g.yield_raw
        g = g.drop(columns=[c for c in ("gcr_raw", "yield_raw", "din_capped", "cap_mwp", "energy_gwh") if c in g])
        if en is not None:
            g["yield_kwh_kwp"] = energy_at(en, g)
        stage = a.stage
    else:
        if not a.summary:
            ap.error("--summary is required unless --from-cell-crop is given")
        grid = pd.read_csv(a.grid)
        slope = pd.read_csv(a.slope).set_index("cell_id")
        g = gcr_table(pd.read_csv(os.path.join(a.summary, f"ry_crop_{a.stage}.csv.gz")))
        stage = a.stage
        if a.robust_with:
            g2 = gcr_table(pd.read_csv(os.path.join(a.summary, f"ry_crop_{a.robust_with}.csv.gz")))
            k = ["cell", "model", "crop", "config", "thr"]
            g = g.merge(g2[k + ["gcr_max", "at_cap"]].rename(columns={"gcr_max": "g2", "at_cap": "c2"}), on=k, how="left")
            g["gcr_max"] = np.fmin(g.gcr_max, g.g2)
            g["at_cap"] = g.at_cap & g.c2.fillna(True).astype(bool)
            g = g.drop(columns=["g2", "c2"])
            stage = f"{a.stage}_robust"
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

    has_energy = en is not None or (a.from_cell_crop is not None and g.yield_kwh_kwp.notna().any())
    g = apply_din_cap(g, a.din_cap, en, a.from_cell_crop is not None)
    write_outputs(g, stage, a.outdir, has_energy)
    if a.din_cap > 0:   # sensitivity: no DIN cap (summary tables only)
        u = g.assign(gcr_max=g.gcr_raw, yield_kwh_kwp=g.yield_raw)
        write_outputs(u, f"{stage}_nodin", a.outdir, has_energy, full=False)
    print("wrote", a.outdir)


if __name__ == "__main__":
    main()
