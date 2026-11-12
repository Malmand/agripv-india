"""Food side of the potential (reads src/food_tradeoff.py outputs): one figure, three panels.
  A  map: crop given up per unit of electricity (kg per MWh), recommended nitrogen, GCM median
  B  share of production given up by crop: current (calibrated) management filled, recommended nitrogen outline,
     error bars = range of five GCMs; dashed line = the 20% that the threshold allows
  C  cumulative crop given up against cumulative electricity, cells ordered from the least crop per MWh;
     vertical line = India's 2025-26 electricity requirement (CEA)
Usage: python src/fig_food.py [--pp results/potential] [--out results/figures]
"""
import argparse
import sys
import warnings
from pathlib import Path

import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm

sys.path.insert(0, str(Path(__file__).parent))
import fig_india as F   # noqa: E402  (map helpers and journal style)

CROPS = [("wheat", "Wheat"), ("chickpea", "Chickpea"), ("pearl_millet", "Pearl\nmillet"), ("groundnut", "Groundnut"),
         ("all", "Four\ncrops")]
CEA_PWH = 1.707493          # India's 2025-26 energy requirement, 1,707,493 MU (CEA LGBR 2026-27); as make_numbers.py


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pp", type=Path, default=Path("results/potential"))
    ap.add_argument("--out", type=Path, default=Path("results/figures"))
    ap.add_argument("--grid", default="data/grid_india_025.csv")
    ap.add_argument("--boundaries", default="data/boundaries/Admin2.shp")
    a = ap.parse_args()
    warnings.filterwarnings("ignore")
    grid = pd.read_csv(a.grid)
    states = gpd.read_file(a.boundaries)
    states["geometry"] = states.geometry.buffer(0.03).buffer(-0.03).simplify(0.02, preserve_topology=True)
    F.CLIP = states.geometry.union_all().buffer(0.02)
    cell = pd.read_csv(a.pp / "food_cell.csv.gz")
    by = pd.read_csv(a.pp / "food_by_crop.csv")
    cu = pd.read_csv(a.pp / "food_curve.csv")

    fig = plt.figure(figsize=(6.3, 4.6), constrained_layout=True)
    gs = fig.add_gridspec(2, 2, width_ratios=[1.05, 1])
    axA = fig.add_subplot(gs[:, 0]); axB = fig.add_subplot(gs[0, 1]); axC = fig.add_subplot(gs[1, 1])

    # A: kg per MWh, recommended nitrogen
    d = cell[(cell.mgmt == "rec") & (cell.elig_ha >= F.MIN_HA)]
    bounds = [0, 0.1, 0.2, 0.3, 0.4, 0.6]
    cmap = mpl.colormaps["viridis"].resampled(len(bounds) - 1).with_extremes(over=mpl.colormaps["viridis"](0.999))
    norm = BoundaryNorm(bounds, cmap.N)
    g = grid.set_index("cell_id").loc[d.cell]
    pm = F.draw_cells(axA, g.lon.values, g.lat.values, d.kg_per_mwh.values, cmap, norm)
    F.india_axes(axA, states, True, True)
    cb = fig.colorbar(pm, ax=axA, orientation="horizontal", shrink=0.85, aspect=28, pad=0.02, extend="max")
    cb.set_ticks(bounds); cb.ax.tick_params(labelsize=7)
    cb.set_label("Crop given up per unit electricity (kg MWh$^{-1}$)", fontsize=8)
    F.panel_label(axA, "A")

    # B: share of production given up by crop
    x = np.arange(len(CROPS)); bw = 0.36
    for k, (tag, fc, lab) in enumerate((("cur", "0.35", "Current N"), ("rec", "white", "Recommended N"))):
        t = by[by.mgmt == tag].set_index("crop")
        m = np.array([t.loc[c, "lost_pct_median"] for c, _ in CROPS])
        lo = np.array([t.loc[c, "lost_pct_min"] for c, _ in CROPS]); hi = np.array([t.loc[c, "lost_pct_max"] for c, _ in CROPS])
        xx = x + (k - 0.5) * bw
        axB.bar(xx, m, bw * 0.92, facecolor=fc, edgecolor="black", linewidth=0.7, label=lab)
        axB.errorbar(xx, m, yerr=[m - lo, hi - m], fmt="none", ecolor="black", elinewidth=0.6, capsize=1.5)
    axB.axhline(20, color="black", lw=0.6, ls="--")
    axB.text(len(CROPS) - 0.45, 20.5, "Allowed by RY ≥ 0.80", ha="right", va="bottom", fontsize=6.5)
    axB.set_xticks(x); axB.set_xticklabels([l for _, l in CROPS], fontsize=7)
    axB.set_ylabel("Production given up (%)", fontsize=8); axB.tick_params(labelsize=7)
    axB.set_ylim(0, 31)
    axB.legend(fontsize=6.5, loc="upper left", ncol=2, columnspacing=1.0, handlelength=1.4)
    F.panel_label(axB, "B")

    # C: cumulative curve
    for tag, ls, lab in (("cur", "-", "Current N"), ("rec", "--", "Recommended N")):
        c = cu[cu.mgmt == tag]
        axC.plot(np.r_[0, c.cum_energy_pwh], np.r_[0, c.cum_lost_mt], color="black", ls=ls, lw=1.0, label=lab)
    axC.axvline(CEA_PWH, color="0.4", lw=0.6, ls=":")
    axC.text(CEA_PWH + 1, axC.get_ylim()[1] * 0.92 if False else 14.5, "India's electricity\nrequirement 2025–26",
             fontsize=6.5, va="top")
    axC.set_xlim(0, None); axC.set_ylim(0, 17)
    axC.set_xlabel("Cumulative electricity (PWh yr$^{-1}$)", fontsize=8)
    axC.set_ylabel("Crop given up (Mt yr$^{-1}$)", fontsize=8); axC.tick_params(labelsize=7)
    axC.legend(fontsize=6.5, loc="center left", bbox_to_anchor=(0.0, 0.55))
    F.panel_label(axC, "C")
    a.out.mkdir(parents=True, exist_ok=True)
    F.save(fig, a.out / "fig_food", png_dpi=400)
    print("wrote", a.out / "fig_food.pdf")


if __name__ == "__main__":
    main()
