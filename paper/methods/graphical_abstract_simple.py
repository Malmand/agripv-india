"""Simpler graphical abstract for non-specialists (same size, colours, icons and map as graphical_abstract.py).

No jargon: relative yield is "% of open-field harvest", GCR is "panel cover (% of land)".
  1  question   "How much solar fits on India's farmland and keeps 80% of the harvest?" with the sun / PV / crop sketch
  2  method     shade model -> crop model, schematic harvest curve against panel cover (no numbers on x)
  3  answer     map of max panel cover keeping 80% of the harvest, headline capacity, multiple of India's
                electricity use, upper bound / robust label, 2050 change, cereal and legume panel cover

Numbers (nothing hard-coded):
  map, cereal / legume values  <pp>/map_gcr_<stage>[_robust].csv.gz, five-GCM median GCR_max per cell and crop,
                               averaged with eligible-area weights (same file and weights as make_numbers.py
                               uses for gcr_<crop>); the cereal value pools wheat and pearl millet, the legume
                               value chickpea and groundnut; shown in % of land
  headline                     <pp>/india_combined_<stage>[_robust].csv (as graphical_abstract.py)
  electricity multiple         numbers.json frame.head_multiple (robust case when present, else equal to
                               frame.main_multiple)
  2050 change                  numbers.json <future>.change_pct
Imports the drawing helpers of graphical_abstract.py, so both versions stay in step.

Usage (from paper/methods): python graphical_abstract_simple.py [--pp ../../results/potential] [--future ssp585_current]
Writes graphical_abstract_simple.pdf / .png (600 dpi) and graphical_abstract_simple_caption.txt.
Not used by the manuscript builders.
"""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parent))
import graphical_abstract as GA  # noqa: E402
from graphical_abstract import (BLUE, GREY, INK, MID, ORANGE, PANEL_BG, SKY, VERM, H, HERE, ICONS,  # noqa: E402
                                MIN_HA, W, CM, check_layout, fmt_cap, geo_to_mm, icon_cropmodel, icon_shade,
                                india_outline, load_results, sketch_farmland)

CEREALS, LEGUMES = ("wheat", "pearl_millet"), ("chickpea", "groundnut")


def parse():
    sys.argv += [] if any(x.startswith("--out") for x in sys.argv) else ["--out", str(HERE / "graphical_abstract_simple")]
    return GA.parse()


def group_cover(a):
    """Eligible-area-weighted mean of the five-GCM median GCR_max for cereals and for legumes, in %."""
    fm = a.pp / f"map_gcr_{a.stage}_robust.csv.gz"
    if not fm.exists():
        fm = a.pp / f"map_gcr_{a.stage}.csv.gz"
    if not fm.exists():
        return {}
    m = pd.read_csv(fm)
    m = m[(m.config == a.config) & (m.thr.round(2) == round(a.thr, 2)) & (m.elig_ha > 0)]
    out = {}
    for name, crops in (("cereals", CEREALS), ("legumes", LEGUMES)):
        d = m[m.crop.isin(crops)]
        if len(d):
            out[name] = 100 * np.average(d.gcr_med, weights=d.elig_ha)
    return out


def numbers(a):
    f = a.pp / "numbers.json"
    return json.loads(f.read_text())["values"] if f.exists() else {}


def wrap(ax, r, text, width, first_width=None, **kw):
    """Fewest lines that fit the width (first line may be narrower), then the most even line lengths.
    Every split of the words is tried (fine for a one-sentence title), widths measured with the renderer."""
    words = text.split()
    cache = {}

    def wmm(sx):
        if sx not in cache:
            t = ax.text(0, 0, sx, **kw)
            cache[sx] = t.get_window_extent(r).transformed(ax.transData.inverted()).width
            t.remove()
        return cache[sx]

    best = None
    for mask in range(1 << (len(words) - 1)):
        lines, cur = [], [words[0]]
        for i in range(1, len(words)):
            if mask >> (i - 1) & 1:
                lines.append(" ".join(cur)); cur = [words[i]]
            else:
                cur.append(words[i])
        lines.append(" ".join(cur))
        if best is not None and len(lines) > best[0][0]:
            continue
        ws = [wmm(sx) for sx in lines]
        if ws[0] <= (first_width or width) and all(x <= width for x in ws[1:]):
            key = (len(lines), max(ws))
            if best is None or key < best[0]:
                best = (key, lines)
    return "\n".join(best[1] if best else words)


