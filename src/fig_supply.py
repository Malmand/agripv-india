"""Land-supply curve (review comment M8): cropland needed for a given APV capacity when the cells with the
highest yield-constrained power density are used first.

For each GCM, cells (east-west layout, RY >= 0.80, slope <= 5%) are sorted by capacity per hectare (crops
combined, cell_combined_<stage>.csv.gz) and capacity and land are accumulated; the curve is the median over
the five GCMs, the band their range. A dashed line shows land at the national mean density.
Writes results/figures/figS6_supply_curve.{pdf,png} and results/potential/supply_curve.csv
(capacity_gwp, land_mha_med, land_mha_min, land_mha_max).
Usage: python src/fig_supply.py [--pp results/potential] [--stage historical_current_robust]
"""
import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

mpl.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"], "font.size": 7,
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.direction": "out", "ytick.direction": "out", "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42, "legend.frameon": False,
})
TARGETS = (300, 500)   # GWp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pp", type=Path, default=Path("results/potential"))
    ap.add_argument("--stage", default="")
    ap.add_argument("--out", type=Path, default=Path("results/figures"))
    a = ap.parse_args()
    st = a.stage or ("historical_current_robust" if (a.pp / "cell_combined_historical_current_robust.csv.gz").exists()
                     else "historical_current")
    c = pd.read_csv(a.pp / f"cell_combined_{st}.csv.gz")
    c = c[(c.config == "ew_fixed") & (c.thr.round(2) == 0.8) & (c.slope_rule == "le5") & (c.land_ha > 0)]
    grid = np.unique(np.r_[np.geomspace(1, c.groupby("model").cap_mwp.sum().min() / 1e3, 400), TARGETS])
    curves, mean_dens = [], []
    for m, d in c.groupby("model"):
        d = d.assign(dens=d.cap_mwp / d.land_ha).sort_values("dens", ascending=False)
        cap = np.r_[0, d.cap_mwp.cumsum().values] / 1e3          # GWp
        land = np.r_[0, d.land_ha.cumsum().values] / 1e6         # Mha
        curves.append(np.interp(grid, cap, land))
        mean_dens.append(d.cap_mwp.sum() / d.land_ha.sum())
    L = np.array(curves)
    med, lo, hi = np.median(L, 0), L.min(0), L.max(0)
    md = float(np.median(mean_dens))                             # MWp/ha
    out = pd.DataFrame({"capacity_gwp": grid, "land_mha_med": med, "land_mha_min": lo, "land_mha_max": hi})
    out.attrs["mean_density"] = md
    a.pp.mkdir(parents=True, exist_ok=True)
    out.to_csv(a.pp / "supply_curve.csv", index=False, float_format="%.5g")

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.7), constrained_layout=True)
    for k, (ax, xmax, unit, sc) in enumerate(zip(axes, (grid[-1], 1000), ("TWp", "GWp"), (1e3, 1))):
        x = grid / sc
        m = grid <= xmax * (1 if sc == 1 else 1e3) + 1e-9
        ax.fill_between(x[m], lo[m], hi[m], color="#56B4E9", alpha=0.4, lw=0, label="GCM range")
        ax.plot(x[m], med[m], color="#0072B2", lw=1.2, label="Densest cells first (median)")
        ax.plot(x[m], grid[m] / 1e3 / md, color="0.3", lw=0.8, ls="--",
                label=f"National mean density ({md:.2f} MWp ha$^{{-1}}$)")
        ax.set_xlim(0, x[m][-1]); ax.set_ylim(0, None)
        ax.set_xlabel(f"Cumulative APV capacity ({unit})", fontsize=8)
        ax.set_ylabel("Cropland needed (Mha)", fontsize=8)
        ax.text(-0.17, 1.02, "AB"[k], transform=ax.transAxes, fontsize=11, fontweight="bold", va="bottom")
    ax = axes[1]
    for t in TARGETS:
        y = np.interp(t, grid, med)
        ax.plot(t, y, "o", ms=3.5, mfc="white", mec="#0072B2", mew=0.8, zorder=5)
        ax.annotate(f"{t} GWp: {y:.2f} Mha", (t, y), xytext=(6, -9), textcoords="offset points", ha="left", fontsize=6.5)
    axes[0].legend(fontsize=6, loc="upper left")
    a.out.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out / "figS6_supply_curve.pdf")
    fig.savefig(a.out / "figS6_supply_curve.png", dpi=400)
    print("supply curve:", {t: round(float(np.interp(t, grid, med)), 3) for t in TARGETS}, "Mha; mean density", round(md, 2))


if __name__ == "__main__":
    main()
