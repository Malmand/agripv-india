"""Figure: modelled vs measured relative PPFD at ICAR-CAZRI (Santra et al., 2021)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parent
d = pd.read_csv(ROOT / "results/validation_cazri_light.csv")
d = d[d.case == "broadband diffuse"]

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 7, "axes.linewidth": 0.75,
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.direction": "out", "ytick.direction": "out", "pdf.fonttype": 42,
    "legend.frameon": False,
})
COL = {"Block 1": "#E69F00", "Block 2": "#0072B2", "Block 3": "#009E73"}
MK = {"09:30": "o", "12:30": "s", "15:30": "^"}
LAB = {"09:30": "09-10 h", "12:30": "12-13 h", "15:30": "15-16 h"}

fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.3))
for ax, v, title, lab in [(axes[0], "total", "Whole system (pitch average)", "A"),
                           (axes[1], "below", "Below PV array", "B")]:
    lim = (0.4, 0.7) if v == "total" else (0.0, 0.6)
    ax.plot(lim, lim, color="black", lw=0.6, ls=(0, (4, 2)))
    for _, r in d.iterrows():
        ax.plot(r[f"obs_{v}"], r[f"mod_{v}"], ls="none", marker=MK[r.time], ms=5,
                color=COL[r.block], mec="white", mew=0.5)
    e = d[f"mod_{v}"] - d[f"obs_{v}"]
    ax.text(0.04, 0.96, f"Bias {e.mean():+.3f}\nRMSE {np.sqrt((e ** 2).mean()):.3f}",
            transform=ax.transAxes, va="top", fontsize=7)
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=8, loc="left", pad=4)
    ax.text(-0.2, 1.04, lab, transform=ax.transAxes, fontsize=11, fontweight="bold", va="bottom")
    ax.set_xlabel("Measured PPFD / unshaded PPFD (–)", fontsize=8)
    ax.set_ylabel("Modelled irradiance / unshaded (–)", fontsize=8)
h = [plt.Line2D([], [], ls="none", marker="o", color=c, ms=5, label=b) for b, c in COL.items()]
h += [plt.Line2D([], [], ls="none", marker=m, color="0.4", ms=5, label=LAB[t]) for t, m in MK.items()]
fig.legend(handles=h, loc="lower center", ncol=6, fontsize=7, bbox_to_anchor=(0.5, -0.01))
fig.tight_layout(rect=(0, 0.07, 1, 1))
fig.savefig(ROOT / "results/fig_validation_cazri_light.pdf")
fig.savefig(ROOT / "results/fig_validation_cazri_light.png", dpi=400)
print("saved")
