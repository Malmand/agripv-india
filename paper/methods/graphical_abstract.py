"""Graphical abstract (Elsevier spec: readable at 13 x 5 cm, >= 1328 x 531 px).

Three panels, left to right, with the result taking about half the width:
  problem  small sketch, solar and farmland competing for land
  method   icon row (shade model -> crop model), one RY-vs-GCR curve with tau and GCR_max, simulation scope
  result   India map of GCR_max at RY >= tau, headline capacity, mid-century change badge and a row of
           four crop icons with the national mean GCR_max of each crop

Result panel is filled from postprocess_india.py outputs when they exist:
  <pp>/map_gcr_<stage>.csv.gz        cell GCR_max (5-GCM median), per crop and layout
  <pp>/india_combined_<stage>.csv    India capacity (crops combined), median and GCM range
  <pp>/india_combined_<future>.csv   same for the mid-century run (2050 badge = change of the median;
                                     default SSP5-8.5)
Map, crop values and headline use the robust case (<stage>_robust files) when it exists.
Map cell value = GCR_max averaged over crops, weighted by eligible area (slope <= 5%).
Crop value = GCR_max of that crop averaged over cells, weighted by eligible area.
Headline = crops-combined capacity, slope <= 5%, same layout and tau. It is the robust case
(<pp>/india_combined_<stage>_robust.csv, min of calibrated and recommended N) when that file exists;
otherwise the calibrated-N value is shown and labelled "upper bound".
Without these files the map and numbers are drawn as marked placeholders ([X]).

Usage (from paper/methods):
  python graphical_abstract.py [--pp ../../results/potential] [--stage historical_current]
                               [--future ssp585_current] [--config ew_fixed] [--thr 0.8]
Writes graphical_abstract.pdf and graphical_abstract.png (600 dpi, 3071 x 1181 px).
All text is >= 7 pt at the final 13 x 5 cm size.
"""
import argparse
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7, "pdf.fonttype": 42,
                     "axes.linewidth": 0.6, "xtick.direction": "out", "ytick.direction": "out"})
BLUE, SKY, GREEN, ORANGE, VERM = "#0072B2", "#56B4E9", "#009E73", "#E69F00", "#D55E00"
SOIL, GREY = "#C9B79C", "0.25"
LAYOUT_NAME = {"ew_fixed": "east-west", "south_fixed": "south-facing", "vertical": "vertical"}
CROPS = [("wheat", "wheat"), ("chickpea", "chickpea"), ("pearl_millet", "pearl millet"), ("groundnut", "groundnut")]
MIN_HA = 1000      # same blank rule as fig_india.py
CM = 1 / 2.54
W, H = 130, 50     # mm; the base axes use mm units, so 1 x unit = 1 y unit


def parse():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pp", type=Path, default=ROOT / "results" / "potential")
    ap.add_argument("--stage", default="historical_current")
    ap.add_argument("--future", default="ssp585_current", help="mid-century stage for the 2050 badge")
    ap.add_argument("--config", default="ew_fixed", choices=list(LAYOUT_NAME))
    ap.add_argument("--thr", type=float, default=0.8)
    ap.add_argument("--grid", type=Path, default=ROOT / "data" / "grid_india_025.csv")
    ap.add_argument("--boundaries", type=Path, default=ROOT / "data" / "boundaries" / "Admin2.shp")
    ap.add_argument("--out", type=Path, default=HERE / "graphical_abstract")
    return ap.parse_args()


def headline(a, stage):
    f = a.pp / f"india_combined_{stage}.csv"
    if not f.exists():
        return None
    t = pd.read_csv(f)
    t = t[(t.config == a.config) & (t.thr.round(2) == round(a.thr, 2)) & (t.slope_rule == "le5")]
    if not len(t):
        return None
    r = t.iloc[0]
    return r.cap_mwp_median, r.cap_mwp_min, r.cap_mwp_max


