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
import json
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import geopandas as gpd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
import fig_india as FI  # noqa: E402
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
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
    sys.argv += [] if any(x.startswith("--out") for x in sys.argv) else ["--out", str(HERE / "graphical_abstract_v4")]
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
        "cell with slope ≤ 5%); cells with less than 1000 ha are blank, the top of the scale (70%) is the largest cover simulated, and the 0.25° values are interpolated for display. The map is the crop-model (upper) case. Capacity is the crops-combined total "
        "with double-cropped land counted once (median of five GCMs); the lower end of the range rescales the simulated relative yield to "
        "field observations of yield under reduced light, and the upper end is the crop-model case. Cereal and legume "
        "values are eligible-area-weighted means; the call-outs give the share of the field covered by panels, the same mean, for the wheat belt (24–31°N, "
        "74–88°E) and the Deccan (12–21°N, 73–80°E); The 2050 values are the changes by 2041–2060 under "
        f"{scen} against 1995–2014 (five-GCM median, "
        + ("robust case" if "ssp585r.change_pct" in json.load(open(ROOT / "results/potential/numbers.json"))["values"] else "calibrated nitrogen")
        + "). " + GA.BOUNDARY_SRC)
    _v = json.load(open(a.pp / "numbers.json"))["values"] if (a.pp / "numbers.json").exists() else {}
    if "rice.cap_twp" in _v:
        txt += (f" With the rice that follows wheat or chickpea also held to {a.thr:.0%} of its yield (CERES-Rice), "
                f"the robust capacity is {_v['rice.cap_twp']} TWp.")
    txt += (" The curves are the area-weighted national mean relative yield of wheat and chickpea against the share of "
            "land under panels (east-west layout, recommended nitrogen, 1995–2014); the panel limit is where a curve "
            f"crosses {a.thr:.0%}. GCMs, global climate models.")
    (HERE / "graphical_abstract_v4_caption.txt").write_text(txt + "\n")


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


