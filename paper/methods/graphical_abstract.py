"""Graphical abstract (Elsevier spec: readable at 13 x 5 cm, >= 1328 x 531 px).

Three panels, left to right, with the result taking about half the width:
  problem  small sketch, solar and farmland competing for land
  method   icon row (shade model -> crop model), one RY-vs-GCR curve with tau and GCR_max, simulation scope
  result   India map of GCR_max at RY >= tau, headline capacity, mid-century change badge and a row of
           four crop icons with the national mean GCR_max of each crop

Result panel is filled from postprocess_india.py outputs when they exist:
  <pp>/map_gcr_<stage>.csv.gz        cell GCR_max (5-GCM median), per crop and layout
  <pp>/india_combined_<stage>.csv    India capacity (crops combined), median and GCM range
  <pp>/numbers.json                  2050 badge: <future>.change_pct, change_lo, change_hi (src/make_numbers.py;
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
import json
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
INK, MID = "#1a1a1a", "#555555"   # text tiers: near black (titles, key numbers), mid grey (all other text)
PANEL_BG = "#F3F6F9"              # background of the result panel
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


BOUNDARY_SRC = ("State and union-territory boundaries: DataMeet India community, States/Admin2 "
                "(https://github.com/datameet/maps, CC BY 4.0).")
ISLANDS = ("Andaman & Nicobar", "Lakshadweep")   # Indian territory: always drawn, labels are placed around them


def india_outline(a, sim_cells=None):
    """India outline (all states and union territories, islands included) and the island polygons."""
    states = gpd.read_file(a.boundaries)
    return states.dissolve().simplify(0.03), states[states.ST_NM.isin(ISLANDS)]


def geo_to_mm(ax, b, lon, lat):
    """Map coordinates on axes b -> mm on the base axes ax (after the aspect is applied)."""
    b.apply_aspect()
    x, y = ax.transData.inverted().transform(b.transData.transform((lon, lat)))
    return x, y


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
    head, label = (rob, "robust") if rob is not None else (base, "upper bound")
    # 2050 badge from numbers.json (src/make_numbers.py): median change and GCM range of the change,
    # calibrated N (the future stages are run with calibrated N)
    change = None
    fn, p = a.pp / "numbers.json", a.future.split("_")[0]
    if fn.exists():
        v = json.loads(fn.read_text())["values"]
        if all(f"{p}.{k}" in v for k in ("change_pct", "change_lo", "change_hi")):
            change = (v[f"{p}.change_pct"], v[f"{p}.change_lo"], v[f"{p}.change_hi"])
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


def check_layout(fig, panels):
    """Print text that leaves its panel or the figure, or overlaps other text (all in mm)."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    mm = 25.4 / fig.dpi
    boxes = []
    for t in fig.findobj(lambda o: hasattr(o, "get_text") and hasattr(o, "get_window_extent")):
        if not t.get_visible() or not str(t.get_text()).strip():
            continue
        e = t.get_window_extent(r)
        boxes.append((t.get_text().replace("\n", " "), e.x0 * mm, e.y0 * mm, e.x1 * mm, e.y1 * mm))
    bad = 0
    for txt, x0, y0, x1, y1 in boxes:
        if x0 < 0 or y0 < 0 or x1 > W or y1 > H:
            print(f"  CLIPPED  {txt!r} x {x0:.1f}-{x1:.1f} y {y0:.1f}-{y1:.1f}"); bad += 1
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        inside = [(px, pw) for px, pw, py0, py1 in panels if px - 0.5 < cx < px + pw + 0.5 and py0 < cy < py1]
        for px, pw in inside:
            if x0 < px + 0.3 or x1 > px + pw - 0.3:
                print(f"  EDGE     {txt!r} x {x0:.1f}-{x1:.1f} (panel {px:.1f}-{px + pw:.1f})"); bad += 1
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a_, b_ = boxes[i], boxes[j]
            if min(a_[3], b_[3]) - max(a_[1], b_[1]) > 0.1 and min(a_[4], b_[4]) - max(a_[2], b_[2]) > 0.1:
                print(f"  OVERLAP  {a_[0]!r} / {b_[0]!r}"); bad += 1
    print(f"layout check: {bad} issue(s)")


