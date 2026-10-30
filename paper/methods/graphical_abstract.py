"""Fig. 1: modelling framework (graphical flowchart)."""
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7, "pdf.fonttype": 42})
BLUE, SKY, GREEN, ORANGE, VERM, GREY = "#0072B2", "#56B4E9", "#009E73", "#E69F00", "#D55E00", "0.25"
W, H = 7.2, 4.15
fig = plt.figure(figsize=(W, H))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 58); ax.axis("off")


def rbox(x, y, w, h, fc, ec, lw=0.8, r=1.4):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw))


def arrow(x1, y1, x2, y2, c=GREY, lw=1.0, ms=9, cs="arc3"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=ms, lw=lw, color=c,
                                 connectionstyle=cs, shrinkA=0, shrinkB=0))


def inset(x, y, w, h):
    a = fig.add_axes([x / 100, y / 58, w / 100, h / 58])
    a.set_facecolor("none")
    for s in a.spines.values():
        s.set_visible(False)
    a.set_xticks([]); a.set_yticks([])
    return a


# ---------------- inputs row ----------------
inputs = [("Climate", "NEX-GDDP-CMIP6\n5 GCMs, 3 periods"), ("Soil", "SoilGrids 2.0\nprofiles to 2 m"),
          ("Cropland", "MapSPAM area, irrigation\nGGCMI sowing dates"), ("Observed yields", "ICRISAT state means\n1995–2014"),
          ("Terrain", "Copernicus DEM\nslope")]
xs = [1.5, 21.3, 41.1, 60.9, 80.7]
for (t, s), x in zip(inputs, xs):
    rbox(x, 45.5, 17.8, 9, "white", "0.55", lw=0.6)
    ax.text(x + 8.9, 52.4, t, ha="center", va="center", fontweight="bold", fontsize=7)
    ax.text(x + 8.9, 48.4, s, ha="center", va="center", fontsize=5.9, color="0.2", linespacing=1.25)
ax.text(1.6, 57.4, "INPUTS (0.25° grid, 2977 cropland cells)", fontsize=6, color="0.35", va="top", fontweight="bold")

# ---------------- process row ----------------
steps = [("1", "Light below panels", BLUE, "#E5F1F8"), ("2", "Crop growth", GREEN, "#E3F3EE"),
         ("3", "Yield limit", VERM, "#FBEAE1"), ("4", "Potential", ORANGE, "#FCF1DC")]
px = [1.5, 26.3, 51.1, 75.9]; pw, py, ph = 22.6, 9.5, 29.5
for (n, t, c, fc), x in zip(steps, px):
    rbox(x, py, pw, ph, fc, c, lw=1.0)
    ax.add_patch(plt.Circle((x + 3.2, py + ph - 3.3), 2.0, color=c))
    ax.text(x + 3.2, py + ph - 3.35, n, color="white", ha="center", va="center", fontweight="bold", fontsize=7.5)
    ax.text(x + 6.3, py + ph - 3.3, t, ha="left", va="center", fontweight="bold", fontsize=7.6, color="0.1")
for a, b in zip(px[:-1], px[1:]):
    arrow(a + pw + 0.2, py + ph / 2, b - 0.2, py + ph / 2, lw=1.3, ms=10)

# step texts
txt = ["Hourly sun and sky light\non 5 ground strips, for 3\nlayouts and GCR 0.05–0.7",
       "DSSAT, 4 crops, irrigated\nand rainfed; N calibrated\nby state",
       "Largest GCR with RY ≥\n0.66, 0.80 or 0.90",
       "Crop area on slopes ≤ 5% × GCR\n→ capacity and energy"]
for x, t in zip(px, txt):
    ax.text(x + pw / 2, py + 1.3, t, ha="center", va="bottom", fontsize=5.9, color="0.15", linespacing=1.25)

# --- mini graphic 1: cross-section with light on strips
a = inset(px[0] + 1.5, py + 9.6, pw - 3, 14.5)
for k in range(2):
    a.plot([k * 6.7, k * 6.7 + 1.8], [3, 3.85], color=BLUE, lw=2.2, solid_capstyle="butt")
    a.plot([k * 6.7 + 0.9, k * 6.7 + 0.9], [0, 3.4], color="0.5", lw=0.7)
f = [0.25, 0.55, 0.85, 0.95, 0.65]
for i, v in enumerate(f):
    a.add_patch(Rectangle((1.2 + i * 1.08, -0.55), 1.0, 0.45, color=plt.cm.YlOrBr(0.05 + 0.55 * v), lw=0))
for xx in (3.6, 5.2):
    a.annotate("", (xx - 0.9, 0.1), (xx + 0.6, 3.9), arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=0.8, mutation_scale=6))