def rule_curves(a):
    """Area-weighted national mean relative yield against GCR, east-west layout, recommended nitrogen
    (the conservative nitrogen case), 1995-2014: the curves whose 80% crossing sets the panel limit."""
    f = ROOT / "runs/s1/summary/ry_crop_historical_recommended.csv.gz"
    if not f.exists():
        return {}
    d = pd.read_csv(f); d = d[d.config == a.config]
    g = pd.read_csv(a.grid).set_index("cell_id")
    out = {}
    for c in ("wheat", "chickpea"):
        x = d[d.crop == c]
        if "water" in x and "all" in set(x.water):
            x = x[x.water == "all"]
        m = x.groupby(["cell", "gcr"]).ry.median().reset_index()
        m["w"] = m.cell.map(g[f"{c}_ha"])
        cur = m.groupby("gcr").apply(lambda t: np.average(t.ry, weights=t.w), include_groups=False)
        out[c] = (np.r_[0.0, cur.index.values], np.r_[1.0, cur.values])
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
            if width(t) <= maxw or size <= 6.5:
                return t
            t.remove(); size -= 0.25

    LX, LW = 1.5, 66.0
    gap = 2.4
    cw = (LW - 2 * gap) / 3                   # width of a step pill and of a finding card
    LBL = dict(fontsize=7, fontweight="bold", color=ACC)                  # small section labels

    # ---- left top: what the model does (drawn), and the rule it applies (real curves)
    p = a.future.split("_")[0]
    scen = {"ssp585": "SSP5-8.5", "ssp245": "SSP2-4.5"}.get(p, "SSP5-8.5")
    big, _ = fmt_cap(head)
    ch = num.get("fut.change_pct", num.get(f"{p}.change_pct", "[±X]"))
    mult = num.get("frame.head_multiple", "[N]")
    cer = f"{grp['cereals']:.0f}%" if "cereals" in grp else "[x]%"
    leg = f"{grp['legumes']:.0f}%" if "legumes" in grp else "[y]%"
    C_W, C_L = "#009E73", "#D55E00"                 # Okabe-Ito: wheat (bluish green), chickpea (vermillion)
    GRN, GRN2, SHD = "#3E8E41", "#A9D19A", "#C4C4C4"
    TOP, BOT = 49.0, 26.0                            # top row band (mm)

    # (1) cross-section: east-west module pairs, incoming light, shaded and sunlit crop strips (technical sketch)
    SX, SWD = LX, 23.0
    box(SX, BOT, SWD, TOP - BOT, "#F4F6F8", "#C9D2DC", 0.5, rs=1.0)
    ax.text(SX + 1.4, TOP - 2.4, "Crop under panels", ha="left", va="center", fontsize=7.5, fontweight="bold", color=INK)
    nc = "5" if "rice.cap_twp" in num else "4"
    ax.text(SX + 1.4, TOP - 5.0, f"3 layouts, {nc} crops", ha="left", va="center", fontsize=6.5, color=MID)
    gy = BOT + 4.0
    posts = [SX + 5.5, SX + 11.25, SX + 17.0]
    for k in range(5):                                                     # light from above, slightly inclined
        x0 = SX + 2.6 + k * 4.0
        ax.annotate("", xy=(x0 + 1.0, gy + 8.6), xytext=(x0 + 1.8, gy + 11.6),
                    arrowprops=dict(arrowstyle="-|>", lw=0.5, color="#B8862B", mutation_scale=4, shrinkA=0, shrinkB=0))
    ax.add_patch(plt.Rectangle((SX + 1.2, gy - 1.6), SWD - 2.4, 1.6, fc="#E3D9C6", ec="none"))  # soil
    for x in np.arange(SX + 1.6, SX + SWD - 1.4, 0.9):                     # crop canopy: darker where sunlit
        shaded = any(abs(x - c) < 2.0 for c in posts)
        ax.add_patch(plt.Rectangle((x, gy), 0.7, 1.3 if shaded else 2.0, fc="#9CC79A" if shaded else "#3E8E41", ec="none"))
    for cx in posts:
        top = gy + 7.6
        ax.plot([cx, cx], [gy, top], color="#6E6E6E", lw=0.6)
        ax.plot([cx - 2.4, cx, cx + 2.4], [top - 1.2, top, top - 1.2], color=NAVY, lw=1.8, solid_joinstyle="miter")
    ax.text(SX + SWD / 2, BOT + 1.3, "light per crop strip", ha="center", va="center", fontsize=6.5, color=MID)

    # (2) the rule: relative yield against panel cover, national means (east-west, recommended N, 1995-2014)
    RX0 = SX + SWD + 2.0
    ax.text(RX0, TOP - 2.4, f"Panel limit at {pct}% yield", ha="left", va="center", fontsize=7.5,
            fontweight="bold", color=INK)
    PX, PY = RX0 + 7.6, BOT + 5.4
    PW, PHH = LX + LW - PX - 0.6, TOP - BOT - 9.6
    rax = axes_mm(PX, PY, PW, PHH)
    curves = rule_curves(a)
    rax.axhspan(a.thr, 1.08, color="#EAF2EA", lw=0, zorder=0)
    rax.text(0.715, 1.065, "allowed", fontsize=6.5, color="#4F7F52", ha="right", va="top", style="italic")
    rax.axhline(a.thr, color=INK, lw=0.7, ls="--", zorder=1)
    for crop_, col, lx, ly, ha in (("wheat", C_W, 0.16, 1.058, "left"), ("chickpea", C_L, 0.02, 0.6, "left")):
        if crop_ in curves:
            gx, ry = curves[crop_]
            rax.plot(gx, ry, color=col, lw=1.6, zorder=3)
            xc = float(np.interp(a.thr, ry[::-1], gx[::-1])) if ry.min() < a.thr else float(gx.max())
            rax.plot([xc, xc], [0.5, a.thr], color=col, lw=0.8, ls=":", zorder=2)
            rax.plot(xc, a.thr, "o", ms=3.4, mfc="white", mec=col, mew=1.1, zorder=5)
            rax.text(xc + 0.01, 0.508, f"{100 * xc:.0f}%", color=col, fontsize=6.5, fontweight="bold", ha="left", va="bottom")
            rax.text(lx, ly, crop_, color=col, fontsize=7, fontweight="bold", ha=ha, va="center")
    rax.set_xlim(0, 0.72); rax.set_ylim(0.5, 1.08)
    rax.set_xticks([0, 0.2, 0.4, 0.6]); rax.set_xticklabels(["0", "20%", "40%", "60%"])
    rax.set_yticks([0.6, 0.8, 1.0]); rax.set_yticklabels(["60%", "80%", "100%"])
    rax.tick_params(labelsize=6.5, length=2, width=0.5, pad=1, colors=INK)
    for sp_ in ("top", "right"):
        rax.spines[sp_].set_visible(False)
    for sp_ in ("left", "bottom"):
        rax.spines[sp_].set_linewidth(0.6)
    rax.set_xlabel("land covered by panels", fontsize=6.5, color=INK, labelpad=0.2)
    rax.set_ylabel("yield kept", fontsize=6.5, color=INK, labelpad=0.4)

    # ---- bottom: one results panel, three columns (label, number, unit, takeaway), left-aligned
    py0, ph = 1.5, 21.5
    box(LX, py0, LW, ph, "#F4F6F8", "#C9D2DC", 0.5, rs=1.0)
    colw = LW / 3
    NUM = dict(fontweight="bold", color=NAVY, ha="left", va="center")
    sz = num.get("fut.size", "small")
    take1 = f"{num['rice.cap_twp']} TWp with rice" if "rice.cap_twp" in num else f"{mult}× India's use"
    cols = [("POTENTIAL", [(f"{num.get('field.ew.t80.cap_twp', '[X]')}–{num.get('head.cap_twp_m', '[Y]')}", None)],
             "TWp at 80% yield", take1),
            ("PANEL COVER", [(cer, "cereals"), (leg, "legumes")], None, "set by the crop"),
            ("2041–2060", [(f"{ch}%", None)], f"capacity, {scen}",
             {"small": "small change", "moderate": "moderate change"}.get(sz, "large change"))]
    for k, (lab, nums, unit, take) in enumerate(cols):
        x0 = LX + k * colw + 2.2
        if k:
            ax.plot([LX + k * colw, LX + k * colw], [py0 + 2.0, py0 + ph - 2.0], color="#C9D2DC", lw=0.5)
        ax.add_patch(plt.Rectangle((x0, py0 + ph - 3.6), 0.5, 1.9, fc=ACC, ec="none"))       # small accent tick
        fit(x0 + 1.2, py0 + ph - 2.65, lab, colw - 4.0, 6.5, ha="left", va="center", fontweight="bold", color=MID)
        if len(nums) == 1:
            fit(x0, 13.4, nums[0][0], colw - 3.4, 16, **NUM)
        else:
            for jj, (v, nm) in enumerate(nums):
                xx = x0 + jj * (colw - 3.4) / 2
                fit(xx, 13.4, v, (colw - 3.4) / 2 - 0.8, 16, **NUM)
                ax.text(xx, 8.6, nm, fontsize=7, color=INK, ha="left", va="center")
        if unit:
            fit(x0, 8.6, unit, colw - 3.4, 7, color=INK, ha="left", va="center")
        fit(x0, 4.4, take, colw - 3.4, 7, color=ACC, ha="left", va="center", fontweight="bold")

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
        FI.CLIP = india.union_all().buffer(0.02)          # smoothed cells stay inside the outline
        FI.draw_cells(b, lon, lat, v, cmap, norm)
    st = gpd.read_file(a.boundaries)                 # faint state borders so the regions can be placed
    st["geometry"] = st.geometry.buffer(0.03).buffer(-0.03).simplify(0.03, preserve_topology=True)
    st.boundary.plot(ax=b, color="#FFFFFF", lw=0.35, alpha=0.75)
    india.boundary.plot(ax=b, color="#4A4A4A", lw=0.45)
    b.set_xlim(68, 97.5); b.set_ylim(6.5, 37.3); b.set_aspect(1 / np.cos(np.radians(22)))
    b.set_xticks([]); b.set_yticks([]); b.set_xlabel(""); b.set_ylabel("")

    # no north arrow or scale bar (less clutter; India's outline is self-explanatory)

    # two call-outs carry the map's story (values computed from the same map file)
    def callout(key, label, txt_lonlat, pt_lonlat):
        if key not in reg:
            return
        tx, ty = geo_to_mm(ax, b, *txt_lonlat)
        px, py_ = geo_to_mm(ax, b, *pt_lonlat)
        t = ax.text(tx, ty, label, ha="left", va="bottom", fontsize=7.5, fontweight="bold", color=INK, linespacing=0.8)
        ax.text(tx, ty - 0.3, f"{reg[key]:.0f}% covered", ha="left", va="top", fontsize=7, color=MID)
        ax.annotate("", xy=(px, py_), xytext=(tx - 0.6, ty),
                    arrowprops=dict(arrowstyle="-", lw=0.6, color=INK, shrinkA=0, shrinkB=0))
        ax.plot(px, py_, "o", ms=2.4, mfc="white", mec=INK, mew=0.7, zorder=6)
    callout("north", "Wheat belt", (86.5, 33.6), (80.5, 27.3))
    callout("deccan", "Legume-rich\nDeccan", (81.3, 10.4), (76.6, 16.6))

    # colour bar east of the map, beside the Bay of Bengal
    cbx, cby, cbh = MX + MW + 1.6, 7.6, 15.6
    cb_ax = axes_mm(cbx, cby, 1.7, cbh)
    ticks = [0, 0.35, 0.7]
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cb_ax, ticks=ticks)
    cb.ax.set_yticklabels([f"{100 * t:.0f}%" for t in ticks[:-1]] + [f"{100 * ticks[-1]:.0f}%+"])
    cb.ax.tick_params(labelsize=7, labelcolor=MID, length=1.5, width=0.5, pad=1)
    cb.ax.minorticks_off()
    cb.outline.set_linewidth(0.4)
    ax.add_patch(FancyBboxPatch((cbx - 1.4, 2.6), 1.6, 1.6, boxstyle="square,pad=0", fc="#EDEDED", ec="#4A4A4A", lw=0.4))
    ax.text(cbx + 0.9, 3.4, "not assessed", ha="left", va="center", fontsize=7, color=MID)
    ax.text(cbx - 0.2, cby + cbh + 11.6, "Max land\nunder panels", ha="left", va="bottom", fontsize=7,
            fontweight="bold", color=INK, linespacing=0.8)
    ax.text(cbx - 0.2, cby + cbh + 11.1, "per field,\neast-west\npanels", ha="left", va="top", fontsize=7, color=MID, linespacing=0.8)

    a.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out.with_suffix(".pdf"))
    fig.savefig(a.out.with_suffix(".png"), dpi=600)
    
    write_caption(a, hlabel, scen)
    print("wrote", a.out.with_suffix(".png"), "|", big, hlabel, "| x", mult, "| 2050", ch, "|", cer, leg, "|",
          {k: round(v) for k, v in reg.items()})


if __name__ == "__main__":
    main()