def load_results(a):
    """Cell map, per-crop mean GCR_max, headline capacity and 2050 change; None where files are missing."""
    # map and crop values from the robust case when it exists (same case as the headline)
    fm = a.pp / f"map_gcr_{a.stage}_robust.csv.gz"
    if not fm.exists():
        fm = a.pp / f"map_gcr_{a.stage}.csv.gz"
    cells, crop = None, {}
    if fm.exists():
        m = pd.read_csv(fm)
        m = m[(m.config == a.config) & (m.thr.round(2) == round(a.thr, 2)) & (m.elig_ha > 0)]
        crop = {c: np.average(d.gcr_med, weights=d.elig_ha) for c, d in m.groupby("crop")}
        m = m.groupby("cell").apply(lambda d: pd.Series({
            "gcr": np.average(d.gcr_med, weights=d.elig_ha), "ha": d.elig_ha.sum()}), include_groups=False)
        m = m[m.ha >= MIN_HA]
        g = pd.read_csv(a.grid).set_index("cell_id").loc[m.index]
        cells = (g.lon.values, g.lat.values, m.gcr.values)
    base, fut = headline(a, a.stage), headline(a, a.future)
    rob = headline(a, f"{a.stage}_robust")
    head, label = (rob, "robust estimate") if rob is not None else (base, "upper bound")
    # 2050 badge: change of the calibrated-N median (the future stages are run with calibrated N)
    change = None if base is None or fut is None else 100 * (fut[0] / base[0] - 1)
    return cells, crop, head, change, label


def fmt_cap(head):
    if head is None:
        return "[X] GWp", "GCM range [X]–[X]"
    med, lo, hi = head
    if med >= 1e6:  # MWp -> TWp; two decimals in the range if one would hide it
        nd = 1 if round(lo / 1e6, 1) != round(hi / 1e6, 1) else 2
        return f"{med / 1e6:.1f} TWp", f"GCM range {lo / 1e6:.{nd}f}–{hi / 1e6:.{nd}f}"
    return f"{med / 1e3:.0f} GWp", f"GCM range {lo / 1e3:.0f}–{hi / 1e3:.0f}"


# ---- drawing helpers, all in mm on the base axes
def sun(ax, x, y, r, n=8, ray=0.8):
    ax.add_patch(Circle((x, y), r, color=ORANGE, lw=0))
    for k in range(n):
        t = 2 * np.pi * k / n
        ax.plot([x + 1.35 * r * np.cos(t), x + (1.35 * r + ray) * np.cos(t)],
                [y + 1.35 * r * np.sin(t), y + (1.35 * r + ray) * np.sin(t)], color=ORANGE, lw=0.8)


def sprout(ax, x, y0, h, lw=0.9):
    ax.plot([x, x], [y0, y0 + h], color=GREEN, lw=lw, solid_capstyle="round")
    for f, s in ((0.45, 1), (0.7, -1)):
        ax.plot([x, x + s * 0.35 * h], [y0 + f * h, y0 + (f + 0.2) * h], color=GREEN, lw=lw,
                solid_capstyle="round")


def leaf(ax, x, y, dx, dy, lw=0.9):
    """Curved leaf from (x, y) towards (x + dx, y + dy)."""
    t = np.linspace(0, 1, 12)
    ax.plot(x + dx * t, y + dy * t + 0.6 * dy * t * (1 - t), color=GREEN,
            lw=lw, solid_capstyle="round")


# Crop icons share one style: green stem and leaves, orange harvested part, height h from (cx, y0).
def icon_wheat(ax, cx, y0, h):
    ax.plot([cx, cx], [y0, y0 + 0.62 * h], color=GREEN, lw=0.9, solid_capstyle="round")
    leaf(ax, cx, y0 + 0.2 * h, 0.28 * h, 0.25 * h); leaf(ax, cx, y0 + 0.32 * h, -0.28 * h, 0.22 * h)
    for k in range(4):          # ear: paired grains
        y = y0 + (0.62 + 0.09 * k) * h
        for s in (-1, 1):
            ax.add_patch(Ellipse((cx + s * 0.07 * h, y), 0.1 * h, 0.16 * h, angle=-s * 30, color=ORANGE, lw=0))
    ax.add_patch(Ellipse((cx, y0 + 0.97 * h), 0.08 * h, 0.13 * h, color=ORANGE, lw=0))


def icon_chickpea(ax, cx, y0, h):
    ax.plot([cx, cx], [y0, y0 + 0.75 * h], color=GREEN, lw=0.9, solid_capstyle="round")
    for f, s in ((0.3, -1), (0.48, 1), (0.66, -1)):      # side branches with small round leaflets
        y = y0 + f * h
        ax.plot([cx, cx + s * 0.3 * h], [y, y + 0.12 * h], color=GREEN, lw=0.7, solid_capstyle="round")
        for u in (0.45, 0.8):
            ax.add_patch(Circle((cx + s * u * 0.3 * h, y + u * 0.12 * h + 0.05 * h), 0.045 * h, color=GREEN, lw=0))
    for y in (0.8, 0.9):
        ax.add_patch(Circle((cx + (0.05 if y == 0.8 else -0.05) * h, y0 + y * h), 0.045 * h, color=GREEN, lw=0))
    ax.add_patch(Ellipse((cx + 0.22 * h, y0 + 0.32 * h), 0.2 * h, 0.15 * h, angle=20, color=ORANGE, lw=0))
    ax.plot([cx, cx + 0.15 * h], [y0 + 0.4 * h, y0 + 0.36 * h], color=GREEN, lw=0.6)


