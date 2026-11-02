"""Journal figures for the India APV potential (reads postprocess_india.py outputs).

  fig_india_gcrmax_<stage>.pdf      map: GCR_max at RY >= thr, crops x layouts (5-GCM median)
  fig_india_capacity_<stage>.pdf    bars: India capacity (GW) by layout and RY threshold,
                                    error bars = range over 5 GCMs; markers = slope-rule cases
  fig_india_states_<stage>.pdf      bars: top states, capacity at RY >= thr, by layout
  fig_india_delta_<fut>.pdf         map: change in GCR_max, future minus historical (if given)
Usage: python fig_india.py --pp results/potential --stage historical_current --grid grid.csv
       --boundaries Admin2.shp --out results/figures [--thr 0.8] [--future ssp585_current]
"""
import argparse
import warnings
from pathlib import Path

import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap

mpl.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"], "font.size": 7,
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.direction": "out", "ytick.direction": "out", "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42, "legend.frameon": False,
})
CROPS = [("wheat", "Wheat"), ("chickpea", "Chickpea"), ("pearl_millet", "Pearl millet"), ("groundnut", "Groundnut")]
LAYOUTS = [("south_fixed", "South-facing, elevated"), ("ew_fixed", "East-west, elevated"),
           ("vertical", "Vertical bifacial")]
OI = {"south_fixed": "#E69F00", "ew_fixed": "#56B4E9", "vertical": "#009E73"}   # Okabe-Ito
MIN_HA = 1000      # cells with less eligible crop area are left blank on maps


def save(fig, stem):
    """Journal PDF (map rasters 400 dpi) plus a 300 dpi PNG that the manuscript builder embeds."""
    fig.savefig(f"{stem}.pdf", dpi=400)
    fig.savefig(f"{stem}.png", dpi=300)


def panel_label(ax, s):
    ax.text(-0.02, 1.02, s, transform=ax.transAxes, fontsize=10, fontweight="bold", ha="right", va="bottom")


def india_axes(ax, states, bottom, left):
    states.boundary.plot(ax=ax, color="0.35", linewidth=0.25)
    ax.set_xlim(68, 97.5); ax.set_ylim(6.5, 37.2)
    ax.set_aspect(1 / np.cos(np.radians(22)))
    ax.set_xlabel(""); ax.set_ylabel("")
    ax.set_xticks([70, 80, 90]); ax.set_yticks([10, 20, 30])
    ax.set_xticklabels([f"{x}°E" for x in (70, 80, 90)] if bottom else [])
    ax.set_yticklabels([f"{y}°N" for y in (10, 20, 30)] if left else [])


def raster(d, grid, col):
    g = grid.set_index("cell_id").loc[d.cell]
    return g.lon.values, g.lat.values, d[col].values


def draw_cells(ax, lon, lat, val, cmap, norm):
    # 0.25 deg cells as squares (scatter in data units is unreliable; use pcolormesh on a full grid)
    lons = np.round(np.arange(68.125, 97.5, 0.25), 3)
    lats = np.round(np.arange(6.625, 37.25, 0.25), 3)
    z = np.full((len(lats), len(lons)), np.nan)
    z[np.searchsorted(lats, np.round(lat, 3)), np.searchsorted(lons, np.round(lon, 3))] = val
    return ax.pcolormesh(np.append(lons - 0.125, lons[-1] + 0.125), np.append(lats - 0.125, lats[-1] + 0.125),
                         np.ma.masked_invalid(z), cmap=cmap, norm=norm, edgecolors="none", rasterized=True)


def mean_range(pp, stage, thr):
    """Area-weighted mean GCR_max per crop and layout for each GCM -> {(crop, cfg): (min, max)}."""
    f = pp / f"cell_crop_{stage}.csv.gz"
    if not f.exists():
        return {}
    c = pd.read_csv(f, usecols=["cell", "model", "crop", "config", "thr", "slope_rule", "gcr_max", "elig_ha"])
    c = c[(c.slope_rule == "le5") & (c.thr.round(2) == thr) & (c.elig_ha >= MIN_HA)]
    w = c.groupby(["crop", "config", "model"]).apply(lambda d: np.average(d.gcr_max, weights=d.elig_ha),
                                                     include_groups=False)
    return {k: (v.min(), v.max()) for k, v in w.groupby(["crop", "config"])}


