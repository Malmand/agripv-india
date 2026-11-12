"""Food side of the yield-constrained potential: crop production kept and given up under the arrays.

For every cell, crop and GCM (east-west layout, RY >= 0.80, slope <= 5%, robust nitrogen GCR_max by default):
  RY_c   = simulated relative yield at the crop's GCR_max under calibrated (current) nitrogen, interpolated in
           the RY-GCR curve of ry_crop_<stage>.csv.gz, which starts at RY = 1 for GCR = 0
  P_c    = eligible area x observed 1995-2014 state yield (ICRISAT District Level Data, as in calibrate_n.py;
           national area-weighted mean where the state has no record); observed, not simulated, yields so that
           crop-model yield bias (e.g. groundnut x2.6) does not enter the tonnes
  lost_c = P_c x (1 - RY_c)
Each crop is taken at its own GCR_max. On double-cropped land the array carries the lower density of the two
seasons, so the loss is an upper bound for the season with the higher GCR_max.
Food energy for the three food grains uses the Indian Food Composition Tables 2017 (Longvah et al., NIN):
wheat, whole (A020) 1347 kJ, bajra (A003) 1456 kJ, Bengal gram, whole (B002) 1201 kJ per 100 g edible portion.
Groundnut, mainly crushed for oil and reported in pods, is given in tonnes only.

Outputs: results/potential/food_by_crop.csv (median and GCM range), food_cell.csv.gz (per cell, GCM median),
food_curve.csv (cells ordered by energy per tonne of crop given up), results/figures/fig_food.{pdf,png}.
Usage: python src/food_tradeoff.py [--pp results/potential] [--summary runs/s1/summary]
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

KJ_PER_KG = {"wheat": 13470, "pearl_millet": 14560, "chickpea": 12010}      # IFCT 2017, per kg edible portion
CROPS = ["wheat", "chickpea", "pearl_millet", "groundnut"]
DLD = {"wheat": "WHEAT", "chickpea": "CHICKPEA", "groundnut": "GROUNDNUT", "pearl_millet": "PEARL MILLET"}


def observed_state_yields(f):
    k = pd.read_csv(f)
    k = k[(k.Year >= 1995) & (k.Year <= 2014)]
    rows = []
    for cr, n in DLD.items():
        a, p = f"{n} AREA (1000 ha)", f"{n} PRODUCTION (1000 tons)"
        s = k.groupby(["State Name", "Year"])[[a, p]].sum().reset_index()
        s = s[s[a] > 0]
        s["y"] = s[p] / s[a] * 1000
        o = s.groupby("State Name").agg(obs=("y", "mean"), area=(a, "mean")).reset_index().assign(crop=cr)
        rows.append(o)
    o = pd.concat(rows).rename(columns={"State Name": "state"})
    o["state"] = o.state.replace({"Orissa": "Odisha"})
    nat = o.groupby("crop").apply(lambda d: np.average(d.obs, weights=d.area), include_groups=False)
    return o[["state", "crop", "obs"]], nat


def ry_at(curve, g):
    """RY at GCR g on a curve [(gcr, ry), ...] that starts at (0, 1)."""
    x, y = zip(*sorted(curve))
    return float(np.interp(g, (0,) + x, (1.0,) + y))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pp", type=Path, default=Path("results/potential"))
    ap.add_argument("--summary", type=Path, default=Path("runs/s1/summary"))
    ap.add_argument("--stage", default="historical_current_robust", help="GCR_max table (cell_crop_<stage>)")
    ap.add_argument("--ry-stages", nargs="+", default=["historical_current", "historical_recommended"],
                    help="RY curves: current (calibrated) management, then recommended nitrogen")
    ap.add_argument("--dld", type=Path, default=Path("data/yields/kaggle_raw/ICRISAT-District Level Data.csv"))
    ap.add_argument("--config", default="ew_fixed")
    ap.add_argument("--thr", type=float, default=0.8)
    ap.add_argument("--fig", type=Path, default=Path("results/figures"))
    a = ap.parse_args()

    c = pd.read_csv(a.pp / f"cell_crop_{a.stage}.csv.gz")
    c = c[(c.config == a.config) & (c.thr.round(2) == a.thr) & (c.slope_rule == "le5") & (c.elig_ha > 0)]
    comb = pd.read_csv(a.pp / f"cell_combined_{a.stage}.csv.gz")
    comb = comb[(comb.config == a.config) & (comb.thr.round(2) == a.thr) & (comb.slope_rule == "le5")]
    e_model = comb.groupby("model").energy_gwh.sum()          # crops combined, double-cropped land once
    obs, nat = observed_state_yields(a.dld)
    c0 = c.merge(obs, on=["state", "crop"], how="left")
    c0["obs"] = c0.obs.fillna(c0.crop.map(nat))
    c0["prod_t"] = c0.elig_ha * c0.obs / 1000
    c0["kj"] = c0.crop.map(KJ_PER_KG)
    outs, cells = [], []
    for k, rs in enumerate(a.ry_stages):
        tag = "cur" if k == 0 else "rec"
        r = pd.read_csv(a.summary / f"ry_crop_{rs}.csv.gz")
        r = r[(r.config == a.config) & (r.water == "all")]
        curves = r.groupby(["cell", "model", "crop"]).apply(lambda d: list(zip(d.gcr, d.ry)), include_groups=False)
        x = c0.join(curves.rename("curve"), on=["cell", "model", "crop"]).dropna(subset=["curve"])
        x["ry"] = [min(ry_at(cv, g), 1.0) for cv, g in zip(x.curve, x.gcr_max)]   # RY > 1 not counted as a gain
        x["lost_t"] = x.prod_t * (1 - x.ry)
        x["prod_pj"] = x.prod_t * 1000 * x.kj / 1e12          # kJ -> PJ
        x["lost_pj"] = x.lost_t * 1000 * x.kj / 1e12
        v = ["prod_t", "lost_t", "prod_pj", "lost_pj"]
        by = x.groupby(["crop", "model"])[v].sum()
        tot = x.groupby("model")[v].sum().assign(crop="all").reset_index().set_index(["crop", "model"])
        by = pd.concat([by, tot])
        by["lost_pct"] = 100 * by.lost_t / by.prod_t
        by["lost_pj_pct"] = 100 * by.lost_pj / by.prod_pj
        by["kg_per_mwh"] = by.lost_t * 1000 / (by.index.get_level_values("model").map(e_model).values * 1000)
        o = by.groupby("crop").agg(["median", "min", "max"])
        o.columns = [f"{vv}_{s_}" for vv, s_ in o.columns]
        outs.append(o.reset_index().assign(mgmt=tag))
        if True:
            cell = x.groupby(["cell", "model"])[["prod_t", "lost_t", "elig_ha"]].sum().reset_index() \
                .merge(comb[["cell", "model", "energy_gwh"]], on=["cell", "model"], how="left")
            cell = cell.groupby("cell")[["prod_t", "lost_t", "energy_gwh", "elig_ha"]].median().reset_index()
            cells.append(cell.assign(mgmt=tag))
    out = pd.concat(outs)
    a.pp.mkdir(parents=True, exist_ok=True)
    out.to_csv(a.pp / "food_by_crop.csv", index=False, float_format="%.6g")
    cell = pd.concat(cells).dropna(subset=["energy_gwh"])
    cell["kg_per_mwh"] = cell.lost_t * 1000 / (cell.energy_gwh * 1000)
    cell.to_csv(a.pp / "food_cell.csv.gz", index=False, float_format="%.6g")
    # cells ordered from the least crop given up per MWh (zero-loss cells first)
    cu = cell.sort_values(["mgmt", "kg_per_mwh"])
    cu = cu.assign(cum_energy_pwh=cu.groupby("mgmt").energy_gwh.cumsum() / 1e6,
                   cum_lost_mt=cu.groupby("mgmt").lost_t.cumsum() / 1e6)
    cu[["mgmt", "cell", "kg_per_mwh", "cum_energy_pwh", "cum_lost_mt"]].to_csv(a.pp / "food_curve.csv", index=False,
                                                                                float_format="%.6g")
    for tag in ("cur", "rec"):
        t = out[out.mgmt == tag].set_index("crop")
        if not len(t):
            continue
        print(f"[{tag}] production {t.loc['all', 'prod_t_median'] / 1e6:.1f} Mt, lost {t.loc['all', 'lost_t_median'] / 1e6:.2f} Mt "
              f"({t.loc['all', 'lost_pct_median']:.1f}%; food energy {t.loc['all', 'lost_pj_pct_median']:.1f}%), "
              f"{t.loc['all', 'kg_per_mwh_median']:.3f} kg per MWh")
        for cr in CROPS:
            if cr in t.index:
                print(f"   {cr:13s} {t.loc[cr, 'prod_t_median'] / 1e6:6.2f} Mt, lost {t.loc[cr, 'lost_t_median'] / 1e6:5.2f} Mt "
                      f"({t.loc[cr, 'lost_pct_median']:.1f}%)")


if __name__ == "__main__":
    main()
