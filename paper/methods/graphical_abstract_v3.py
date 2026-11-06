"""Graphical abstract, version 3: one dominant map, a title block and a findings box
(layout after the Applied Energy graphical abstract of Neesham-McTiernan et al. 2025).

  left   navy title block (the question), a three-step method strip, a pale findings box with three
         bold numbers: national capacity and its multiple of India's electricity use, cereal vs legume
         panel cover, 2050 change in capacity and energy
  right  large India map of the largest panel cover that keeps >= 80% of the open-field yield,
         colour bar in the Arabian Sea

Numbers come from the same files as graphical_abstract_simple.py (nothing hard-coded): headline from
india_combined_<stage>[_robust].csv, map and crop groups from map_gcr_<stage>[_robust].csv.gz, the electricity
multiple and 2050 changes from numbers.json. Font: Source Sans 3 (SIL OFL 1.1), bundled in fonts/ so Cloud Shell
renders the same text widths.

Usage (from paper/methods): python graphical_abstract_v3.py [--future ssp585_current]
Writes graphical_abstract_v3.pdf / .png (600 dpi) and graphical_abstract_v3_caption.txt.
"""
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import graphical_abstract as GA  # noqa: E402
import graphical_abstract_simple as GS  # noqa: E402
from graphical_abstract import H, W, CM, check_layout, fmt_cap, geo_to_mm, india_outline, load_results  # noqa: E402

for f in sorted((HERE / "fonts").glob("SourceSans3-*.ttf")):   # after the imports, which set their own rcParams
    font_manager.fontManager.addfont(str(f))
# Source Sans 3 (Adobe, SIL OFL 1.1), latin subset; DejaVu Sans supplies the few maths glyphs (≈ ≥) it lacks
mpl.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Source Sans 3", "DejaVu Sans"],
                     "pdf.fonttype": 42})

NAVY, PALE, PALE_EC = "#1F3B5C", "#E8F1EA", "#9DBFA5"
INK, MID, ACC = "#1A1A1A", "#4D4D4D", "#0B6E99"
PILL, PILL_EC = "#EEF3F8", "#A9BCD0"


def parse():
    sys.argv += [] if any(x.startswith("--out") for x in sys.argv) else ["--out", str(HERE / "graphical_abstract_v3")]
    return GA.parse()


def write_caption(a, hlabel, scen):
    case = ("calibrated nitrogen, an upper bound because low nitrogen rates hide part of the shade loss"
            if hlabel == "upper bound" else
            "robust case, in which each cell, crop and GCM takes the smaller panel cover of the calibrated and "
            "recommended nitrogen runs")
    txt = (
        "Graphical abstract. A light model for three array layouts and the DSSAT crop model for wheat, chickpea, "
        "pearl millet and groundnut give, for every 0.25° cell, the largest panel cover (ground coverage ratio, "
        f"the share of land covered by modules) that keeps at least {a.thr:.0%} of the open-field yield. The map "
        f"shows it for east-west elevated arrays under 1995–2014 climate, {case}: the median over five GCMs, "
        "averaged over the four crops with eligible-area weights (MapSPAM harvested area on the share of the "
        "cell with slope ≤ 5%); cells with less than 1000 ha are blank. Capacity is the crops-combined total "
        "with double-cropped land counted once (median of five GCMs); the electricity multiple is its annual "
        "generation divided by India's 2025–26 electricity requirement (1,707 TWh, CEA). Cereal and legume "
        "values are eligible-area-weighted means; the call-outs give the same mean for the wheat belt (24–31°N, "
        "74–88°E) and the Deccan (12–21°N, 73–80°E). The 2050 values are the changes by 2041–2060 under "
        f"{scen} against 1995–2014 (five-GCM median, calibrated nitrogen). " + GA.BOUNDARY_SRC)
    (HERE / "graphical_abstract_v3_caption.txt").write_text(txt + "\n")


REGIONS = {   # annotated on the map: box (lon0, lon1, lat0, lat1), label anchor in the sea or empty land (lon, lat)
    "north": ((74, 88, 24, 31), "Wheat-dominated north"),
    "deccan": ((73, 80, 12, 21), "Legume-rich Deccan"),
}


def region_cover(a):
    """Eligible-area-weighted mean panel cover (%) in the two annotated regions, same map file as the figure."""
    fm = a.pp / f"map_gcr_{a.stage}_robust.csv.gz"
    if not fm.exists():
        fm = a.pp / f"map_gcr_{a.stage}.csv.gz"
    if not fm.exists():
        return {}
    m = pd.read_csv(fm)
    m = m[(m.config == a.config) & (m.thr.round(2) == round(a.thr, 2)) & (m.elig_ha > 0)]
    m = m.join(pd.read_csv(a.grid).set_index("cell_id")[["lat", "lon"]], on="cell")
    out = {}
    for k, ((x0, x1, y0, y1), _) in REGIONS.items():
        d = m[m.lon.between(x0, x1) & m.lat.between(y0, y1)]
        if len(d):
            out[k] = 100 * np.average(d.gcr_med, weights=d.elig_ha)
    return out