def fig_gcrmax(pp, stage, grid, states, thr, out):
    m = pd.read_csv(pp / f"map_gcr_{stage}.csv.gz")
    m = m[(m.thr.round(2) == thr) & (m.elig_ha >= MIN_HA)]
    rng = mean_range(pp, stage, thr)
    bounds = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7001]
    cmap = ListedColormap(mpl.colormaps["viridis"](np.linspace(0, 1, len(bounds) - 1)))
    norm = BoundaryNorm(bounds, cmap.N)
    fig, axs = plt.subplots(4, 3, figsize=(6.3, 8.6), constrained_layout=True)
    for i, (crop, cl) in enumerate(CROPS):
        for j, (cfg, ll) in enumerate(LAYOUTS):
            ax = axs[i, j]
            d = m[(m.crop == crop) & (m.config == cfg)]
            pm = draw_cells(ax, *raster(d, grid, "gcr_med"), cmap, norm)
            india_axes(ax, states, i == 3, j == 0)
            if len(d):
                w = np.average(d.gcr_med, weights=d.elig_ha)
                lo, hi = rng.get((crop, cfg), (np.nan, np.nan))
                # area-weighted mean of the 5-GCM median map (range of the per-GCM means)
                txt = f"{w:.2f}" + (f" ({lo:.2f}–{hi:.2f})" if np.isfinite(lo) else "")
                ax.text(0.02, 0.01, txt, transform=ax.transAxes, ha="left", va="bottom", fontsize=6)
            if i == 0:
                ax.set_title(ll, fontsize=8)
            if j == 0:
                ax.text(-0.38, 0.5, cl, transform=ax.transAxes, rotation=90, va="center", fontsize=8)
            panel_label(ax, "ABCDEFGHIJKL"[3 * i + j])
    cb = fig.colorbar(pm, ax=axs, orientation="horizontal", shrink=0.5, aspect=35, pad=0.01)
    cb.set_label(f"Maximum ground coverage ratio with relative yield ≥ {thr:.2f} (–)", fontsize=8)
    cb.ax.tick_params(labelsize=7)
    save(fig, out / f"fig_india_gcrmax_{stage}_thr{int(thr * 100)}")
    plt.close(fig)


def fig_capacity(pp, stage, out):
    t = pd.read_csv(pp / f"india_combined_{stage}.csv")
    fig, ax = plt.subplots(figsize=(3.5, 3.0), constrained_layout=True)
    thrs = sorted(t.thr.unique())
    w = 0.26
    for j, (cfg, ll) in enumerate(LAYOUTS):
        d = t[(t.config == cfg) & (t.slope_rule == "le5")].set_index("thr").loc[thrs]
        x = np.arange(len(thrs)) + (j - 1) * w
        y = d.cap_mwp_median / 1e6
        ax.bar(x, y, w * 0.92, color=OI[cfg], label=ll, edgecolor="none")
        ax.errorbar(x, y, yerr=[y - d.cap_mwp_min / 1e6, d.cap_mwp_max / 1e6 - y], fmt="none",
                    ecolor="black", elinewidth=0.6, capsize=1.5)
        for rule, mk in (("none", "^"), ("le10", "v")):
            s = t[(t.config == cfg) & (t.slope_rule == rule)].set_index("thr").loc[thrs]
            ax.plot(x, s.cap_mwp_median / 1e6, mk, ms=2.5, mfc="white", mec="black", mew=0.5,
                    label={"none": "No slope limit", "le10": "Slope ≤ 10%"}[rule] if j == 0 else None)
    ax.set_xticks(np.arange(len(thrs)))
    ax.set_xticklabels([f"RY ≥ {x:.2f}" for x in thrs])
    ax.set_ylabel("Capacity (TWp)")
    ax.legend(fontsize=6, loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=3)
    save(fig, out / f"fig_india_capacity_{stage}")
    plt.close(fig)


