"""Fig. 1: methodology flowchart (readable at print size)."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon

plt.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42, "mathtext.default": "regular"})
TF, BF = 9.2, 8.4                      # title and body font sizes (pt) at 6.2 in width
fig = plt.figure(figsize=(6.2, 6.4))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 96.5); ax.axis("off")
C = {"data": ("white", "0.45"), "proc": ("#DCEBF5", "#0072B2"), "out": ("#FCEFD2", "#E69F00"), "dec": ("#FBE3D6", "#D55E00")}
XI, WI, XP, WP, XO, WO = 2.5, 25.0, 36.0, 28.0, 72.5, 25.0


def box(x, y, w, h, title, body, kind):
    fc, ec = C[kind]
    if kind == "data":
        s = 1.4
        ax.add_patch(Polygon([(x + s, y), (x + w, y), (x + w - s, y + h), (x, y + h)], fc=fc, ec=ec, lw=0.8))
    else:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={2.0 if kind == 'out' else 0.7}",
                                    fc=fc, ec=ec, lw=0.9))
    ax.text(x + w / 2, y + h * 0.66, title, ha="center", va="center", fontsize=TF, fontweight="bold")
    ax.text(x + w / 2, y + h * 0.30, body, ha="center", va="center", fontsize=BF, color="0.2")
    return dict(l=(x, y + h / 2), r=(x + w, y + h / 2), t=(x + w / 2, y + h), b=(x + w / 2, y))


def arrow(p, q, ls="-"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=9, lw=0.9, color="0.2", linestyle=ls,
                                 shrinkA=0, shrinkB=0.5))


def line(*pts):
    for p, q in zip(pts[:-1], pts[1:]):
        ax.plot([p[0], q[0]], [p[1], q[1]], color="0.2", lw=0.9, solid_capstyle="butt")


def band(y0, y1, label):
    ax.add_patch(FancyBboxPatch((0.8, y0), 98.4, y1 - y0, boxstyle="round,pad=0,rounding_size=1.2", fc="0.965", ec="0.85", lw=0.5))
    ax.text(2.0, y1 - 1.0, label, ha="left", va="top", fontsize=TF - 0.4, fontweight="bold", color="0.35")


for x, w, t in ((XI, WI, "Data"), (XP, WP, "Models"), (XO, WO, "Outputs")):
    ax.text(x + w / 2, 95.0, t, ha="center", va="center", fontsize=TF + 0.6, fontweight="bold")
ax.plot([1, 99], [93.3, 93.3], color="0.6", lw=0.5)

H = 9.0
# A light
band(78.0, 92.5, "A  Light (2.2)")
cl = box(XI, 79.2, WI, H, "Climate", "5 GCMs × 3 periods", "data")
lm = box(XP, 79.2, WP, H, "Light model", "3 layouts × GCR 0.05–0.7", "proc")
lf = box(XO, 79.2, WO, H, "Light factor", "per ground strip", "out")
arrow(cl["r"], lm["l"]); arrow(lm["r"], lf["l"])

# B crop
band(47.5, 76.5, "B  Crop model (2.3–2.4)")
cs = box(XI, 63.0, WI, H, "Land and soils", "area, calendar, soil", "data")
ob = box(XI, 50.5, WI, H, "Observed yields", "ICRISAT, by state", "data")
ds = box(XP, 63.0, WP, H, "DSSAT", "4 crops, open + shaded", "proc")
cb = box(XP, 50.5, WP, H, "Nitrogen calibration", "wheat, pearl millet", "proc")
yo = box(XO, 63.0, WO, H, "Crop yields", "open field and per strip", "out")
arrow(cs["r"], ds["l"]); arrow(ob["r"], cb["l"]); arrow(ds["r"], yo["l"])
arrow(cb["t"], ds["b"], ls="--")
ax.text(XP + WP / 2 + 1.2, 60.75, "state nitrogen", fontsize=BF - 0.6, style="italic", color="0.3", va="center")
line(lf["b"], (lf["b"][0], 77.25), (XP + WP * 0.8, 77.25)); arrow((XP + WP * 0.8, 77.25), (XP + WP * 0.8, 72.0))
line((XI + 5, 79.2), (XI + 5, 77.25), (XP + WP * 0.2, 77.25)); arrow((XP + WP * 0.2, 77.25), (XP + WP * 0.2, 72.0))

# C yield constraint
band(22.0, 46.0, "C  Yield constraint (2.5)")
th = box(XI, 25.5, WI, H, "Thresholds τ", "0.66, 0.80, 0.90", "data")
ry = box(XP, 34.5, WP, 7.5, "Relative yield", "RY = shaded / open", "proc")
cx, cy, dw, dh = XP + WP / 2, 28.0, 17.0, 8.6
fc, ec = C["dec"]
ax.add_patch(Polygon([(cx, cy + dh / 2), (cx + dw / 2, cy), (cx, cy - dh / 2), (cx - dw / 2, cy)], fc=fc, ec=ec, lw=0.9))
ax.text(cx, cy, "RY ≥ τ ?", ha="center", va="center", fontsize=TF, fontweight="bold")
gm = box(XO, 25.5, WO, H, "GCR$_{max}$", "largest GCR passing", "out")
line(yo["r"], (98.2, yo["r"][1]), (98.2, 46.75), (cx, 46.75)); arrow((cx, 46.75), ry["t"])
arrow(ry["b"], (cx, cy + dh / 2)); arrow(th["r"], (cx - dw / 2, cy)); arrow((cx + dw / 2, cy), gm["l"])

# D potential
band(1.0, 17.6, "D  Capacity and energy (2.5)")
tr = box(XI, 2.8, WI, H, "Terrain and PV", "slope ≤ 5%, bifacial", "data")
ce = box(XP, 2.8, WP, H, "Capacity and energy", "eligible land × GCR$_{max}$", "proc")
rs = box(XO, 2.8, WO, H, "Results", "maps, TWp, PWh", "out")
arrow(tr["r"], ce["l"]); arrow(ce["r"], rs["l"])
line(gm["b"], (gm["b"][0], 19.8), (XP + WP / 2, 19.8)); arrow((XP + WP / 2, 19.8), ce["t"])

fig.savefig("fig1_flow.pdf"); fig.savefig("fig1_flow.png", dpi=400)