def icon_millet(ax, cx, y0, h):
    ax.plot([cx, cx], [y0, y0 + 0.62 * h], color=GREEN, lw=0.9, solid_capstyle="round")
    leaf(ax, cx, y0 + 0.15 * h, 0.34 * h, 0.35 * h); leaf(ax, cx, y0 + 0.3 * h, -0.34 * h, 0.3 * h)
    ax.add_patch(FancyBboxPatch((cx - 0.075 * h, y0 + 0.6 * h), 0.15 * h, 0.4 * h,
                                boxstyle=f"round,pad=0,rounding_size={0.07 * h}", fc=ORANGE, ec="none"))


def icon_groundnut(ax, cx, y0, h):
    gy = y0 + 0.4 * h                                    # soil surface
    ax.add_patch(Rectangle((cx - 0.4 * h, y0), 0.8 * h, 0.4 * h, color=SOIL, lw=0))
    ax.plot([cx, cx], [gy, gy + 0.42 * h], color=GREEN, lw=0.9, solid_capstyle="round")
    for dx, y in ((-0.17, 0.3), (0.17, 0.3), (0, 0.5)):   # leaves: pairs of ovals
        x = cx + dx * h
        ax.plot([cx, x], [gy + (y - 0.12) * h, gy + y * h], color=GREEN, lw=0.6)
        for s in (-1, 1):
            ax.add_patch(Ellipse((x + s * 0.05 * h, gy + y * h), 0.09 * h, 0.13 * h, angle=s * 25, color=GREEN, lw=0))
    for dx in (-0.2, 0.18):                              # pegs and pods under ground
        ax.plot([cx, cx + dx * h], [gy, y0 + 0.18 * h], color=GREEN, lw=0.6)
        ax.add_patch(Ellipse((cx + dx * h, y0 + 0.13 * h), 0.24 * h, 0.12 * h, angle=10, color=ORANGE, lw=0))


def icon_shade(ax, cx, y0, h):
    """Shade model: sun ray hitting a tilted panel, shadow on the ground."""
    ax.add_patch(Rectangle((cx - 0.55 * h, y0), 1.1 * h, 0.14 * h, color=SOIL, lw=0))
    ax.add_patch(Rectangle((cx - 0.05 * h, y0), 0.6 * h, 0.14 * h, color="0.55", lw=0))
    ax.plot([cx - 0.15 * h, cx + 0.45 * h], [y0 + 0.5 * h, y0 + 0.72 * h], color=BLUE, lw=1.6, solid_capstyle="butt")
    ax.plot([cx + 0.15 * h, cx + 0.15 * h], [y0 + 0.14 * h, y0 + 0.6 * h], color="0.45", lw=0.5)
    ax.add_patch(Circle((cx - 0.4 * h, y0 + 0.85 * h), 0.13 * h, color=ORANGE, lw=0))
    ax.annotate("", (cx - 0.25 * h, y0 + 0.2 * h), (cx - 0.33 * h, y0 + 0.68 * h),
                arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=0.6, mutation_scale=4))


def icon_cropmodel(ax, cx, y0, h):
    """Crop model: a plant inside a model box."""
    ax.add_patch(FancyBboxPatch((cx - 0.5 * h, y0), h, h, boxstyle=f"round,pad=0,rounding_size={0.15 * h}",
                                fc="#E3F3EE", ec=GREEN, lw=0.7))
    sprout(ax, cx, y0 + 0.12 * h, 0.72 * h, lw=0.8)


ICONS = {"wheat": icon_wheat, "chickpea": icon_chickpea, "pearl_millet": icon_millet, "groundnut": icon_groundnut}


