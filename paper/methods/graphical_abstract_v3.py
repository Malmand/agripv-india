"""Graphical abstract, version 3: one dominant map, a title block and a findings box
(layout after the Applied Energy graphical abstract of Neesham-McTiernan et al. 2025).

  left   navy title block (the question), a three-step method strip, a pale findings box with three
         bold numbers: national capacity and its multiple of India's electricity use, cereal vs legume
         panel cover, 2050 change in capacity and energy
  right  large India map of the largest panel cover that keeps >= 80% of the open-field yield,
         colour bar in the Arabian Sea

Numbers come from the same files as graphical_abstract_simple.py (nothing hard-coded): headline from
india_combined_<stage>[_robust].csv, map and crop groups from map_gcr_<stage>[_robust].csv.gz, the electricity
multiple and 2050 changes from numbers.json. Font: Inter (SIL OFL 1.1), bundled in fonts/ so Cloud Shell
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

for f in sorted((HERE / "fonts").glob("Inter-*.otf")):   # after the imports, which set their own rcParams
    font_manager.fontManager.addfont(str(f))
mpl.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Inter", "DejaVu Sans"], "pdf.fonttype": 42})

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
        "values are eligible-area-weighted means. The 2050 values are the changes by 2041–2060 under "
        f"{scen} against 1995–2014 (five-GCM median, calibrated nitrogen). " + GA.BOUNDARY_SRC)
    (HERE / "graphical_abstract_v3_caption.txt").write_text(txt + "\n")


def main():
    a = parse()
    cells, crop, head, change, hlabel = load_results(a)
    grp, num = GS.group_cover(a), GS.numbers(a)
    pct = int(round(100 * a.thr))
    fig = plt.figure(figsize=(W / 10 * CM, H / 10 * CM))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
    r = fig.canvas.get_renderer()

    def axes_mm(x, y, w, h):
        return fig.add_axes([x / W, y / H, w / W, h / H])

    def box(x, y, w, h, fc, ec="none", lw=0.0, rs=2.2):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={rs}", fc=fc, ec=ec, lw=lw))

    LX, LW = 1.5, 66.0                       # left column

    # ---- title block
    box(LX, 36.0, LW, 12.5, NAVY)
    ax.text(LX + LW / 2, 42.25, f"How much solar can India's cropland carry\nwhile keeping {pct}% of the crop yield?",
            ha="center", va="center", fontsize=8.5, fontweight="semibold", color="white", linespacing=1.25)

    # ---- method strip: three pills joined by arrows
    steps = ["Light model\n3 array layouts", "Crop model\nDSSAT, 4 crops", f"Yield rule\n≥ {pct}% of yield"]
    pw, gap, py, ph = 20.0, 3.0, 26.5, 7.6
    x0 = LX + (LW - (3 * pw + 2 * gap)) / 2
    for k, s in enumerate(steps):
        px = x0 + k * (pw + gap)
        box(px, py, pw, ph, PILL, PILL_EC, 0.5, rs=1.6)
        ax.text(px + pw / 2, py + ph / 2, s, ha="center", va="center", fontsize=7, color=INK, linespacing=1.15)
        if k < 2:
            ax.add_patch(FancyArrowPatch((px + pw + 0.6, py + ph / 2), (px + pw + gap - 0.6, py + ph / 2),
                                         arrowstyle="-|>", mutation_scale=7, lw=0.9, color=MID, shrinkA=0, shrinkB=0))
    ax.text(LX + LW / 2, 24.0, "2,977 grid cells · 5 climate models · today and 2050",
            ha="center", va="center", fontsize=7, color=MID)

    # ---- findings box
    box(LX, 1.5, LW, 19.8, PALE, PALE_EC, 0.6)
    big, _ = fmt_cap(head)
    mult = num.get("frame.head_multiple", num.get("frame.main_multiple", "[N]"))
    p = a.future.split("_")[0]
    scen = {"ssp585": "SSP5-8.5", "ssp245": "SSP2-4.5"}.get(p, "SSP5-8.5")
    ch, ech = num.get(f"{p}.change_pct", "[±X]"), num.get(f"{p}.energy_change_pct", "[±X]")
    cer = f"{grp['cereals']:.0f}%" if "cereals" in grp else "[x]%"
    leg = f"{grp['legumes']:.0f}%" if "legumes" in grp else "[y]%"
    land = num.get("head.land_mha", "[X]")
    rows = [(big, f"on {land} Mha of cropland ({hlabel}),\n≈ {mult}× India's yearly electricity use"),
            (f"{cer} | {leg}", "max panel cover,\ncereals | legumes"),
            (f"{ch}%", f"capacity by 2050 ({scen}),\nannual energy {ech}%")]
    VX = LX + 2.0                             # value column; descriptions start at a common x
    vs = [ax.text(VX, 0, v, fontsize=10, fontweight="bold") for v, _ in rows]
    TX = max(t.get_window_extent(r).transformed(ax.transData.inverted()).x1 for t in vs) + 2.0
    for t in vs:
        t.remove()
    for (v, t), y in zip(rows, (17.8, 11.4, 5.0)):
        ax.text(VX, y, v, ha="left", va="center", fontsize=10, fontweight="bold", color=ACC)
        ax.text(TX, y, t, ha="left", va="center", fontsize=7, color=INK, linespacing=1.05)

    # ---- map
    MX, MY, MH = 70.0, 1.0, 48.0
    MW = MH * 29.5 * np.cos(np.radians(22)) / 30.8
    b = axes_mm(MX, MY, MW, MH)
    b.set_facecolor("none")
    for s in b.spines.values():
        s.set_visible(False)
    india, _ = india_outline(a)
    bounds = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7001]
    cmap = ListedColormap(plt.colormaps["viridis"](np.linspace(0, 1, len(bounds) - 1)))
    norm = BoundaryNorm(bounds, cmap.N)
    india.plot(ax=b, color="#ECECEC", edgecolor="none")
    if cells is not None:
        lon, lat, v = cells
        lons = np.round(np.arange(68.125, 97.5, 0.25), 3); lats = np.round(np.arange(6.625, 37.25, 0.25), 3)
        z = np.full((len(lats), len(lons)), np.nan)
        z[np.searchsorted(lats, np.round(lat, 3)), np.searchsorted(lons, np.round(lon, 3))] = v
        b.pcolormesh(np.append(lons - 0.125, lons[-1] + 0.125), np.append(lats - 0.125, lats[-1] + 0.125),
                     np.ma.masked_invalid(z), cmap=cmap, norm=norm, edgecolors="none", rasterized=True)
    india.boundary.plot(ax=b, color="#555555", lw=0.45)
    b.set_xlim(68, 97.5); b.set_ylim(6.5, 37.3); b.set_aspect(1 / np.cos(np.radians(22)))
    b.set_xticks([]); b.set_yticks([]); b.set_xlabel(""); b.set_ylabel("")
    # vertical colour bar east of the map, beside the Bay of Bengal, title above it
    cbx, cby, cbh = MX + MW + 3.0, 6.0, 17.0
    cb_ax = axes_mm(cbx, cby, 1.6, cbh)
    ticks = [0, 0.35, 0.7]
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cb_ax, ticks=ticks)
    cb.ax.set_yticklabels([f"{100 * t:.0f}%" for t in ticks])
    cb.ax.tick_params(labelsize=7, labelcolor=MID, length=1.5, width=0.5, pad=1)
    cb.ax.minorticks_off()
    cb.outline.set_linewidth(0.4)
    ax.text(cbx - 0.3, cby + cbh + 1.5, f"Max panel\ncover at\n≥ {pct}% yield", ha="left", va="bottom", fontsize=7,
            color=INK, fontweight="medium", linespacing=1.1)

    a.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out.with_suffix(".pdf"))
    fig.savefig(a.out.with_suffix(".png"), dpi=600)
    check_layout(fig, [(LX, LW, 0, H)])
    write_caption(a, hlabel, scen)
    print("wrote", a.out.with_suffix(".png"), "|", big, hlabel, "| x", mult, "| 2050", ch, ech, "|", cer, leg)


if __name__ == "__main__":
    main()
