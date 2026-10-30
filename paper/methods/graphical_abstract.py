"""Graphical abstract (Elsevier spec: landscape 5:2, 13 x 5.2 cm, >= 1328 x 531 px).

Three panels, left to right: problem (solar vs farmland), method (light model + crop model,
yield threshold) and result (India map of GCR_max at RY >= tau with the headline capacity).

Result panel is filled from postprocess_india.py outputs when they exist:
  <pp>/map_gcr_<stage>.csv.gz        cell GCR_max (5-GCM median), per crop and layout
  <pp>/india_combined_<stage>.csv    India capacity (crops combined), median and GCM range
Cell value = GCR_max averaged over crops, weighted by eligible area (slope <= 5%).
Headline = crops-combined capacity, slope <= 5%, same layout and tau.
Without these files the map and numbers are drawn as marked placeholders.

Usage (from paper/methods):
  python graphical_abstract.py [--pp ../../results/potential] [--stage historical_current]
                               [--config ew_fixed] [--thr 0.8]
Writes graphical_abstract.pdf and graphical_abstract.png (600 dpi, 3071 x 1228 px).
"""
import argparse
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7, "pdf.fonttype": 42,
                     "axes.linewidth": 0.6, "xtick.direction": "out", "ytick.direction": "out"})
BLUE, SKY, GREEN, ORANGE, VERM, YEL = "#0072B2", "#56B4E9", "#009E73", "#E69F00", "#D55E00", "#F0E442"
SOIL, GREY = "#C9B79C", "0.25"
LAYOUT_NAME = {"ew_fixed": "east-west", "south_fixed": "south-facing", "vertical": "vertical"}
MIN_HA = 1000      # same blank rule as fig_india.py
CM = 1 / 2.54
W, H = 13.0, 5.2   # cm; drawing units below are mm (0-130 x 0-52)


def parse():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pp", type=Path, default=ROOT / "results" / "potential")
    ap.add_argument("--stage", default="historical_current")
    ap.add_argument("--config", default="ew_fixed", choices=list(LAYOUT_NAME))
    ap.add_argument("--thr", type=float, default=0.8)
    ap.add_argument("--grid", type=Path, default=ROOT / "data" / "grid_india_025.csv")
    ap.add_argument("--boundaries", type=Path, default=ROOT / "data" / "boundaries" / "Admin2.shp")
    ap.add_argument("--out", type=Path, default=HERE / "graphical_abstract")
    return ap.parse_args()


def load_results(a):
    """Cell map and headline capacity, or None where the files are missing."""
    fm, fi = a.pp / f"map_gcr_{a.stage}.csv.gz", a.pp / f"india_combined_{a.stage}.csv"
    cells = head = None
    if fm.exists():
        m = pd.read_csv(fm)
        m = m[(m.config == a.config) & (m.thr.round(2) == round(a.thr, 2)) & (m.elig_ha > 0)]
        m = m.groupby("cell").apply(lambda d: pd.Series({
            "gcr": np.average(d.gcr_med, weights=d.elig_ha), "ha": d.elig_ha.sum()}), include_groups=False)
        m = m[m.ha >= MIN_HA]
        g = pd.read_csv(a.grid).set_index("cell_id").loc[m.index]
        cells = (g.lon.values, g.lat.values, m.gcr.values)
    if fi.exists():
        t = pd.read_csv(fi)
        t = t[(t.config == a.config) & (t.thr.round(2) == round(a.thr, 2)) & (t.slope_rule == "le5")]
        if len(t):
            r = t.iloc[0]
            head = (r.cap_mwp_median, r.cap_mwp_min, r.cap_mwp_max)
    return cells, head


def fmt_cap(head):
    if head is None:
        return "[X] GWp", "range [X]–[X] GWp"
    med, lo, hi = head
    if med >= 1e6:  # MWp -> TWp
        return f"{med / 1e6:.1f} TWp", f"range {lo / 1e6:.1f}–{hi / 1e6:.1f} TWp"
    return f"{med / 1e3:.0f} GWp", f"range {lo / 1e3:.0f}–{hi / 1e3:.0f} GWp"


