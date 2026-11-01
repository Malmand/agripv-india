"""Headline numbers for the Results text, from postprocess_india.py outputs.

Writes <pp>/headline_numbers.md: India totals (crops combined, slope <= 5%) by layout and
threshold, crop-level GCR_max and share of area at the simulated GCR limit, top states,
calibrated vs robust, and mid-century change if future stages are present.
With --summary (folder with ry_crop_<stage>.csv.gz) it adds sanity checks: open-field yields by
state against the calibration (results/validation_before_after.csv), capacity density, specific
yield, and the share of vertical-layout area with GCR_max > 0.6 (DIN SPEC 91434 15% land loss).
Usage: python results_summary.py --pp results/potential --stages historical_current [historical_current_robust
       ssp585_current ...] [--summary runs/s1/summary --grid data/grid_india_025.csv]
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def fmt_range(m, lo, hi, scale, nd=1):
    return f"{m / scale:.{nd}f} ({lo / scale:.{nd}f}–{hi / scale:.{nd}f})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pp", required=True, type=Path)
    ap.add_argument("--stages", nargs="+", required=True)
    ap.add_argument("--summary", type=Path, help="folder with ry_crop_<stage>.csv.gz (sanity checks)")
    ap.add_argument("--grid", type=Path, default=Path("data/grid_india_025.csv"))
    ap.add_argument("--validation", type=Path, default=Path("results/validation_before_after.csv"))
    a = ap.parse_args()
    out = ["# Headline numbers (median over 5 GCMs, range in brackets)", ""]
    base = a.stages[0]
    for st in a.stages:
        f = a.pp / f"india_combined_{st}.csv"
        if not f.exists():
            continue
        t = pd.read_csv(f)
        t = t[t.slope_rule == "le5"].sort_values(["thr", "config"])
        out += [f"## {st}: crops combined, slope ≤ 5%", "",
                "| Layout | τ | Land (Mha) | Capacity (TWp) | Energy (PWh/yr) |", "|---|---|---|---|---|"]
        for r in t.itertuples():
            en = fmt_range(r.energy_gwh_median, r.energy_gwh_min, r.energy_gwh_max, 1e6, 2) if np.isfinite(r.energy_gwh_median) and r.energy_gwh_median > 0 else "n/a"
            out.append(f"| {r.config} | {r.thr:.2f} | {r.land_ha_median / 1e6:.2f} | "
                       f"{fmt_range(r.cap_mwp_median, r.cap_mwp_min, r.cap_mwp_max, 1e6, 2)} | {en} |")
        out.append("")
        c = pd.read_csv(a.pp / f"cell_crop_{st}.csv.gz")
        c = c[(c.slope_rule == "le5") & (c.thr.round(2) == 0.8) & (c.elig_ha > 0)]
        w = c.groupby(["crop", "config"]).apply(lambda d: pd.Series({
            "gcr_aw": np.average(d.gcr_max, weights=d.elig_ha),
            "share_at_cap": np.average(d.at_cap.astype(float), weights=d.elig_ha) if "at_cap" in d else np.nan}),
            include_groups=False).reset_index()
        out += [f"### {st}: area-weighted GCR_max at τ = 0.80 (all GCMs pooled)", "",
                "| Crop | Layout | GCR_max | Share of area at simulated GCR limit |", "|---|---|---|---|"]
        out += [f"| {r.crop} | {r.config} | {r.gcr_aw:.2f} | {r.share_at_cap:.0%} |" for r in w.itertuples()]
        out.append("")
        s = pd.read_csv(a.pp / f"state_combined_{st}.csv")
        s = s[(s.slope_rule == "le5") & (s.thr.round(2) == 0.8)]
        top = s.groupby("state").cap_mwp_median.max().sort_values(ascending=False).head(8)
        out += [f"### {st}: top states, best layout, τ = 0.80 (GWp)", ""]
        out += [f"- {k}: {v / 1e3:.0f}" for k, v in top.items()]
        out.append("")
    # mid-century change against the first stage
    b = a.pp / f"india_combined_{base}.csv"
    for st in a.stages[1:]:
        f = a.pp / f"india_combined_{st}.csv"
        if not (b.exists() and f.exists()) or "robust" in st or "recommended" in st:
            continue
        x = pd.read_csv(b).merge(pd.read_csv(f), on=["config", "thr", "slope_rule"], suffixes=("_h", "_f"))
        x = x[x.slope_rule == "le5"]
        out += [f"## Change {base} → {st} (capacity, %)", ""]
        out += [f"- {r.config}, τ {r.thr:.2f}: {100 * (r.cap_mwp_median_f / r.cap_mwp_median_h - 1):+.0f}%" for r in x.itertuples()]
        out.append("")
    # calibrated N vs robust (min of calibrated and recommended N)
    for st in a.stages:
        f, b = a.pp / f"india_combined_{st}.csv", a.pp / f"india_combined_{st}_robust.csv"
        if not (f.exists() and b.exists()):
            continue
        x = pd.read_csv(f).merge(pd.read_csv(b), on=["config", "thr", "slope_rule"], suffixes=("_c", "_r"))
        x = x[x.slope_rule == "le5"]
        out += [f"## Robust vs calibrated N, {st} (capacity, %)", ""]
        out += [f"- {r.config}, τ {r.thr:.2f}: {100 * (r.cap_mwp_median_r / r.cap_mwp_median_c - 1):+.1f}%" for r in x.itertuples()]
        out.append("")
    out += sanity(a)
    (a.pp / "headline_numbers.md").write_text("\n".join(out))
    print("\n".join(out))


def sanity(a):
    """Checks to read before using the numbers (not for the paper text as such)."""
    out = ["## Sanity checks", ""]
    for st in a.stages:
        f = a.pp / f"india_combined_{st}.csv"
        if not f.exists():
            continue
        t = pd.read_csv(f)
        t = t[(t.slope_rule == "le5") & (t.land_ha_median > 0)]
        out += [f"### {st}: capacity density and specific yield (slope ≤ 5%)", "",
                "| Layout | τ | MWp per ha of land | kWh/kWp/yr |", "|---|---|---|---|"]
        for r in t.sort_values(["thr", "config"]).itertuples():
            sy = 1000 * r.energy_gwh_median / r.cap_mwp_median if r.energy_gwh_median > 0 else np.nan
            out.append(f"| {r.config} | {r.thr:.2f} | {r.cap_mwp_median / r.land_ha_median:.2f} | {sy:.0f} |")
        out.append("")
        c = pd.read_csv(a.pp / f"cell_crop_{st}.csv.gz")
        v = c[(c.config == "vertical") & (c.slope_rule == "le5") & (c.elig_ha > 0)]
        if len(v):
            sh = v.groupby("thr").apply(lambda d: np.average(d.gcr_max > 0.6 + 1e-9, weights=d.elig_ha),
                                        include_groups=False)
            out += [f"- {st}: vertical layout, share of eligible area with GCR_max > 0.6 (DIN 15% land loss): "
                    + ", ".join(f"τ {k:.2f} {x:.0%}" for k, x in sh.items()), ""]
    if a.summary is None:
        return out
    grid = pd.read_csv(a.grid)
    obs = pd.read_csv(a.validation) if a.validation.exists() else None
    for st in a.stages:
        f = a.summary / f"ry_crop_{st}.csv.gz"
        if not f.exists():
            continue
        ry = pd.read_csv(f)
        op = ry.groupby(["cell", "model", "crop"]).open.first().groupby(["cell", "crop"]).median().reset_index()
        area = grid.melt(id_vars=["cell_id", "state"], value_vars=[c for c in grid if c.endswith("_ha")],
                         var_name="crop", value_name="ha").rename(columns={"cell_id": "cell"})
        area["crop"] = area.crop.str.replace("_ha", "")
        op = op.merge(area, on=["cell", "crop"])
        op = op[op.ha > 0]
        stt = op.groupby(["state", "crop"]).apply(lambda d: pd.Series({"sim": np.average(d.open, weights=d.ha),
                                                                       "ha": d.ha.sum()}),
                                                  include_groups=False).reset_index()
        out += [f"### {st}: open-field yield (kg/ha, 5-GCM median, SPAM-area weighted)", "",
                "| Crop | Cells | India mean | States matched | Sim/obs (matched states) | Sim/calibration sim |",
                "|---|---|---|---|---|---|"]
        for crop, d in stt.groupby("crop"):
            ncell = (op.crop == crop).sum()
            line = f"| {crop} | {ncell} | {np.average(d.sim, weights=d.ha):.0f} |"
            if obs is not None:
                case = "after" if crop in ("wheat", "pearl_millet") else "before"
                o = obs[(obs.crop == crop) & (obs.case == case)]
                m = d.merge(o, on="state", suffixes=("", "_cal"))
                if len(m):
                    w = m.obs_area
                    line += (f" {len(m)} | {np.average(m.sim, weights=w) / np.average(m.obs, weights=w):.2f} |"
                             f" {np.average(m.sim, weights=w) / np.average(m.sim_cal, weights=w):.2f} |")
                else:
                    line += " 0 | n/a | n/a |"
            out.append(line)
        out += ["", "Legumes are compared with uncalibrated (farmer N) runs; groundnut sim/obs about 2.7 is known.", ""]
    return out


if __name__ == "__main__":
    main()