a.text(4.3, 4.4, "☀", ha="center", va="center", fontsize=9, color=ORANGE)
a.text(3.85, -1.15, "light factor per strip", ha="center", va="center", fontsize=5.2, color="0.3")
a.set_xlim(-0.5, 8.6); a.set_ylim(-1.6, 4.9)

# --- mini graphic 2: yield per strip vs open field
a = inset(px[1] + 3.0, py + 10.3, pw - 6, 12.8)
yv = [0.62, 0.78, 0.9, 0.95, 0.84]
a.bar(range(5), yv, color=GREEN, width=0.7, alpha=0.85)
a.bar([5.4], [1.0], color="0.6", width=0.7)
a.axhline(1.0, color="0.6", lw=0.5, ls=":")
a.set_xticks(list(range(5)) + [5.4]); a.set_xticklabels(["S1", "S2", "S3", "S4", "S5", "open"], fontsize=5)
a.tick_params(length=0, pad=1)
a.spines["bottom"].set_visible(True); a.spines["bottom"].set_linewidth(0.5)
a.set_ylim(0, 1.15)
a.text(-0.6, 1.12, "yield", fontsize=5.2, color="0.3", va="top")

# --- mini graphic 3: RY vs GCR with thresholds
a = inset(px[2] + 3.6, py + 10.6, pw - 6.6, 12.5)
g = np.linspace(0, 0.7, 50); ry = 1 - 0.55 * g - 0.35 * g ** 2
a.plot(g, ry, color=VERM, lw=1.3)
a.axhline(0.8, color="0.3", lw=0.6, ls="--")
gm = g[np.argmin(abs(ry - 0.8))]
a.plot([gm, gm], [0.4, 0.8], color="0.3", lw=0.6, ls="--")
a.plot(gm, 0.8, "o", ms=3, color="0.1")
a.text(gm + 0.02, 0.43, "GCR$_{max}$", fontsize=5.4, va="bottom")
a.text(0.69, 0.81, "τ = 0.8", fontsize=5.2, ha="right", va="bottom", color="0.3")
a.set_xlim(0, 0.72); a.set_ylim(0.4, 1.03)
for s in ("left", "bottom"):
    a.spines[s].set_visible(True); a.spines[s].set_linewidth(0.5)
a.set_xlabel("GCR", fontsize=5.2, labelpad=1); a.set_ylabel("RY", fontsize=5.2, labelpad=1)

# --- mini graphic 4: India outline
a = inset(px[3] + 4.5, py + 9.4, pw - 9, 15.4)
try:
    st = gpd.read_file("../../data/boundaries/Admin2.shp")
    india = st.dissolve().simplify(0.05)
    india.plot(ax=a, color="#F6D58E", edgecolor=ORANGE, lw=0.5)
    a.set_xlim(68, 97.5); a.set_ylim(6.5, 37.3); a.set_aspect(1 / np.cos(np.radians(22))); a.set_xlabel(""); a.set_ylabel("")
except Exception:
    a.text(0.5, 0.5, "India", ha="center")
a.set_xticks([]); a.set_yticks([])

# ---------------- input -> step arrows (targets ordered like sources: no crossings) ----------------
top = py + ph + 0.3
arrow(xs[0] + 6, 45.3, px[0] + pw / 2, top, c="0.45", lw=0.8, ms=7)         # climate -> light
arrow(xs[0] + 12, 45.3, px[1] + 4, top, c="0.45", lw=0.8, ms=7)            # climate -> crop
arrow(xs[1] + 8.9, 45.3, px[1] + 9, top, c="0.45", lw=0.8, ms=7)           # soil -> crop
arrow(xs[2] + 8.9, 45.3, px[1] + 14, top, c="0.45", lw=0.8, ms=7)          # cropland -> crop
arrow(xs[3] + 8.9, 45.3, px[1] + 19, top, c="0.45", lw=0.8, ms=7)          # observed yields -> crop (calibration)
arrow(xs[4] + 8.9, 45.3, px[3] + pw / 2, top, c="0.45", lw=0.8, ms=7)      # terrain -> potential
# ---------------- bottom banner ----------------
rbox(1.5, 1.2, 97.0, 6.0, "#F2F2F2", "none")
ax.text(50, 4.2, "Repeated for every cell × 5 climate models × 3 periods (1995–2014; 2041–2060 SSP2-4.5 and SSP5-8.5)"
        "  →  maps and totals as 5-model median and range", ha="center", va="center", fontsize=6.2, color="0.15")

fig.savefig("graphical_abstract.pdf"); fig.savefig("graphical_abstract.png", dpi=500)
