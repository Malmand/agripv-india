"""Journal figures for the India APV potential (reads postprocess_india.py outputs).

  fig_india_gcrmax_<stage>.pdf      map: GCR_max at RY >= thr, crops x layouts (5-GCM median)
  fig_india_capacity_<stage>.pdf    bars: India capacity (GW) by layout and RY threshold,
                                    error bars = range over 5 GCMs; markers = slope-rule cases
  fig_india_cases_<robust>.pdf     bars: capacity and energy, robust (filled) vs calibrated N (outline)
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


def save(fig, stem, png_dpi=300):
    """Journal PDF (map rasters 400 dpi) plus a PNG that the manuscript builder embeds."""
    fig.savefig(f"{stem}.pdf", dpi=400)
    fig.savefig(f"{stem}.png", dpi=png_dpi)


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
    ax.tick_params(labelsize=7.5)
    if not bottom:
        ax.tick_params(axis="x", length=0)
    if not left:
        ax.tick_params(axis="y", length=0)


def raster(d, grid, col):
    g = grid.set_index("cell_id").loc[d.cell]
    return g.lon.values, g.lat.values, d[col].values


CLIP = None      # India outline (shapely geometry); set in main so smoothed cells never spill into sea or neighbours
SMOOTH = 6       # display up-sampling factor of the 0.25 deg cells (bilinear, within the cells that have data)


def geom_path(geom):
    """Matplotlib path of a (multi)polygon, holes included."""
    from matplotlib.path import Path
    polys = list(geom.geoms) if hasattr(geom, "geoms") else [geom]
    verts, codes = [], []
    for pg in polys:
        for ring in [pg.exterior, *pg.interiors]:
            xy = np.asarray(ring.coords)
            verts.extend(xy); codes.extend([Path.MOVETO] + [Path.LINETO] * (len(xy) - 2) + [Path.CLOSEPOLY])
    return Path(verts, codes)


def draw_cells(ax, lon, lat, val, cmap, norm):
    """0.25 deg cells on a full grid. With SMOOTH > 1 the values are interpolated bilinearly, using only cells
    that have data (so blanks do not pull values down), and drawn on a finer mesh clipped to the India outline;
    this is a display choice, the data resolution stays 0.25 deg."""
    from matplotlib.patches import PathPatch
    from scipy.ndimage import zoom
    lons = np.round(np.arange(68.125, 97.5, 0.25), 3)
    lats = np.round(np.arange(6.625, 37.25, 0.25), 3)
    z = np.full((len(lats), len(lons)), np.nan)
    z[np.searchsorted(lats, np.round(lat, 3)), np.searchsorted(lons, np.round(lon, 3))] = val
    xe = np.append(lons - 0.125, lons[-1] + 0.125); ye = np.append(lats - 0.125, lats[-1] + 0.125)
    if SMOOTH > 1:
        ok = np.isfinite(z)
        zz = zoom(np.where(ok, z, 0.0), SMOOTH, order=1, grid_mode=True, mode="nearest")
        ww = zoom(ok.astype(float), SMOOTH, order=1, grid_mode=True, mode="nearest")
        from scipy.ndimage import gaussian_filter
        sg = 0.45 * SMOOTH                                  # ~0.45 cell: rounds the stair-steps, keeps the pattern
        zz, ww = gaussian_filter(zz, sg), gaussian_filter(ww, sg)
        z = np.round(np.where(ww >= 0.5, zz / np.maximum(ww, 1e-9), np.nan), 5)   # rounding: capped values sit on class edges
        xe = np.linspace(xe[0], xe[-1], z.shape[1] + 1); ye = np.linspace(ye[0], ye[-1], z.shape[0] + 1)
    pm = ax.pcolormesh(xe, ye, np.ma.masked_invalid(z), cmap=cmap, norm=norm, edgecolors="none", rasterized=True)
    if CLIP is not None:
        pm.set_clip_path(PathPatch(geom_path(CLIP), transform=ax.transData))
    return pm


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
    fig, axs = plt.subplots(4, 3, figsize=(6.3, 8.9), constrained_layout=True)
    fig.get_layout_engine().set(w_pad=0.01, h_pad=0.01, wspace=0.0, hspace=0.0)
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
                ax.text(0.02, 0.01, txt, transform=ax.transAxes, ha="left", va="bottom", fontsize=7)
            if i == 0:
                ax.set_title(ll, fontsize=8.5)
            if j == 0:
                ax.text(-0.42, 0.5, cl, transform=ax.transAxes, rotation=90, va="center", fontsize=8.5)
            panel_label(ax, "ABCDEFGHIJKL"[3 * i + j])
    cb = fig.colorbar(pm, ax=axs, orientation="horizontal", shrink=0.6, aspect=35, pad=0.01)
    cb.set_label(f"Maximum ground coverage ratio with relative yield ≥ {thr:.2f} (–)", fontsize=8.5)
    cb.ax.tick_params(labelsize=7.5)
    save(fig, out / f"fig_india_gcrmax_{stage}_thr{int(thr * 100)}")
    plt.close(fig)


def fig_capmap(pp, stage, grid, states, thr, out):
    """One large map of the headline result: yield-constrained capacity density (MWp per ha of eligible
    cropland, all crops combined, east-west layout, slope <= 5%), median over the five GCMs, with the three
    leading states labelled and the national total."""
    import matplotlib.patheffects as pe
    c = pd.read_csv(pp / f"cell_combined_{stage}.csv.gz")
    c = c[(c.config == "ew_fixed") & (c.thr.round(2) == thr) & (c.slope_rule == "le5")]
    tot = c.groupby("model").agg(cap=("cap_mwp", "sum"), land=("land_ha", "sum"))     # all cells, as in Table 4
    cap_tw, land_mha = tot.cap.median() / 1e6, tot.land.median() / 1e6
    c = c[c.land_ha >= MIN_HA].assign(dens=lambda x: x.cap_mwp / x.land_ha)           # map: cells with >= 1000 ha
    d = c.groupby("cell").dens.median().rename("v").reset_index()
    st = pd.read_csv(pp / f"state_combined_{stage}.csv")
    st = st[(st.thr.round(2) == thr) & (st.slope_rule == "le5") & (st.config == "ew_fixed")]
    top = st.sort_values("cap_mwp_median", ascending=False).head(3)
    bounds = np.round(np.arange(0, 1.61, 0.2), 2)
    cmap = ListedColormap(mpl.colormaps["viridis"](np.linspace(0, 1, len(bounds) - 1)))
    norm = BoundaryNorm(bounds, cmap.N)
    fig, ax = plt.subplots(figsize=(6.3, 6.3), constrained_layout=True)
    g = grid.set_index("cell_id").loc[d.cell]
    pm = draw_cells(ax, g.lon.values, g.lat.values, d.v.values, cmap, norm)
    states.boundary.plot(ax=ax, color="0.3", linewidth=0.35)
    ax.set_xlim(68, 97.5); ax.set_ylim(6.5, 37.2)
    ax.set_aspect(1 / np.cos(np.radians(22)))
    ax.set_xlabel(""); ax.set_ylabel("")
    ax.set_xticks([70, 75, 80, 85, 90, 95]); ax.set_yticks([10, 15, 20, 25, 30, 35])
    ax.set_xticklabels([f"{x}°E" for x in (70, 75, 80, 85, 90, 95)])
    ax.set_yticklabels([f"{y}°N" for y in (10, 15, 20, 25, 30, 35)])
    ax.tick_params(labelsize=7.5)
    halo = [pe.withStroke(linewidth=2.2, foreground="white")]
    for r in top.itertuples():
        geom = states[states.ST_NM == r.state].geometry.union_all().representative_point()
        ax.text(geom.x, geom.y, f"{r.state}\n{r.cap_mwp_median / 1e6:.1f} TWp", ha="center", va="center",
                fontsize=7.5, fontweight="bold", path_effects=halo, zorder=6)
    km5 = 500 / (111.32 * np.cos(np.radians(22)))                  # 500 km in degrees of longitude at 22 N
    ax.plot([69.2, 69.2 + km5], [8.3, 8.3], color="black", lw=1.6, solid_capstyle="butt")
    ax.text(69.2 + km5 / 2, 9.0, "500 km", ha="center", va="bottom", fontsize=7.5)
    ax.annotate("", xy=(70.2, 14.6), xytext=(70.2, 11.6), arrowprops=dict(arrowstyle="-|>", color="black", lw=1.0))
    ax.text(70.2, 14.9, "N", ha="center", va="bottom", fontsize=8, fontweight="bold")
    ax.text(0.99, 0.99, f"India: {cap_tw:.1f} TWp on {land_mha:.1f} Mha\n(median of five GCMs)", transform=ax.transAxes,
            ha="right", va="top", fontsize=8, fontweight="bold", path_effects=halo)
    cb = fig.colorbar(pm, ax=ax, shrink=0.62, aspect=26, pad=0.02)
    cb.set_label("Capacity density (MWp per ha of cropland)", fontsize=8.5)
    cb.ax.tick_params(labelsize=7.5)
    save(fig, out / f"fig_india_capmap_{stage}_thr{int(thr * 100)}", png_dpi=400)
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


def fig_cases(pp, calib, robust, out):
    """Capacity (A) and annual energy (B) by layout and RY threshold: robust case as filled bars with the
    GCM range, calibrated-nitrogen upper bound as an outline bar behind it (slope <= 5%)."""
    tc = pd.read_csv(pp / f"india_combined_{calib}.csv")
    tr = pd.read_csv(pp / f"india_combined_{robust}.csv")
    thrs = sorted(tr.thr.unique())
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9), constrained_layout=True)
    w = 0.26
    for ax, (col, scale, ylab, lab) in zip(axes, (("cap_mwp", 1e6, "Capacity (TWp)", "A"),
                                                  ("energy_gwh", 1e6, "Annual energy (PWh yr$^{-1}$)", "B"))):
        for j, (cfg, ll) in enumerate(LAYOUTS):
            x = np.arange(len(thrs)) + (j - 1) * w
            dc = tc[(tc.config == cfg) & (tc.slope_rule == "le5")].set_index("thr").loc[thrs]
            dr = tr[(tr.config == cfg) & (tr.slope_rule == "le5")].set_index("thr").loc[thrs]
            ax.bar(x, dc[f"{col}_median"] / scale, w * 0.92, facecolor="white", edgecolor=OI[cfg], linewidth=0.8,
                   label=None)
            y = dr[f"{col}_median"] / scale
            ax.bar(x, y, w * 0.92, color=OI[cfg], edgecolor="none", label=ll)
            ax.errorbar(x, y, yerr=[y - dr[f"{col}_min"] / scale, dr[f"{col}_max"] / scale - y], fmt="none",
                        ecolor="black", elinewidth=0.6, capsize=1.5)
        ax.set_xticks(np.arange(len(thrs)))
        ax.set_xticklabels([f"RY ≥ {x:.2f}" for x in thrs])
        ax.set_ylabel(ylab, fontsize=8)
        ax.text(-0.16, 1.02, lab, transform=ax.transAxes, fontsize=11, fontweight="bold", va="bottom")
    h, l = axes[0].get_legend_handles_labels()
    h.append(mpl.patches.Patch(facecolor="white", edgecolor="black", linewidth=0.8))
    l.append("Outline: calibrated N (upper bound)")
    fig.legend(h, l, fontsize=6.5, loc="outside lower center", ncol=4)
    save(fig, out / f"fig_india_cases_{robust}")
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
    ap.add_argument("--calib", help="calibrated stage: with a robust --stage, also draw fig_india_cases_<stage>")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    grid = pd.read_csv(a.grid)
    states = gpd.read_file(a.boundaries)
    warnings.filterwarnings("ignore", message="Geometry is in a geographic CRS")
    # outline only for orientation: close the narrow channels between delta islands (Sundarbans) and
    # between islets, and simplify (~2 km), else they draw as dark blobs and bloat the PDF. All states and
    # union territories stay, including the Andaman & Nicobar Islands and Lakshadweep.
    states["geometry"] = states.geometry.buffer(0.03).buffer(-0.03).simplify(0.02, preserve_topology=True)
    CLIP = states.geometry.union_all().buffer(0.02)
    fig_gcrmax(a.pp, a.stage, grid, states, a.thr, a.out)
    fig_capmap(a.pp, a.stage, grid, states, a.thr, a.out)
    fig_capacity(a.pp, a.stage, a.out)
    fig_states(a.pp, a.stage, a.thr, a.out)
    if a.calib:
        fig_cases(a.pp, a.calib, a.stage, a.out)
    for f in a.future:
        fig_delta(a.pp, a.stage, f, grid, states, a.thr, a.out)
    print("figures in", a.out)
