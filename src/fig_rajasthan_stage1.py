"""Figure: relative yield (RY) under agrivoltaics across Rajasthan, GCR 0.3,
farmer practice, current climate (1995-2014), 5-GCM ensemble median.
Rows = crop systems, columns = layouts. Binned colour with a break at RY 0.8.
"""
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap

RUN = Path(sys.argv[1])
OUT = Path(sys.argv[2])
GCR = float(sys.argv[3]) if len(sys.argv) > 3 else 0.3
EXCLUDE = ["R0005"]  # implausible open-field yields (wheat 10.4 t/ha); soil profile under review

mpl.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"], "font.size": 7,
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.direction": "out", "ytick.direction": "out", "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "pdf.fonttype": 42,
})

e = pd.read_csv(RUN / "ry_ensemble.csv")
e = e[(e.gcr.round(2) == GCR) & ~e.cell.isin(EXCLUDE)]
SYSTEMS = [("wheat", "Wheat (irrigated)"), ("pearl_millet", "Pearl millet (rainfed)"),
           ("groundnut_rainfed", "Groundnut (rainfed)"), ("chickpea_mix", "Chickpea (26% irrigated)")]
LAYOUTS = [("south_fixed", "South-facing, elevated"), ("ew_fixed", "East-west, elevated"),
           ("vertical", "Vertical bifacial")]
bounds = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1]  # values outside are clipped into the end bins
cmap = ListedColormap(mpl.colormaps["viridis"](np.linspace(0.0, 1.0, len(bounds) - 1)))
norm = BoundaryNorm(bounds, cmap.N, clip=True)

lats = np.round(np.arange(23.125, 30.25, 0.25), 3)
lons = np.round(np.arange(69.625, 78.25, 0.25), 3)
edges_lat = np.append(lats - 0.125, lats[-1] + 0.125)
edges_lon = np.append(lons - 0.125, lons[-1] + 0.125)

fig, axs = plt.subplots(len(SYSTEMS), len(LAYOUTS), figsize=(6.3, 7.6), constrained_layout=True)
for i, (sys_, slab) in enumerate(SYSTEMS):
    for j, (cfg, clab) in enumerate(LAYOUTS):
        ax = axs[i, j]
        d = e[(e.system == sys_) & (e.config == cfg)]
        grid = np.full((len(lats), len(lons)), np.nan)
        yi = np.searchsorted(lats, d.lat.round(3))
        xi = np.searchsorted(lons, d.lon.round(3))
        grid[yi, xi] = d.ry_med.values
        pm = ax.pcolormesh(edges_lon, edges_lat, np.ma.masked_invalid(grid), cmap=cmap, norm=norm,
                           edgecolors="none")
        share = (d.ry_med >= 0.8).mean() * 100
        ax.text(0.03, 0.97, f"{share:.0f}% of cells\nwith RY ≥ 0.8", transform=ax.transAxes,
                ha="left", va="top", fontsize=6)
        ax.set_aspect(1 / np.cos(np.radians(26.5)))
        ax.set_xlim(69.4, 78.4); ax.set_ylim(22.9, 30.3)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.set_xticks([70, 72, 74, 76, 78]); ax.set_yticks([24, 26, 28, 30])
        ax.set_xticklabels([f"{x}°E" for x in [70, 72, 74, 76, 78]] if i == len(SYSTEMS) - 1 else [])
        ax.set_yticklabels([f"{y}°N" for y in [24, 26, 28, 30]] if j == 0 else [])
        if i == 0:
            ax.set_title(clab, fontsize=8)
        if j == 0:
            ax.set_ylabel(slab, fontsize=8)
        ax.text(-0.02 if j else -0.30, 1.02, "ABCDEFGHIJKL"[i * 3 + j], transform=ax.transAxes,
                fontsize=10, fontweight="bold", va="bottom")
cb = fig.colorbar(pm, ax=axs, orientation="horizontal", shrink=0.6, aspect=40, pad=0.01,
                  ticks=[0.55, 0.65, 0.75, 0.85, 0.95, 1.05])
cb.ax.set_xticklabels(["<0.6", "0.6–0.7", "0.7–0.8", "0.8–0.9", "0.9–1.0", "≥1.0"])
cb.set_label(f"Relative yield under APV at GCR {GCR} (–), ensemble median of 5 GCMs", fontsize=8)
cb.outline.set_linewidth(0.5)
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT.with_suffix(".pdf"))
fig.savefig(OUT.with_suffix(".png"), dpi=300)
print("saved", OUT)