def disc(ax, r, x, y_top, first_line, n, xmin, **T):
    """Numbered disc left of the first title line (as graphical_abstract.py); returns the title shift."""
    rd = 1.25
    t = ax.text(x, y_top, first_line, ha="center", va="top", **T)
    e = t.get_window_extent(r).transformed(ax.transData.inverted())
    t.remove()
    dx = max(0.0, xmin + 0.6 - (e.x0 - 0.5 - 2 * rd))
    cx, cy = e.x0 + dx - 0.5 - rd, (e.y0 + e.y1) / 2
    ax.add_patch(Circle((cx, cy), rd, fc=INK, ec="none", zorder=5))
    ax.text(cx, cy - 0.05, str(n), ha="center", va="center", fontsize=7, fontweight="bold", color="white", zorder=6)
    return dx


def write_caption(a, hlabel, scen, mult_key):
    case = ("calibrated nitrogen, an upper bound because low nitrogen rates hide part of the shade loss"
            if hlabel == "upper bound" else
            "robust case, in which each cell, crop and GCM takes the smaller panel cover of the calibrated and "
            "recommended nitrogen runs")
    txt = (
        "Graphical abstract (simple version). Left: the question. Centre: a light model and the DSSAT crop model "
        "give the harvest under the panels as a percentage of the open-field harvest for increasing panel cover "
        "(ground coverage ratio, the share of land covered by modules); the curve is schematic. The dot marks the "
        f"largest panel cover that keeps at least {a.thr:.0%} of the open-field harvest. "
        f"Right: that largest panel cover for east-west panels under 1995–2014 climate, {case}. For each 0.25° "
        "cell and crop it is the median over five GCMs; the map shows the mean of the four crops weighted by "
        "eligible area (MapSPAM harvested area on the share of the cell with slope ≤ 5%), and cells with less "
        "than 1000 ha are blank. The cereal value is the eligible-area-weighted mean over all wheat and pearl "
        "millet cells, the legume value over all chickpea and groundnut cells. The headline is the "
        "crops-combined capacity (double-cropped land counted once), median of the five national totals. "
        "The electricity multiple is its annual generation divided by India's 2025–26 electricity requirement "
        "(1,707 TWh; CEA Load Generation Balance Report 2026-27). The 2050 line "
        f"gives the change in capacity by 2041–2060 under {scen} against 1995–2014 (five-GCM median, "
        "calibrated nitrogen). " + GA.BOUNDARY_SRC)
    (HERE / "graphical_abstract_simple_caption.txt").write_text(txt + "\n")


