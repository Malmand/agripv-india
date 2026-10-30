import sys; sys.path.insert(0, "../../prod")
import numpy as np, matplotlib.pyplot as plt
import pv_shading as ps
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7, "axes.linewidth": 0.6, "pdf.fonttype": 42,
    "xtick.direction": "out", "ytick.direction": "out", "axes.spines.top": False, "axes.spines.right": False})
G = 0.3
fig, axs = plt.subplots(1, 3, figsize=(7.0, 2.3), constrained_layout=True)
titles = {"south_fixed": "South-facing, elevated (tilt 25°)", "ew_fixed": "East-west ridge, elevated (tilt 10°)",
          "vertical": "Vertical bifacial (east/west faces)"}
xlab = {"south_fixed": "Distance south to north (m)", "ew_fixed": "Distance west to east (m)", "vertical": "Distance west to east (m)"}
for ax, (k, lab) in zip(axs, zip(titles, "ABC")):
    cfg = ps.make_config(k); geo = ps.strip_geometry(cfg, G); p = geo["pitch"]
    for r in range(-1, 2):
        for s in cfg.segments:
            ax.plot([s[0] + r*p, s[2] + r*p], [s[1], s[3]], color="#0072B2", lw=2.2, solid_capstyle="butt")
        xm = np.mean([s[0] for s in cfg.segments] + [s[2] for s in cfg.segments]) + r*p
        ax.plot([xm, xm], [0, min(min(s[1], s[3]) for s in cfg.segments)], color="0.45", lw=0.8)
    xr = np.mean([s[0] for s in cfg.segments] + [s[2] for s in cfg.segments])
    x0 = xr + cfg.uncultivated/2; L = p - cfg.uncultivated
    for i in range(5):
        ax.add_patch(plt.Rectangle((x0 + i*L/5, -0.35), L/5*0.94, 0.3, color=plt.cm.viridis(0.25 + 0.15*i), lw=0))
        ax.text(x0 + (i+0.47)*L/5, -0.75, f"S{i+1}", ha="center", va="top", fontsize=5.5)
    ax.axhline(0, color="0.3", lw=0.6)
    ax.annotate("", (xr + p, 5.6), (xr, 5.6), arrowprops=dict(arrowstyle="<->", lw=0.6))
    ax.text(xr + p/2, 5.75, f"pitch {p:.1f} m", ha="center", va="bottom", fontsize=6)
    ax.set_xlim(xr - 0.35*p, xr + 1.35*p); ax.set_ylim(-1.4, 6.6)
    ax.set_xlabel(xlab[k]); ax.set_ylabel("Height (m)" if lab == "A" else "")
    ax.set_title(titles[k], fontsize=7)
    ax.text(-0.02, 1.08, lab, transform=ax.transAxes, fontsize=10, fontweight="bold", ha="right")
fig.savefig("fig2_layouts.pdf"); fig.savefig("fig2_layouts.png", dpi=400)
