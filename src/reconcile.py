"""Reconcile our yield-constrained APV capacity with fixed-density national estimates.

Starting from the assumption used in earlier national studies (a fixed power density on all
crop land, no yield check; TERI 0.42-0.75 MW/ha), the assumptions of this study are added
one at a time on the same grid and the same four crops (wheat, chickpea, pearl millet,
groundnut), so each step shows how much of the gap one assumption explains:

  1  fixed density D (0.42 and 0.75 MW/ha) x MapSPAM harvested area of the four crops
  2  + slope rule: only the share of each cell with terrain slope <= 5 %
  3  + double cropping: rabi (wheat, chickpea) and kharif (pearl millet, groundnut) area on
       the same cell shares land, so the overlap min(A_rabi, A_kharif) is counted once
  4  + yield constraint: D replaced by the cell's GCR_max at RY >= thr (calibrated N stage),
       capacity = ha x GCR_max x eta x 10 MW/ha, overlap at the lower of the two seasons
  5  + robust management: GCR_max = min(calibrated N, recommended N) per cell, crop, model

Steps 1-3 do not depend on the climate model. Steps 4-5 are summed per model; the bar is the
median and the error bar the min-max range over models. The land and capacity rules of
steps 2-5 are those of prod/postprocess_india.py (imported, not copied). Only cell-crop pairs
that were simulated enter all steps, so the bars compare like with like; the crop area left
out (crops below the simulation area threshold in a cell) is printed and written to the CSV.

Outputs: <out_csv>  levels for every layout and threshold (GW)
         <fig>      waterfall for one layout and threshold (default ew_fixed, RY >= 0.8)

Usage: python src/reconcile.py --summary runs/s1/summary --stage historical_current
       [--robust-with historical_recommended] [--grid data/grid_india_025.csv]
       [--slope data/slope_india.csv] [--layout ew_fixed] [--thr 0.8] [--din-cap 0.6]
       [--fig results/figures/fig_reconcile.pdf] [--out-csv results/potential/reconcile.csv]
Without --robust-with (or if that file is missing) step 5 is left out of the figure.
"""
import argparse
import os
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "prod"))
from postprocess_india import DIN_LAYOUT, ETA, KHARIF, RABI, gcr_table  # noqa: E402

DENS = (0.42, 0.75)          # MW/ha, TERI (2026) range
SLOPE_COL = "frac_slope_le5"
LAYOUT_NAME = {"ew_fixed": "east-west elevated", "south_fixed": "south-facing elevated",
               "vertical": "vertical bifacial"}

mpl.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"], "font.size": 7,
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.direction": "out", "ytick.direction": "out", "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42, "legend.frameon": False,
})
C_TOTAL, C_DOWN, C_UP = "0.45", "#D55E00", "#0072B2"   # grey, Okabe-Ito vermillion / blue


def season_land(d):
    """Per cell: rabi and kharif eligible area and the land counted once (max of the two)."""
    ar = d[d.crop.isin(RABI)].groupby("cell").elig_ha.sum()
    ak = d[d.crop.isin(KHARIF)].groupby("cell").elig_ha.sum()
    s = pd.concat([ar.rename("Ar"), ak.rename("Ak")], axis=1).fillna(0.0)
    s["land"] = s.Ar + s.Ak - np.minimum(s.Ar, s.Ak)
    return s


def yield_capacity(g):
    """Capacity (MWp) per model with GCR_max, same combination rule as postprocess_india.py (vectorised)."""
    g = g[g.elig_ha > 0].assign(season=lambda d: np.where(d.crop.isin(RABI), "r", "k"),
                                 ga=lambda d: d.gcr_max * d.elig_ha)
    s = g.groupby(["model", "cell", "season"])[["elig_ha", "ga"]].sum().unstack("season", fill_value=0.0)
    A_r, A_k = s[("elig_ha", "r")] if ("elig_ha", "r") in s else 0.0, s[("elig_ha", "k")] if ("elig_ha", "k") in s else 0.0
    G_r = (s[("ga", "r")] / A_r).where(A_r > 0, 0.0) if ("ga", "r") in s else 0.0
    G_k = (s[("ga", "k")] / A_k).where(A_k > 0, 0.0) if ("ga", "k") in s else 0.0
    ov = np.minimum(A_r, A_k)
    mw = (ov * np.minimum(G_r, G_k) + (A_r - ov) * G_r + (A_k - ov) * G_k) * ETA * 10
    return mw.groupby(level="model").sum()