def fig_states(pp, stage, thr, out, top=12):
    t = pd.read_csv(pp / f"state_combined_{stage}.csv")
    t = t[(t.thr.round(2) == thr) & (t.slope_rule == "le5")]
    order = t.groupby("state").cap_mwp_median.max().sort_values().index[-top:]
    fig, ax = plt.subplots(figsize=(3.5, 3.4), constrained_layout=True)
    h = 0.27
    for j, (cfg, ll) in enumerate(LAYOUTS):
        d = t[t.config == cfg].set_index("state").reindex(order)
        y = np.arange(len(order)) + (1 - j) * h
        v = d.cap_mwp_median / 1e6
        ax.barh(y, v, h * 0.92, color=OI[cfg], label=ll, edgecolor="none")
        ax.errorbar(v, y, xerr=[v - d.cap_mwp_min / 1e6, d.cap_mwp_max / 1e6 - v], fmt="none",
                    ecolor="black", elinewidth=0.5, capsize=1)
    ax.set_yticks(np.arange(len(order)))
    ax.set_yticklabels(order)
    ax.set_xlabel(f"Capacity at RY ≥ {thr:.2f} (TWp)")
    ax.legend(fontsize=6, loc="lower right")
    save(fig, out / f"fig_india_states_{stage}_thr{int(thr * 100)}")
    plt.close(fig)


def fig_delta(pp, hist, fut, grid, states, thr, out):
    a = pd.read_csv(pp / f"map_gcr_{hist}.csv.gz")
    b = pd.read_csv(pp / f"map_gcr_{fut}.csv.gz")
    k = ["cell", "crop", "config", "thr"]
    m = a.merge(b[k + ["gcr_med"]], on=k, suffixes=("_h", "_f"))
    m = m[(m.thr.round(2) == thr) & (m.elig_ha >= MIN_HA)]
    m["d"] = m.gcr_med_f - m.gcr_med_h
    bounds = [-0.3, -0.2, -0.1, -0.025, 0.025, 0.1, 0.2, 0.3]
    cols = mpl.colormaps["PuOr"](np.linspace(0.05, 0.95, len(bounds) + 1))
    cols[len(cols) // 2] = mpl.colors.to_rgba("0.85")   # no-change class grey, so it differs from no data
    cmap = ListedColormap(cols[1:-1]).with_extremes(under=cols[0], over=cols[-1])
    norm = BoundaryNorm(bounds, cmap.N)
    fig, axs = plt.subplots(4, 3, figsize=(6.3, 8.6), constrained_layout=True)
    for i, (crop, cl) in enumerate(CROPS):
        for j, (cfg, ll) in enumerate(LAYOUTS):
            ax = axs[i, j]
            d = m[(m.crop == crop) & (m.config == cfg)]
            pm = draw_cells(ax, *raster(d, grid, "d"), cmap, norm)
            india_axes(ax, states, i == 3, j == 0)
            if i == 0:
                ax.set_title(ll, fontsize=8)
            if j == 0:
                ax.text(-0.38, 0.5, cl, transform=ax.transAxes, rotation=90, va="center", fontsize=8)
            panel_label(ax, "ABCDEFGHIJKL"[3 * i + j])
    cb = fig.colorbar(pm, ax=axs, orientation="horizontal", shrink=0.5, aspect=35, pad=0.01, extend="both")
    cb.set_ticks([-0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3], labels=["−0.3", "−0.2", "−0.1", "0", "0.1", "0.2", "0.3"])
    cb.ax.tick_params(labelsize=7)
    cb.set_label(f"Change in maximum GCR at RY ≥ {thr:.2f}, 2041–2060 minus 1995–2014 (–)", fontsize=8)
    save(fig, out / f"fig_india_delta_{fut}_thr{int(thr * 100)}")
    plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pp", required=True, type=Path)
    ap.add_argument("--stage", required=True)
    ap.add_argument("--grid", required=True)
    ap.add_argument("--boundaries", required=True)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--thr", type=float, default=0.8)
    ap.add_argument("--future", nargs="*", default=[])
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    grid = pd.read_csv(a.grid)
    states = gpd.read_file(a.boundaries)
    warnings.filterwarnings("ignore", message="Geometry is in a geographic CRS")
    # outline only for orientation: close the narrow channels between delta islands (Sundarbans) and
    # between islets, and simplify (~2 km), else they draw as dark blobs and bloat the PDF. All states and
    # union territories stay, including the Andaman & Nicobar Islands and Lakshadweep.
    states["geometry"] = states.geometry.buffer(0.03).buffer(-0.03).simplify(0.02, preserve_topology=True)
    fig_gcrmax(a.pp, a.stage, grid, states, a.thr, a.out)
    fig_capacity(a.pp, a.stage, a.out)
    fig_states(a.pp, a.stage, a.thr, a.out)
    for f in a.future:
        fig_delta(a.pp, a.stage, f, grid, states, a.thr, a.out)
    print("figures in", a.out)