def main():
    a = parse()
    cells, crop, head, change, hlabel = load_results(a)
    fig = plt.figure(figsize=(W / 10 * CM, H / 10 * CM))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")

    def axes_mm(x, y, w, h):
        return fig.add_axes([x / W, y / H, w / W, h / H])

    # panel frames, titles and arrows between panels
    panels = [(1.0, 16.4, "Solar vs\nfood on\nfarmland"), (19.6, 45.3, "Simulate shade → yield"),
              (67.1, 61.9, f"Where agrivoltaics keeps ≥ {a.thr:.0%} yield")]
    for x, w, t in panels:
        ax.add_patch(FancyBboxPatch((x, 1.0), w, 48, boxstyle="round,pad=0,rounding_size=1.8", fc="white",
                                    ec="0.6", lw=0.6))
        ax.text(x + w / 2, 47.4, t, fontsize=8, fontweight="bold", ha="center", va="top", linespacing=1.15,
                multialignment="center")
    for x0, x1 in ((17.5, 19.5), (65.0, 67.0)):
        ax.add_patch(FancyArrowPatch((x0, 25), (x1, 25), arrowstyle="-|>", mutation_scale=8, lw=1.2,
                                     color=GREY, shrinkA=0, shrinkB=0))

    # ---- problem: solar rows and crops competing for the same land
    gy = 9.0
    ax.add_patch(Rectangle((2.1, gy - 3.0), 14.2, 3.0, color=SOIL, lw=0))
    sun(ax, 9.2, 27.0, 1.8)
    for k in range(2):
        x = 2.5 + 3.1 * k
        ax.add_patch(Polygon([[x, gy + 2.6], [x + 2.7, gy + 4.4], [x + 2.7, gy + 5.2], [x, gy + 3.4]], color=BLUE, lw=0))
        ax.plot([x + 1.5, x + 1.5], [gy, gy + 3.5], color="0.45", lw=0.6)
    for k in range(4):
        sprout(ax, 10.3 + 1.6 * k, gy, 4.6)
    ax.plot([8.9, 8.9], [gy - 2.5, gy + 9.5], color="0.3", lw=0.6, ls=(0, (2, 1.5)))

    # ---- method: one RY-GCR curve with tau and GCR_max
    # icon row: shade model -> crop model, each icon centred above its label
    for cx, label, icon in ((34.5, "shade model", icon_shade), (53.0, "crop model", icon_cropmodel)):
        icon(ax, cx, 38.6, 4.0)
        ax.text(cx, 36.4, label, ha="center", va="center", fontsize=7, color="0.15")
    ax.add_patch(FancyArrowPatch((38.6, 40.6), (48.9, 40.6), arrowstyle="-|>", mutation_scale=6, lw=0.9,
                                 color=GREY, shrinkA=0, shrinkB=0))
    ax.text(42.25, 6.0, "every 0.25° cell · 5 climate models", ha="center", va="center", fontsize=7, color="0.2")
    b = axes_mm(33.0, 17.4, 28.0, 16.8)
    g = np.linspace(0, 0.7, 80); ry = 1 - 0.45 * g - 0.45 * g ** 2
    gm = g[np.argmin(abs(ry - a.thr))]
    b.fill_between(g[g <= gm], 0.4, ry[g <= gm], color=SKY, alpha=0.35, lw=0)
    b.plot(g, ry, color=VERM, lw=1.4)
    b.axhline(a.thr, color="0.2", lw=0.6, ls="--")
    b.plot([gm, gm], [0.4, a.thr], color="0.2", lw=0.6, ls="--")
    b.plot(gm, a.thr, "o", ms=3.5, color="0.1", zorder=5)
    b.text(0.71, a.thr + 0.025, f"RY = {a.thr:.1f}", ha="right", va="bottom", fontsize=7)
    b.text(gm + 0.025, 0.43, "GCR$_{max}$", fontsize=7, va="bottom", fontweight="bold")
    b.text(0.03, 0.43, "keeps\nyield", fontsize=7, va="bottom", color=BLUE, linespacing=1.1)
    b.set_xlim(0, 0.72); b.set_ylim(0.4, 1.05)
    b.set_xticks([0, 0.7], ["0", "0.7"]); b.set_yticks([0.4, 0.7, 1.0], ["0.4", "0.7", "1"])
    b.tick_params(labelsize=7, length=2, width=0.5, pad=1)
    for s in ("top", "right"):
        b.spines[s].set_visible(False)
    b.set_xlabel("panel cover, GCR [–]", fontsize=7, labelpad=1)
    b.set_ylabel("rel. yield, RY [–]", fontsize=7, labelpad=1)
    b.yaxis.set_label_coords(-0.21, 0.46)

    # ---- result: India map of GCR_max at RY >= tau
    b = axes_mm(73.0, 14.5, 26.2, 29.5)
    b.set_facecolor("none")
    for s in b.spines.values():
        s.set_visible(False)
    states = gpd.read_file(a.boundaries)
    india = states.dissolve().simplify(0.03)
    bounds = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7001]
    cmap = ListedColormap(plt.colormaps["viridis"](np.linspace(0, 1, len(bounds) - 1)))
    norm = BoundaryNorm(bounds, cmap.N)
    if cells is None:
        india.plot(ax=b, color="0.9", edgecolor="0.4", lw=0.4, hatch="////")
        b.text(80.5, 21.5, "[map]", ha="center", va="center", fontsize=7, color="0.1",
               bbox=dict(boxstyle="square,pad=0.25", fc="white", ec="0.1", lw=0.5, ls="--"))
    else:
        india.plot(ax=b, color="0.93", edgecolor="none")
        lon, lat, v = cells
        lons = np.round(np.arange(68.125, 97.5, 0.25), 3); lats = np.round(np.arange(6.625, 37.25, 0.25), 3)
        z = np.full((len(lats), len(lons)), np.nan)
        z[np.searchsorted(lats, np.round(lat, 3)), np.searchsorted(lons, np.round(lon, 3))] = v
        b.pcolormesh(np.append(lons - 0.125, lons[-1] + 0.125), np.append(lats - 0.125, lats[-1] + 0.125),
                     np.ma.masked_invalid(z), cmap=cmap, norm=norm, edgecolors="none", rasterized=True)
        india.boundary.plot(ax=b, color="0.35", lw=0.4)
    b.set_xlim(68, 97.5); b.set_ylim(6.5, 37.3); b.set_aspect(1 / np.cos(np.radians(22)))
    b.set_xticks([]); b.set_yticks([]); b.set_xlabel(""); b.set_ylabel("")
    cb_ax = axes_mm(70.2, 17.0, 1.5, 20.0)
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cb_ax, ticks=[0, 0.7])
    cb.ax.set_yticklabels(["0", "0.7"]); cb.ax.tick_params(labelsize=7, length=1.5, width=0.5, pad=1)
    cb.outline.set_linewidth(0.5)
    ax.text(68.9, 27.0, "max GCR", ha="center", va="center", fontsize=7, color="0.15", rotation=90)

    # headline capacity and 2050 badge
    big, rng = fmt_cap(head)
    xr = 114.4
    ax.text(xr, 37.0, big, ha="center", va="center", fontsize=15, fontweight="bold", color=BLUE)
    ax.text(xr, 31.0, hlabel, ha="center", va="center", fontsize=9, fontweight="bold", color="black")
    if head is None:
        ax.add_patch(Rectangle((xr - 13.5, 33.5), 27.0, 7.0, fill=False, ec="0.1", lw=0.5, ls="--"))
    # 2050 badge: scenario on the first line, change of the median on the second
    scen = {"ssp585": "SSP5-8.5", "ssp245": "SSP2-4.5"}.get(a.future.split("_")[0], "SSP5-8.5")
    val = "[±X]%" if change is None else f"{change:+.0f}%".replace("-", "−")
    ax.add_patch(FancyBboxPatch((xr - 13.6, 17.6), 27.2, 9.0, boxstyle="round,pad=0,rounding_size=2.5",
                                fc=ORANGE, ec="none"))
    ax.text(xr, 24.2, f"2050 ({scen}):", ha="center", va="center", fontsize=7, fontweight="bold", color="black")
    ax.text(xr, 20.3, val, ha="center", va="center", fontsize=10, fontweight="bold", color="black")

    # crop icons with national mean GCR_max
    for (c, name), cx in zip(CROPS, (73.5, 87.5, 103.0, 120.0)):   # slots sized to the crop names
        ICONS[c](ax, cx - 3.4, 7.6, 6.0)
        ax.text(cx - 0.4, 10.6, "[X]" if c not in crop else f"{crop[c]:.2f}", ha="left", va="center",
                fontsize=8, fontweight="bold", color="0.1")
        ax.text(cx - 1.0, 4.3, name, ha="center", va="center", fontsize=7, color="0.2")

    a.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out.with_suffix(".pdf"))
    fig.savefig(a.out.with_suffix(".png"), dpi=600)
    print("wrote", a.out.with_suffix(".pdf"), "map:", "filled" if cells else "placeholder",
          "| headline:", big, f"({hlabel})", rng, "|", f"2050 ({scen}): {val}", "| crops:", {c: round(v, 2) for c, v in crop.items()})


if __name__ == "__main__":
    main()