def gcr_long(summary, stage, area, slope, din_cap=0.6):
    ry = pd.read_csv(os.path.join(summary, f"ry_crop_{stage}.csv.gz"))
    g = gcr_table(ry)
    if din_cap > 0:   # DIN SPEC 91434 land-loss cap on the vertical layout, as in postprocess_india.py
        v = g.config == DIN_LAYOUT
        g.loc[v, "gcr_max"] = g.loc[v, "gcr_max"].clip(upper=din_cap)
    g = g.merge(area, on=["cell", "crop"], how="left")
    g["elig_ha"] = g.area_ha * g.cell.map(slope).fillna(0.0)
    return g


def levels(a):
    grid = pd.read_csv(a.grid)
    slope = pd.read_csv(a.slope).set_index("cell_id")[SLOPE_COL]
    area = grid.melt(id_vars=["cell_id"], value_vars=[f"{c}_ha" for c in RABI + KHARIF],
                     var_name="crop", value_name="area_ha").rename(columns={"cell_id": "cell"})
    area["crop"] = area.crop.str.replace("_ha", "")

    g = gcr_long(a.summary, a.stage, area, slope, a.din_cap)
    rob = None
    if a.robust_with and os.path.exists(os.path.join(a.summary, f"ry_crop_{a.robust_with}.csv.gz")):
        g2 = gcr_long(a.summary, a.robust_with, area, slope, a.din_cap)
        k = ["cell", "model", "crop", "config", "thr"]
        rob = g.merge(g2[k + ["gcr_max"]].rename(columns={"gcr_max": "g2"}), on=k, how="left")
        rob["gcr_max"] = np.fmin(rob.gcr_max, rob.g2)
    elif a.robust_with:
        print(f"note: ry_crop_{a.robust_with}.csv.gz not found, step 5 left out")

    # simulated cell-crop pairs define the land base of every step
    pairs = g[["cell", "crop"]].drop_duplicates().merge(area, on=["cell", "crop"], how="left")
    pairs["elig_ha"] = pairs.area_ha * pairs.cell.map(slope).fillna(0.0)
    cells = pairs.cell.unique()
    all_area = area[area.cell.isin(cells)].area_ha.sum()
    grid_area = area.area_ha.sum()
    A1 = pairs.area_ha.sum()
    A2 = pairs.elig_ha.sum()
    A3 = season_land(pairs).land.sum()
    print(f"crop area on grid {grid_area / 1e6:.3f} Mha; in simulated cells {all_area / 1e6:.3f} Mha; "
          f"simulated cell-crop pairs {A1 / 1e6:.3f} Mha ({100 * A1 / grid_area:.1f}% of grid)")

    rows = []
    for cfg in sorted(g.config.unique()):
        for thr in sorted(g.thr.unique()):
            sel = (g.config == cfg) & (g.thr == thr)
            c4 = yield_capacity(g[sel])
            c5 = yield_capacity(rob[(rob.config == cfg) & (rob.thr == thr)]) if rob is not None else None
            for D in DENS:
                base = dict(config=cfg, thr=thr, density_mw_ha=D)
                for step, name, ha in ((1, "fixed density, all crop area", A1),
                                       (2, "slope <= 5%", A2), (3, "double cropping counted once", A3)):
                    rows.append(base | dict(step=step, name=name, land_mha=ha / 1e6,
                                            gw_median=ha * D / 1e3, gw_min=ha * D / 1e3, gw_max=ha * D / 1e3))
                for step, name, c in ((4, f"yield constraint ({a.stage})", c4),
                                      (5, f"robust management (min with {a.robust_with})", c5)):
                    if c is None:
                        continue
                    rows.append(base | dict(step=step, name=name, land_mha=A3 / 1e6, gw_median=c.median() / 1e3,
                                            gw_min=c.min() / 1e3, gw_max=c.max() / 1e3))
    t = pd.DataFrame(rows)
    t["grid_crop_mha"] = grid_area / 1e6
    t["simulated_share"] = A1 / grid_area
    return t