def sketch_farmland(ax, P, sun_y=27.5, sun_r=2.9, div_top=13.0):
    """Panel 1: sun over two PV rows (left) and crops (right) on one strip of soil, sized to fill the panel."""
    x0, w = P
    cx, gy = x0 + w / 2, 7.0
    ax.add_patch(Rectangle((x0 + 1.0, gy - 3.6), w - 2.0, 3.6, color=SOIL, lw=0))
    sun(ax, cx, sun_y, sun_r, ray=1.2)
    for k in range(2):
        x = x0 + 1.4 + 3.7 * k
        ax.add_patch(Polygon([[x, gy + 6.0], [x + 3.4, gy + 8.4], [x + 3.4, gy + 9.5], [x, gy + 7.1]],
                             color=BLUE, lw=0))
        ax.plot([x + 1.8, x + 1.8], [gy, gy + 7.2], color="0.45", lw=0.8)
    for k in range(3):
        sprout(ax, cx + 2.4 + 1.9 * k, gy, 5.6, lw=1.1)    # leaves stay right of the divide and inside
    ax.plot([cx, cx], [gy - 3.0, gy + div_top], color="0.3", lw=0.6, ls=(0, (2, 1.5)))


def write_caption(a, hlabel, scen):
    """Caption of the graphical abstract, consistent with what is drawn (graphical_abstract_caption.txt)."""
    case = ("calibrated nitrogen, an upper bound because low nitrogen rates hide part of the shade loss"
            if hlabel == "upper bound" else
            "robust case, in which each cell, crop and GCM takes the smaller GCR_max of the calibrated and "
            "recommended nitrogen runs")
    lay = LAYOUT_NAME[a.config]
    txt = (
        "Graphical abstract. Left: solar PV and crops compete for the same farmland. Centre: a light model and "
        "the DSSAT crop model give the relative yield (RY, crop yield under the array divided by open-field yield) as a function of the "
        "ground coverage ratio (GCR) for each cell, crop and layout; the curve is schematic. GCR_max is the "
        f"largest GCR that keeps RY ≥ {a.thr:.1f}, found where the RY-GCR curve, linearly interpolated from "
        "RY = 1 at GCR 0, first falls below the threshold. "
        f"Right: GCR_max at RY ≥ {a.thr:.1f} for the {lay} layout under 1995–2014 climate, {case}. "
        "For each 0.25° cell and crop, GCR_max is first computed for each of five GCMs and the median of the five "
        "is taken. Eligible area is the MapSPAM harvested area of the crop times the share of the cell with "
        "terrain slope ≤ 5%. The map shows, per cell, the mean of the four crops' median GCR_max weighted by "
        "eligible area; cells with less than 1000 ha of eligible area are left blank. Each crop value is the "
        "mean of that crop's median GCR_max over all cells with eligible area, weighted by eligible area. "
        "Cereals were simulated up to GCR 0.7 and legumes up to 0.5, so cells that still meet the threshold at "
        "that limit enter at the limit. The headline is the crops-combined capacity (double-cropped land counted "
        "once, capacity = eligible area × GCR_max × 2.2 MWp ha^−1^ per unit GCR), summed nationally for each GCM; "
        "the value shown is the median of the five national totals. "
        f"The badge gives the change in this capacity by 2041–2060 under {scen} against 1995–2014 with "
        "calibrated nitrogen: the change of the five-GCM median totals, and the range of the change over the "
        "five GCMs. " + BOUNDARY_SRC)
    (HERE / "graphical_abstract_caption.txt").write_text(txt + "\n")