def main():
    a = parse()
    cells, head = load_results(a)
    fig = plt.figure(figsize=(W * CM, H * CM))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 130); ax.set_ylim(0, 52); ax.axis("off")

    def inset(x, y, w, h):
        b = fig.add_axes([x / 130, y / 52, w / 130, h / 52]); b.set_facecolor("none")
        for s in b.spines.values():
            s.set_visible(False)
        b.set_xticks([]); b.set_yticks([])
        return b

    def sun(b, x, y, r, n=8, ray=0.9):
        b.add_patch(Circle((x, y), r, color=ORANGE, lw=0))
        for k in range(n):
            t = 2 * np.pi * k / n
            b.plot([x + 1.35 * r * np.cos(t), x + (1.35 * r + ray) * np.cos(t)],
                   [y + 1.35 * r * np.sin(t), y + (1.35 * r + ray) * np.sin(t)], color=ORANGE, lw=0.8)

    def plant(b, x, y0, h, c=GREEN, lw=0.9):
        b.plot([x, x], [y0, y0 + h], color=c, lw=lw, solid_capstyle="round")
        for f, s in ((0.45, 1), (0.7, -1)):
            b.plot([x, x + s * 0.35 * h], [y0 + f * h, y0 + (f + 0.2) * h], color=c, lw=lw, solid_capstyle="round")

    # panel frames, titles and arrows between panels
    px = [(1.5, 38.5), (44.5, 41.5), (91.5, 37.0)]
    titles = [("Problem", "Solar or food on one field?"), ("Method", "Shade the crop, keep the yield"),
              ("Result", "Where agrivoltaics fit in India")]
    for (x, w), (t, s) in zip(px, titles):
        ax.add_patch(FancyBboxPatch((x, 1.5), w, 49, boxstyle="round,pad=0,rounding_size=2", fc="white",
                                    ec="0.6", lw=0.6))
        ax.text(x + 2.2, 47.3, t, fontsize=9, fontweight="bold", va="center")
        ax.text(x + 2.2, 42.9, s, fontsize=6.5, color="0.2", va="center")
    for x0, x1 in ((40.3, 44.2), (86.3, 91.2)):
        ax.add_patch(FancyArrowPatch((x0, 26), (x1, 26), arrowstyle="-|>", mutation_scale=10, lw=1.4,
                                     color=GREY, shrinkA=0, shrinkB=0))

    # ---- A: problem. Ground-mounted solar (left) against cropland (right)
    b = inset(3, 9, 35.5, 31)
    b.set_xlim(0, 36); b.set_ylim(0, 30)
    b.add_patch(Rectangle((0, 0), 36, 5, color=SOIL, lw=0))
    sun(b, 18, 24, 2.3)
    for k in range(3):     # dense solar rows
        x = 1.2 + 5.2 * k
        b.add_patch(Polygon([[x, 7.6], [x + 4.4, 10.6], [x + 4.4, 11.5], [x, 8.5]], color=BLUE, lw=0))
        b.plot([x + 2.6, x + 2.6], [5, 9.5], color="0.45", lw=0.6)
    for k in range(6):     # crop field
        plant(b, 20.5 + 2.6 * k, 5, 6.5)
    b.plot([17.8, 17.8], [1, 15], color="0.3", lw=0.6, ls=(0, (2, 1.5)))
    b.text(8.6, 2.5, "solar", ha="center", va="center", fontsize=7, color="white", fontweight="bold")
    b.text(27.0, 2.5, "farmland", ha="center", va="center", fontsize=7, color="white", fontweight="bold")
    b.text(18, 17.2, "competing for land", ha="center", va="center", fontsize=6.5, color="0.15")
    ax.text(20.7, 5.4, "Agrivoltaics: panels above crops", ha="center", va="center", fontsize=6,
            color=BLUE, fontweight="bold")

    # ---- B: method. Light model + crop model -> relative yield vs GCR, threshold tau
    b = inset(46, 26.5, 16.5, 14)        # light model sketch
    b.set_xlim(0, 10); b.set_ylim(0, 8.5)
    sun(b, 8.6, 7.4, 0.55, ray=0.4)
    b.add_patch(Rectangle((0, 0), 10, 0.8, color=SOIL, lw=0))
    for x in (0.7, 5.6):
        b.plot([x, x + 2.6], [3.8, 4.9], color=BLUE, lw=2.2, solid_capstyle="butt")
        b.plot([x + 1.3, x + 1.3], [0.8, 4.3], color="0.45", lw=0.6)
    for x in (3.4, 5.0):
        b.annotate("", (x - 1.6, 1.2), (x + 1.2, 6.8), arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=0.7,
                                                                        mutation_scale=5))
    for i, x in enumerate(np.linspace(0.6, 9.4, 9)):
        plant(b, x, 0.8, 1.4 + 0.5 * np.sin(i), lw=0.7)
    ax.text(54.2, 25.0, "light model", ha="center", va="center", fontsize=6.5)
    ax.text(63.8, 33.5, "+", ha="center", va="center", fontsize=10, color=GREY, fontweight="bold")
    b = inset(66, 26.5, 18, 14)          # crop model sketch
    b.set_xlim(0, 10); b.set_ylim(0, 8.5)
    b.add_patch(FancyBboxPatch((0.6, 1.0), 8.8, 6.6, boxstyle="round,pad=0,rounding_size=0.8", fc="#E3F3EE",
                               ec=GREEN, lw=0.8))
    for i, x in enumerate((2.6, 5.0, 7.4)):
        plant(b, x, 1.9, 3.2 + 0.6 * i, lw=1.0)
    b.text(5, 6.6, "DSSAT", ha="center", va="center", fontsize=6.5, color=GREEN, fontweight="bold")
    ax.text(75, 25.0, "crop model", ha="center", va="center", fontsize=6.5)

    b = fig.add_axes([54.5 / 130, 9.0 / 52, 29 / 130, 13 / 52])   # RY-GCR curve, L-frame axes
    g = np.linspace(0, 0.7, 60); ry = 1 - 0.45 * g - 0.45 * g ** 2
    gm = g[np.argmin(abs(ry - a.thr))]
    b.fill_between(g[g <= gm], 0.4, ry[g <= gm], color=SKY, alpha=0.35, lw=0)
    b.plot(g, ry, color=VERM, lw=1.3)
    b.axhline(a.thr, color="0.2", lw=0.6, ls="--")
    b.plot([gm, gm], [0.4, a.thr], color="0.2", lw=0.6, ls="--")
    b.plot(gm, a.thr, "o", ms=3, color="0.1")
    b.text(0.70, a.thr + 0.03, f"yield limit {a.thr:.1f}", ha="right", va="bottom", fontsize=6)
    b.text(gm + 0.02, 0.45, "GCR$_{max}$", fontsize=6.5, va="bottom")
    b.set_xlim(0, 0.72); b.set_ylim(0.4, 1.05)
    b.set_xticks([0, 0.35, 0.7], ["0", "0.35", "0.7"]); b.set_yticks([0.5, 1.0], ["0.5", "1"])
    b.tick_params(labelsize=6, length=2, width=0.5, pad=1)
    for s in ("top", "right"):
        b.spines[s].set_visible(False)
    b.set_xlabel("panel cover (GCR) [–]", fontsize=6.5, labelpad=1)
    b.set_ylabel("rel. yield [–]", fontsize=6.5, labelpad=1)

    # ---- C: result. India map of GCR_max at RY >= tau, headline capacity
    b = inset(92.5, 2.5, 22.5, 39)
    states = gpd.read_file(a.boundaries)
    india = states.dissolve().simplify(0.03)
    bounds = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7001]
    cmap = ListedColormap(plt.colormaps["viridis"](np.linspace(0, 1, len(bounds) - 1)))
    norm = BoundaryNorm(bounds, cmap.N)
    if cells is None:
        india.plot(ax=b, color="0.88", edgecolor="0.4", lw=0.4, hatch="////")
        b.text(82, 22, "[PLACEHOLDER]\nGCR$_{max}$ map\nfills from\nresults/potential", ha="center",
               va="center", fontsize=5.5, color="0.1",
               bbox=dict(boxstyle="square,pad=0.3", fc="white", ec="0.1", lw=0.5, ls="--"))
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
    cb_ax = fig.add_axes([119.5 / 130, 15.0 / 52, 1.6 / 130, 20 / 52])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cb_ax, ticks=[0, 0.35, 0.7])
    cb.ax.set_yticklabels(["0", "0.35", "0.7"]); cb.ax.tick_params(labelsize=6, length=1.5, width=0.5, pad=1)
    cb.outline.set_linewidth(0.5)
    ax.text(120.3, 36.6, "GCR$_{max}$", ha="center", va="bottom", fontsize=6.5)
    big, rng = fmt_cap(head)
    ax.text(127.0, 4.4, big, ha="right", va="bottom", fontsize=10, fontweight="bold", color=BLUE)
    ax.text(127.0, 2.6, f"{LAYOUT_NAME[a.config]}, RY ≥ {a.thr:.1f}", ha="right", va="bottom", fontsize=5.5,
            color="0.2")
    if head is None:
        ax.add_patch(Rectangle((107.0, 2.0), 21.0, 7.6, fill=False, ec="0.1", lw=0.5, ls="--"))

    a.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out.with_suffix(".pdf"))
    fig.savefig(a.out.with_suffix(".png"), dpi=600)
    print("wrote", a.out.with_suffix(".pdf"), "map:", "filled" if cells else "placeholder",
          "| headline:", big, rng)


if __name__ == "__main__":
    main()