def waterfall(t, a):
    s = t[(t.config == a.layout) & np.isclose(t.thr, a.thr)]
    hi = s[s.density_mw_ha == max(DENS)].set_index("step")
    lo = s[s.density_mw_ha == min(DENS)].set_index("step")
    tw = hi.gw_median.max() >= 1000
    k = 1e-3 if tw else 1.0
    unit = "TWp" if tw else "GWp"
    steps = list(hi.index)
    lv = hi.gw_median * k

    labels = {1: f"Fixed {max(DENS):.2f}\nMW ha$^{{-1}}$, all\ncrop area",
              2: "Slope\n≤ 5%", 3: "Double-cropped\nland once",
              4: f"Yield limit\nRY ≥ {a.thr:.2f}", 5: "Robust nitrogen\nmanagement"}
    xs, names = [], []
    fig, ax = plt.subplots(figsize=(5.51, 2.7))   # 140 mm, 1.5 column
    w = 0.62
    # start total
    ax.bar(0, lv[1], w, color=C_TOTAL, lw=0)
    xs.append(0); names.append(labels[1])
    for i, st in enumerate(steps[1:], start=1):
        prev, cur = lv[steps[i - 1]], lv[st]
        d = cur - prev
        ax.bar(i, d, w, bottom=prev, color=C_DOWN if d < 0 else C_UP, lw=0)
        ax.plot([i - 1 + w / 2, i - w / 2], [prev, prev], color="0.2", lw=0.5)
        top = max(prev, cur)
        if st >= 4:
            lo_, hi_ = hi.loc[st, "gw_min"] * k, hi.loc[st, "gw_max"] * k
            ax.errorbar(i, cur, yerr=[[cur - lo_], [hi_ - cur]], color="0.1", lw=0.6, capsize=1.5, capthick=0.6)
            top = max(top, hi_)
        ax.text(i, top + 0.02 * lv[1], f"{100 * d / prev:+.0f}%".replace("-", "−"), ha="center", va="bottom", fontsize=6)
        xs.append(i); names.append(labels[st])
    # end total
    n = len(steps)
    ax.plot([n - 1 + w / 2, n - w / 2], [lv[steps[-1]]] * 2, color="0.2", lw=0.5)
    ax.bar(n, lv[steps[-1]], w, color=C_TOTAL, lw=0)
    lo_, hi_ = hi.loc[steps[-1], "gw_min"] * k, hi.loc[steps[-1], "gw_max"] * k
    ax.errorbar(n, lv[steps[-1]], yerr=[[lv[steps[-1]] - lo_], [hi_ - lv[steps[-1]]]], color="0.1", lw=0.6,
                capsize=1.5, capthick=0.6)
    xs.append(n); names.append("This study" if 5 in steps else "This study\n(upper bound)")
    # low fixed density (0.42 MW/ha) chain for steps 1-3 (step s sits at x = s - 1), joining step 4
    l3 = [s_ for s_ in (1, 2, 3) if s_ in lo.index]
    y3 = lo.loc[l3, "gw_median"].values * k
    ax.plot([s_ - 1 for s_ in l3], y3, ls="none", marker="D", ms=3, mfc="white", mec="0.1", mew=0.6,
            label=f"Fixed {min(DENS):.2f} MW ha$^{{-1}}$", zorder=3)
    if 4 in steps:
        ax.plot([2, 3 - w / 2], [y3[-1], lv[4]], ls=":", color="0.1", lw=0.6)
    ax.set_xticks(xs)
    ax.set_xticklabels(names, fontsize=6.5)
    ax.set_xlim(-0.6, n + 0.6)
    ax.set_ylim(0, max(hi.gw_max.max() * k, lv.max()) * 1.12)
    ax.set_ylabel(f"Capacity ({unit})", fontsize=8)
    ax.tick_params(axis="y", labelsize=7)
    from matplotlib.patches import Patch
    hd = [Patch(color=C_TOTAL, label="Total"), Patch(color=C_DOWN, label="Decrease"),
          Patch(color=C_UP, label="Increase")] + ax.get_legend_handles_labels()[0]
    ax.legend(handles=hd, fontsize=6.5, loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=4,
              handlelength=1.0, columnspacing=1.2, borderaxespad=0.1)
    fig.tight_layout()
    Path(a.fig).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.fig)
    fig.savefig(Path(a.fig).with_suffix(".png"), dpi=600)
    print("wrote", a.fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", required=True)
    ap.add_argument("--stage", default="historical_current")
    ap.add_argument("--robust-with", default="historical_recommended")
    ap.add_argument("--grid", default=str(ROOT / "data/grid_india_025.csv"))
    ap.add_argument("--slope", default=str(ROOT / "data/slope_india.csv"))
    ap.add_argument("--layout", default="ew_fixed")
    ap.add_argument("--thr", type=float, default=0.8)
    ap.add_argument("--din-cap", type=float, default=0.6, help="vertical GCR_max cap (0 = none)")
    ap.add_argument("--fig", default=str(ROOT / "results/figures/fig_reconcile.pdf"))
    ap.add_argument("--out-csv", default=str(ROOT / "results/potential/reconcile.csv"))
    a = ap.parse_args()
    if a.robust_with == a.stage:
        a.robust_with = None
    t = levels(a)
    Path(a.out_csv).parent.mkdir(parents=True, exist_ok=True)
    t.to_csv(a.out_csv, index=False, float_format="%.5g")
    print("wrote", a.out_csv)
    s = t[(t.config == a.layout) & np.isclose(t.thr, a.thr)]
    print(s[["density_mw_ha", "step", "name", "land_mha", "gw_median", "gw_min", "gw_max"]]
          .to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    waterfall(t, a)


if __name__ == "__main__":
    main()