def main():
    a = parse()
    cells, crop, head, change, hlabel = load_results(a)
    fig = plt.figure(figsize=(W / 10 * CM, H / 10 * CM))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")

    def axes_mm(x, y, w, h):
        return fig.add_axes([x / W, y / H, w / W, h / H])

    # three text tiers: T1 key numbers (large, bold), T2 panel titles (bold, near black), T3 everything else
    T2 = dict(fontsize=8, fontweight="bold", color=INK)
    T3 = dict(fontsize=7, color=MID)

    # panel frames with numbered discs on the top edge, titles and arrows between panels
    PL, PM, PR = (1.0, 17.9), (21.1, 43.9), (67.4, 61.6)      # (x, width) of the three panels, mm
    panels = [(PL, "Solar vs\nfood on\nfarmland"), (PM, "Simulate shade → yield"),
              (PR, f"Where ≥ {a.thr:.0%} yield is kept")]
    r_mm = fig.canvas.get_renderer()
    for i, ((x, w), t) in enumerate(panels, start=1):
        ax.add_patch(FancyBboxPatch((x, 1.0), w, 47.6, boxstyle="round,pad=0,rounding_size=1.8",
                                    fc=PANEL_BG if i == 3 else "white", ec="0.6", lw=0.6))
        # numbered disc inline, just left of the first title line, on its centre line; the title moves right
        # when the disc would otherwise reach the frame
        rd = 1.25
        first = ax.text(x + w / 2, 47.0, t.split("\n")[0], ha="center", va="top", **T2)
        e = first.get_window_extent(r_mm).transformed(ax.transData.inverted())
        first.remove()
        dx = max(0.0, x + 0.6 - (e.x0 - 0.5 - 2 * rd))
        e.x0 += dx
        ax.text(x + w / 2 + dx, 47.0, t, ha="center", va="top", linespacing=1.15, multialignment="center", **T2)
        cy = (e.y0 + e.y1) / 2
        ax.add_patch(Circle((e.x0 - 0.5 - rd, cy), rd, fc=INK, ec="none", zorder=5))
        ax.text(e.x0 - 0.5 - rd, cy - 0.05, str(i), ha="center", va="center", fontsize=7, fontweight="bold",
                color="white", zorder=6)
    for x0, x1 in ((PL[0] + PL[1] + 0.1, PM[0] - 0.1), (PM[0] + PM[1] + 0.1, PR[0] - 0.1)):
        ax.add_patch(FancyArrowPatch((x0, 25), (x1, 25), arrowstyle="-|>", mutation_scale=8, lw=1.2,
                                     color=GREY, shrinkA=0, shrinkB=0))

    # ---- 1 problem: solar rows and crops competing for the same land
    sketch_farmland(ax, PL)

    # ---- 2 method: one RY-GCR curve with tau and GCR_max
    mc = PM[0] + PM[1] / 2                      # method panel centre
    for cx, label, icon in ((mc - 7.75, "shade model", icon_shade), (mc + 10.75, "crop model", icon_cropmodel)):
        icon(ax, cx, 38.0, 4.0)
        ax.text(cx, 35.8, label, ha="center", va="center", **T3)
    ax.add_patch(FancyArrowPatch((mc - 3.65, 40.0), (mc + 6.65, 40.0), arrowstyle="-|>", mutation_scale=6, lw=0.9,
                                 color=GREY, shrinkA=0, shrinkB=0))
    ax.text(mc, 6.0, "every 0.25° cell · 5 climate models", ha="center", va="center", **T3)
    bx = mc - 9.25
    b = axes_mm(bx, 17.4, 28.0, 16.0)
    g = np.linspace(0, 0.7, 80); ry = 1 - 0.45 * g - 0.45 * g ** 2
    gm = g[np.argmin(abs(ry - a.thr))]
    # band between the curve and the RY = tau line, from GCR 0 to GCR_max: the yield kept above the threshold
    b.fill_between(g[g <= gm], a.thr, ry[g <= gm], color=SKY, alpha=0.45, lw=0)
    b.plot(g, ry, color=VERM, lw=1.4)
    b.axhline(a.thr, color="0.2", lw=0.6, ls="--")
    b.plot([gm, gm], [0.4, a.thr], color="0.2", lw=0.6, ls="--")
    b.plot(gm, a.thr, "o", ms=3.5, color="0.1", zorder=5)
    b.text(0.71, a.thr + 0.025, f"RY = {a.thr:.1f}", ha="right", va="bottom", **T3)
    b.text(gm + 0.025, 0.43, "GCR$_{max}$", va="bottom", **T3)
    b.text(0.71, 1.04, "schematic", ha="right", va="top", style="italic", **T3)
    b.annotate(f"≥ {a.thr:.1f}\nkept", xy=(0.07, a.thr + 0.07), xytext=(0.02, 0.6), fontsize=7, color=BLUE,
               ha="left", va="center", linespacing=1.05,
               arrowprops=dict(arrowstyle="-", color=BLUE, lw=0.6, shrinkA=0, shrinkB=0))
    b.set_xlim(0, 0.72); b.set_ylim(0.4, 1.05)
    b.set_xticks([0, 0.7], ["0", "0.7"]); b.set_yticks([0.4, 0.7, 1.0], ["0.4", "0.7", "1"])
    b.tick_params(labelsize=7, labelcolor=MID, length=2, width=0.5, pad=1)
    for s in ("top", "right"):
        b.spines[s].set_visible(False)
    b.set_xlabel("ground coverage ratio, GCR [–]", labelpad=1, **T3)
    b.xaxis.set_label_coords((mc - bx) / 28.0, -0.25)   # centred on the panel, not the axes
    b.set_ylabel("rel. yield, RY [–]", labelpad=1, **T3)
    b.yaxis.set_label_coords(-0.21, 0.46)

    # ---- 3 result: India map of GCR_max at RY >= tau
    mx, mw = PR[0] + 6.9, 20.8                  # map left edge and width (height follows the aspect)
    b = axes_mm(mx, 14.5, mw, mw * 29.5 / 26.2)
    b.set_facecolor("none")
    for s in b.spines.values():
        s.set_visible(False)
    india, islands = india_outline(a)
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
    cb_ax = axes_mm(PR[0] + 2.95, 16.6, 1.5, 6.4)    # over the Arabian Sea, so tick labels clear the coast
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cb_ax, ticks=[0, 0.35, 0.7])
    cb.ax.set_yticklabels(["0", "0.35", "0.7"])
    cb.ax.tick_params(labelsize=7, labelcolor=MID, length=1.5, width=0.5, pad=1)
    cb.outline.set_linewidth(0.5)
    ax.text(PR[0] + 1.65, 21.7, "max GCR", ha="center", va="center", rotation=90, **T3)

    # headline capacity, right-aligned in the empty area north-east of the map, and the 2050 badge
    big, rng = fmt_cap(head)
    xe = PR[0] + PR[1] - 1.2                    # right text edge
    ax.text(xe, 40.0, big, ha="right", va="center", fontsize=14, fontweight="bold", color=BLUE)
    lab = ax.text(xe, 36.3, f"({hlabel})", ha="right", va="center", fontsize=7, fontweight="bold", color=INK)
    lx = lab.get_window_extent(r_mm).transformed(ax.transData.inverted()).x0
    ax.text(lx - 0.6, 36.3, "technical potential", ha="right", va="center", **T3)
    ax.text(xe, 33.8, "1995–2014 climate", ha="right", va="center", **T3)
    if head is None:
        ax.add_patch(Rectangle((xe - 27.0, 37.6), 27.0, 5.0, fill=False, ec="0.1", lw=0.5, ls="--"))
    # badge: white with a thin orange border; values from numbers.json, placeholders when the stage is missing
    scen = {"ssp585": "SSP5-8.5", "ssp245": "SSP2-4.5"}.get(a.future.split("_")[0], "SSP5-8.5")
    med, lo, hi = ("[±X]", "[lo]", "[hi]") if change is None else change
    b.set_xlim(68, 97.5); b.set_ylim(6.5, 37.3)
    andaman = islands[islands.ST_NM == "Andaman & Nicobar"].total_bounds
    bl = geo_to_mm(ax, b, andaman[2], andaman[3])[0] + 0.8   # badge starts east of the Andaman Islands
    br = PR[0] + PR[1] - 0.4
    xb = (bl + br) / 2
    ax.add_patch(FancyBboxPatch((bl, 15.6), br - bl, 12.4, boxstyle="round,pad=0,rounding_size=1.6",
                                fc="white", ec=ORANGE, lw=0.6))
    ax.text(xb, 24.6, f"{med}% by 2050", ha="center", va="center", fontsize=10, fontweight="bold", color=INK)
    ax.text(xb, 20.9, f"{scen} vs 1995–2014", ha="center", va="center", **T3)
    ax.text(xb, 18.3, f"5-model range {lo} to {hi}%", ha="center", va="center", **T3)
    val = f"{med}% ({lo} to {hi}%)"

    # crop icons with national mean GCR_max, small label at the start of the row
    ax.text(PR[0] + 1.5, 13.9, f"max GCR (RY ≥ {a.thr:.1f})", ha="left", va="center", **T3)
    for (c, name), cx in zip(CROPS, (PR[0] + 6.2, PR[0] + 21.0, PR[0] + 37.0, PR[0] + 53.6)):
        ICONS[c](ax, cx - 3.4, 6.6, 6.0)
        ax.text(cx - 0.4, 9.6, "[X]" if c not in crop else f"{crop[c]:.2f}", ha="left", va="center",
                fontsize=8, fontweight="bold", color=INK)
        ax.text(cx - 1.0, 3.4, name, ha="center", va="center", **T3)

    a.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out.with_suffix(".pdf"))
    fig.savefig(a.out.with_suffix(".png"), dpi=600)
    check_layout(fig, [(*PL, 0, H), (*PM, 0, H), (*PR, 0, H), (bl, br - bl, 15.6, 28.0)])
    write_caption(a, hlabel, scen)
    print("wrote", a.out.with_suffix(".pdf"), "map:", "filled" if cells else "placeholder",
          "| headline:", big, f"({hlabel})", rng, "|", f"2050 change ({scen}): {val}", "| crops:", {c: round(v, 2) for c, v in crop.items()})


if __name__ == "__main__":
    main()