def main():
    a = parse()
    cells, crop, head, change, hlabel = load_results(a)
    grp, num = group_cover(a), numbers(a)
    fig = plt.figure(figsize=(W / 10 * CM, H / 10 * CM))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
    r = fig.canvas.get_renderer()

    def axes_mm(x, y, w, h):
        return fig.add_axes([x / W, y / H, w / W, h / H])

    T1 = dict(fontweight="bold", color=BLUE)
    T2 = dict(fontsize=8, fontweight="bold", color=INK)
    T3 = dict(fontsize=7, color=MID)
    pct = int(round(100 * a.thr))

    PL, PM, PR = (1.0, 26.6), (29.6, 45.4), (77.0, 52.0)
    for i, (x, w) in enumerate((PL, PM, PR), start=1):
        ax.add_patch(FancyBboxPatch((x, 1.0), w, 47.6, boxstyle="round,pad=0,rounding_size=1.8",
                                    fc=PANEL_BG if i == 3 else "white", ec="0.6", lw=0.6))
    for x0, x1 in ((PL[0] + PL[1] + 0.1, PM[0] - 0.1), (PM[0] + PM[1] + 0.1, PR[0] - 0.1)):
        ax.add_patch(FancyArrowPatch((x0, 25), (x1, 25), arrowstyle="-|>", mutation_scale=8, lw=1.2,
                                     color=GREY, shrinkA=0, shrinkB=0))

    # ---- 1 question
    x, w = PL
    TQ = dict(T2, fontsize=7.5)               # the question is long: 7.5 pt bold keeps it to five lines
    q = wrap(ax, r, f"How much solar fits on India's farmland and keeps {pct}% of the harvest?", w - 1.6,
             first_width=w - 5.0, ha="center", va="top", **TQ)
    dx = disc(ax, r, x + w / 2, 47.0, q.split("\n")[0], 1, x, **TQ)
    for k, line in enumerate(q.split("\n")):
        qt = ax.text(x + w / 2 + dx, 47.0 - 3.1 * k, line, ha="center", va="top", **TQ)
    qb = qt.get_window_extent(r).transformed(ax.transData.inverted()).y0
    sketch_farmland(ax, PL, sun_y=(qb + 17.2) / 2, sun_r=1.9, div_top=10.0)

    # ---- 2 method
    x, w = PM
    mc = x + w / 2
    dx = disc(ax, r, mc, 47.0, "Simulate shade → harvest", 2, x, **T2)
    ax.text(mc + dx, 47.0, "Simulate shade → harvest", ha="center", va="top", **T2)
    for cx, label, icon in ((mc - 9.0, "shade model", icon_shade), (mc + 9.0, "crop model", icon_cropmodel)):
        icon(ax, cx, 39.9, 3.6)
        ax.text(cx, 38.0, label, ha="center", va="center", **T3)
    ax.add_patch(FancyArrowPatch((mc - 5.2, 41.7), (mc + 5.0, 41.7), arrowstyle="-|>", mutation_scale=6, lw=0.9,
                                 color=GREY, shrinkA=0, shrinkB=0))
    ax.text(mc, 6.0, "every 0.25° cell · 5 climate models", ha="center", va="center", **T3)
    bx, bw = mc - 13.0, 31.0
    b = axes_mm(bx, 16.4, bw, 16.4)
    g = np.linspace(0, 0.7, 80); ry = 100 * (1 - 0.45 * g - 0.45 * g ** 2)
    gm = g[np.argmin(abs(ry - pct))]
    b.fill_between(g[g <= gm], pct, ry[g <= gm], color=SKY, alpha=0.45, lw=0)
    b.plot(g, ry, color=VERM, lw=1.4)
    b.axhline(pct, color="0.2", lw=0.6, ls="--")
    b.plot([gm, gm], [40, pct], color="0.2", lw=0.6, ls="--")
    b.plot(gm, pct, "o", ms=3.5, color="0.1", zorder=5)
    b.text(gm - 0.02, 43, "max panel\ncover", ha="right", va="bottom", linespacing=1.05, **T3)
    b.text(0.71, 104, "schematic", ha="right", va="top", style="italic", **T3)
    b.set_xlim(0, 0.72); b.set_ylim(40, 105)
    b.set_xticks([]); b.set_yticks([pct, 100], [f"{pct}%", "100%"])
    b.tick_params(labelsize=7, labelcolor=MID, length=2, width=0.5, pad=1)
    for s in ("top", "right"):
        b.spines[s].set_visible(False)
    b.set_xlabel("panel cover: sparse → dense", labelpad=2, **T3)
    ax.text(bx - 0.4, 34.6, "harvest (% of open field)", ha="left", va="center", **T3)

    # ---- 3 answer
    x, w = PR
    dx = disc(ax, r, x + w / 2, 47.0, "Answer for India", 3, x, **T2)
    ax.text(x + w / 2 + dx, 47.0, "Answer for India", ha="center", va="top", **T2)
    # map title directly above the map, left-aligned with it
    ax.text(x + 1.4, 40.5, f"max panel cover\nkeeping {pct}% harvest", ha="left", va="center", linespacing=1.1, **T3)
    mx, mw = x + 1.2, 20.6
    mh = mw * 29.5 / 26.2
    b = axes_mm(mx, 13.8, mw, mh)
    b.set_facecolor("none")
    for s in b.spines.values():
        s.set_visible(False)
    gr = pd.read_csv(a.grid)
    india, islands = india_outline(a)
    bounds = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7001]
    cmap = ListedColormap(plt.colormaps["viridis"](np.linspace(0, 1, len(bounds) - 1)))
    norm = BoundaryNorm(bounds, cmap.N)
    if cells is None:
        india.plot(ax=b, color="0.9", edgecolor="0.4", lw=0.4, hatch="////")
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
    # colour bar in the Bay of Bengal, between the east coast and the Andaman Islands; ticks in % of land
    ticks = [0, 0.35, 0.7]
    c0x, c0y = geo_to_mm(ax, b, 84.0, 9.0)
    c1x, c1y = geo_to_mm(ax, b, 84.0, 16.2)
    cb_ax = axes_mm(c0x, c0y, 1.2, c1y - c0y)
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cb_ax, ticks=ticks)
    cb.ax.set_yticklabels([f"{100 * t:.0f}" + ("%" if t == ticks[-1] else "") for t in ticks])
    cb.ax.tick_params(labelsize=7, labelcolor=MID, length=1.5, width=0.5, pad=1)
    cb.outline.set_linewidth(0.5)

    # right column: headline, electricity multiple, case label, 2050 line
    xe = x + w - 1.2
    big, _ = fmt_cap(head)
    ax.text(xe, 35.0, big, ha="right", va="center", fontsize=14, **T1)
    mult_key = "frame.head_multiple" if "frame.head_multiple" in num else "frame.main_multiple"
    mult = num.get(mult_key, "[N]")
    ax.text(xe, 31.8, f"would generate ≈ {mult}×\nIndia's yearly\nelectricity use", ha="right", va="top",
            linespacing=1.1, **T3)
    ax.text(xe, 22.5, f"({hlabel})", ha="right", va="center", fontsize=7, fontweight="bold", color=INK)
    scen = {"ssp585": "SSP5-8.5", "ssp245": "SSP2-4.5"}.get(a.future.split("_")[0], "SSP5-8.5")
    p = a.future.split("_")[0]
    ch = num.get(f"{p}.change_pct", "[±X]")
    ax.text(xe, 18.6, f"2050 ({scen}):\n{ch}% vs 1995–2014", ha="right", va="center", linespacing=1.1, **T3)

    # crop groups: two icons each with the group's panel cover, under a small row label
    ax.text(x + 1.4, 12.1, "max panel cover:", ha="left", va="center", **T3)
    for k, (name, crops) in enumerate((("cereals", CEREALS), ("legumes", LEGUMES))):
        gx = x + 2.0 + k * 27.0
        for j, c in enumerate(crops):
            ICONS[c](ax, gx + 4.4 * j, 2.6, 6.0)
        val = f"~{grp[name]:.0f}%" if name in grp else "~[x]%"
        ax.text(gx + 9.6, 4.6, name, ha="left", va="center", **T3)
        ax.text(gx + 9.6, 7.6, val, ha="left", va="center", fontsize=8, fontweight="bold", color=INK)

    a.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out.with_suffix(".pdf"))
    fig.savefig(a.out.with_suffix(".png"), dpi=600)
    check_layout(fig, [(*PL, 0, H), (*PM, 0, H), (*PR, 0, H)])
    write_caption(a, hlabel, scen, mult_key)
    print("wrote", a.out.with_suffix(".png"), "| headline:", big, f"({hlabel})", "| x", mult, "| 2050", ch,
          "| groups:", {k: round(v, 1) for k, v in grp.items()})


if __name__ == "__main__":
    main()