def main():
    a = parse()
    cells, crop, head, change, hlabel = load_results(a)
    grp, num, reg = GS.group_cover(a), GS.numbers(a), region_cover(a)
    pct = int(round(100 * a.thr))
    fig = plt.figure(figsize=(W / 10 * CM, H / 10 * CM))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
    r = fig.canvas.get_renderer()

    def axes_mm(x, y, w, h):
        return fig.add_axes([x / W, y / H, w / W, h / H])

    def box(x, y, w, h, fc, ec="none", lw=0.0, rs=1.8):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={rs}", fc=fc, ec=ec, lw=lw))

    def width(t):
        return t.get_window_extent(r).transformed(ax.transData.inverted()).width

    def fit(x, y, txt, maxw, size, **kw):
        """Text shrunk in 0.25 pt steps until it fits maxw (never below 7 pt)."""
        while True:
            t = ax.text(x, y, txt, fontsize=size, **kw)
            if width(t) <= maxw or size <= 7:
                return t
            t.remove(); size -= 0.25

    LX, LW = 1.5, 66.0
    gap = 2.4
    cw = (LW - 2 * gap) / 3                   # width of a step pill and of a finding card
    LBL = dict(fontsize=7, fontweight="bold", color=ACC)                  # small section labels

    # ---- the question
    box(LX, 38.6, LW, 10.2, NAVY, rs=2.0)
    ax.text(LX + LW / 2, 43.7, f"How much solar can India's farmland host\nand still keep {pct}% of each harvest?",
            ha="center", va="center", fontsize=10, fontweight="bold", color="white", linespacing=0.9)

    # ---- the method: three steps, one line each
    ax.text(LX + 0.3, 36.6, "METHOD", ha="left", va="center", **LBL)
    steps = [("Light model", "shade on crops,\n3 panel layouts"),
             ("Crop model", "DSSAT, 4 crops,\n5 climate models"),
             ("Yield rule",  f"densest panels\nat {pct}% of harvest")]
    py, ph = 25.4, 9.6
    for k, (h1, h2) in enumerate(steps):
        px = LX + k * (cw + gap)
        box(px, py, cw, ph, PILL, PILL_EC, 0.5, rs=1.4)
        ax.text(px + cw / 2, py + 7.1, h1, ha="center", va="center", fontsize=8, fontweight="bold", color=INK)
        ax.text(px + cw / 2, py + 3.0, h2, ha="center", va="center", fontsize=7, color=MID, linespacing=0.8)
        if k < 2:
            ax.add_patch(FancyArrowPatch((px + cw + 0.35, py + ph / 2), (px + cw + gap - 0.35, py + ph / 2),
                                         arrowstyle="-|>", mutation_scale=6, lw=0.8, color=NAVY, shrinkA=0,
                                         shrinkB=0))

    # ---- key findings: one number per card, its caption directly underneath
    ax.text(LX + 0.3, 22.9, "KEY FINDINGS", ha="left", va="center", **LBL)
    big, _ = fmt_cap(head)
    mult = num.get("frame.head_multiple", num.get("frame.main_multiple", "[N]"))
    p = a.future.split("_")[0]
    scen = {"ssp585": "SSP5-8.5", "ssp245": "SSP2-4.5"}.get(p, "SSP5-8.5")
    ch = num.get(f"{p}.change_pct", "[±X]")
    cer = f"{grp['cereals']:.0f}%" if "cereals" in grp else "[x]%"
    leg = f"{grp['legumes']:.0f}%" if "legumes" in grp else "[y]%"
    cy, chh = 1.5, 19.6
    YN, YC = 14.0, 10.3                        # number centre, caption top
    NUM = dict(fontweight="bold", color=ACC, ha="center", va="center")
    CAP = dict(fontsize=7, color=INK, ha="center", va="top", linespacing=0.8)
    for k in range(3):
        cx = LX + k * (cw + gap)
        box(cx, cy, cw, chh, "white", PILL_EC, 0.6, rs=1.4)
        ax.add_patch(FancyBboxPatch((cx, cy + chh - 0.9), cw, 0.9, boxstyle="round,pad=0,rounding_size=0.45",
                                    fc=ACC, ec="none"))
        mid = cx + cw / 2
        ax.text(mid, cy + chh - 2.6, ("HOW MUCH?", "HOW DENSE?", "BY 2050?")[k], ha="center", va="center",
                fontsize=7, fontweight="bold", color=MID)
        if k == 0:
            fit(mid, YN, big, cw - 2.4, 13, **NUM)
            ax.text(mid, YC, f"of solar fits;\noutput: {mult}× India's\nelectricity use", **CAP)
        elif k == 1:
            for j, (v, nm) in enumerate(((cer, "cereals"), (leg, "legumes"))):
                xx = cx + cw * (0.27 + 0.46 * j)
                ax.text(xx, YN + 0.6, v, fontsize=12, **NUM)
                ax.text(xx, YN - 2.5, nm, fontsize=7, color=MID, ha="center", va="center")
            ax.plot([mid, mid], [YN - 3.1, YN + 2.8], color=PILL_EC, lw=0.5)
            ax.text(mid, YC - 1.0, "of field under panels", **CAP)
            ax.text(mid, YC - 4.4, "Set caps by crop", **dict(CAP, fontweight="bold", color=ACC))
        else:
            ax.text(mid, YN, f"{ch}%", fontsize=13, **NUM)
            ax.text(mid, YC - 1.0, f"capacity, {scen}", **CAP)
            ax.text(mid, YC - 4.4, "Climate-robust", **dict(CAP, fontweight="bold", color=ACC))

    # ---- map: the answer, everywhere
    MX, MY, MH = 70.5, 1.0, 48.0
    MW = MH * 29.5 * np.cos(np.radians(22)) / 30.8
    b = axes_mm(MX, MY, MW, MH)
    b.set_facecolor("none")
    ax.set_zorder(3); ax.patch.set_visible(False)       # call-outs and labels on top of the map
    for sp in b.spines.values():
        sp.set_visible(False)
    india, _ = india_outline(a)
    bounds = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7001]
    cmap = ListedColormap(plt.colormaps["viridis"](np.linspace(0, 1, len(bounds) - 1)))
    norm = BoundaryNorm(bounds, cmap.N)
    india.plot(ax=b, color="#EDEDED", edgecolor="none")
    if cells is not None:
        lon, lat, v = cells
        lons = np.round(np.arange(68.125, 97.5, 0.25), 3); lats = np.round(np.arange(6.625, 37.25, 0.25), 3)
        z = np.full((len(lats), len(lons)), np.nan)
        z[np.searchsorted(lats, np.round(lat, 3)), np.searchsorted(lons, np.round(lon, 3))] = v
        b.pcolormesh(np.append(lons - 0.125, lons[-1] + 0.125), np.append(lats - 0.125, lats[-1] + 0.125),
                     np.ma.masked_invalid(z), cmap=cmap, norm=norm, edgecolors="none", rasterized=True)
    india.boundary.plot(ax=b, color="#4A4A4A", lw=0.45)
    b.set_xlim(68, 97.5); b.set_ylim(6.5, 37.3); b.set_aspect(1 / np.cos(np.radians(22)))
    b.set_xticks([]); b.set_yticks([]); b.set_xlabel(""); b.set_ylabel("")

    # two call-outs carry the map's story (values computed from the same map file)
    def callout(key, label, txt_lonlat, pt_lonlat):
        if key not in reg:
            return
        tx, ty = geo_to_mm(ax, b, *txt_lonlat)
        px, py_ = geo_to_mm(ax, b, *pt_lonlat)
        t = ax.text(tx, ty, label, ha="left", va="bottom", fontsize=7.5, fontweight="bold", color=INK, linespacing=0.8)
        ax.text(tx, ty - 0.3, f"{reg[key]:.0f}% of land", ha="left", va="top", fontsize=7, color=MID)
        ax.annotate("", xy=(px, py_), xytext=(tx - 0.6, ty),
                    arrowprops=dict(arrowstyle="-", lw=0.6, color=INK, shrinkA=0, shrinkB=0))
        ax.plot(px, py_, "o", ms=2.4, mfc="white", mec=INK, mew=0.7, zorder=6)
    callout("north", "Wheat belt", (86.5, 33.6), (80.5, 27.3))
    callout("deccan", "Legume-rich\nDeccan", (81.3, 10.4), (76.6, 16.6))

    # colour bar east of the map, beside the Bay of Bengal
    cbx, cby, cbh = MX + MW + 1.6, 4.0, 18.0
    cb_ax = axes_mm(cbx, cby, 1.7, cbh)
    ticks = [0, 0.35, 0.7]
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cb_ax, ticks=ticks)
    cb.ax.set_yticklabels([f"{100 * t:.0f}%" for t in ticks])
    cb.ax.tick_params(labelsize=7, labelcolor=MID, length=1.5, width=0.5, pad=1)
    cb.ax.minorticks_off()
    cb.outline.set_linewidth(0.4)
    ax.text(cbx - 0.2, cby + cbh + 11.6, "Max land\nunder panels", ha="left", va="bottom", fontsize=7,
            fontweight="bold", color=INK, linespacing=0.8)
    ax.text(cbx - 0.2, cby + cbh + 11.1, f"per field,\nkeeping {pct}%\nof harvest", ha="left", va="top", fontsize=7, color=MID, linespacing=0.8)

    a.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out.with_suffix(".pdf"))
    fig.savefig(a.out.with_suffix(".png"), dpi=600)
    check_layout(fig, [(LX, LW, 0, H)])
    write_caption(a, hlabel, scen)
    print("wrote", a.out.with_suffix(".png"), "|", big, hlabel, "| x", mult, "| 2050", ch, "|", cer, leg, "|",
          {k: round(v) for k, v in reg.items()})


if __name__ == "__main__":
    main()
