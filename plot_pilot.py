"""Figure: relative yield vs GCR for the Jodhpur pilot (journal style)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parent
import sys
SCEN = sys.argv[1] if len(sys.argv) > 1 else "soilgrids_F"
summ = pd.read_csv(ROOT / "results" / SCEN / "pilot_summary.csv")

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 7, "axes.linewidth": 0.75,
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.direction": "out", "ytick.direction": "out",
    "xtick.major.width": 0.75, "ytick.major.width": 0.75,
    "xtick.minor.visible": False, "ytick.minor.visible": False,
    "pdf.fonttype": 42, "legend.frameon": False,
})
STY = {  # Okabe-Ito, distinct marker + line style per configuration
    "south_fixed": dict(color="#E69F00", marker="o", ls="-", label="Elevated fixed, south"),
    "ew_fixed": dict(color="#0072B2", marker="s", ls="--", label="Elevated fixed, east-west"),
    "vertical": dict(color="#009E73", marker="^", ls=":", label="Vertical bifacial"),
}
CROPS = [("wheat", "Wheat (rabi, irrigated)"), ("chickpea", "Chickpea (rabi, irrigated)"),
         ("pearl_millet", "Pearl millet (kharif, rainfed)"), ("groundnut", "Groundnut (kharif, irrigated)")]

fig, axes = plt.subplots(2, 2, figsize=(7.0, 5.0), sharex=True, sharey=False)
for ax, (key, title), lab in zip(axes.flat, CROPS, "ABCD"):
    s = summ[summ.crop == key].rename(columns={"ry": "mean", "ry_sd": "std"})
    for cfg, st in STY.items():
        e = s[s.config == cfg]
        x = pd.concat([pd.Series([0.0]), e.gcr]).values
        m = pd.concat([pd.Series([1.0]), e["mean"]]).values
        sd = pd.concat([pd.Series([0.0]), e["std"]]).values
        ax.errorbar(x, m, yerr=sd, color=st["color"], marker=st["marker"], ls=st["ls"],
                    lw=1.0, ms=4, capsize=2, elinewidth=0.6, label=st["label"])
    ax.axhline(0.80, color="black", lw=0.6, ls=(0, (4, 2)))
    ax.axhline(0.66, color="0.55", lw=0.5, ls=(0, (1, 2)))
    ax.set_title(title, fontsize=8, loc="left", pad=4)
    ax.text(-0.16, 1.06, lab, transform=ax.transAxes, fontsize=11, fontweight="bold", va="bottom")
    ax.set_xticks([0, 0.1, 0.2, 0.3, 0.4, 0.5])
    ax.set_ylim(0, 1.6 if key == "pearl_millet" else 1.15)
for ax in axes[1]:
    ax.set_xlabel("Ground coverage ratio, GCR (–)", fontsize=8)
for ax in axes[:, 0]:
    ax.set_ylabel("Relative yield, RY (–)", fontsize=8)
axes[1, 1].text(0.505, 0.815, "80% threshold", fontsize=6, ha="right", va="bottom")
axes[1, 1].text(0.505, 0.675, "66%", fontsize=6, ha="right", va="bottom", color="0.4")
h, l = axes[0, 0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=3, fontsize=7, bbox_to_anchor=(0.5, -0.01))
fig.tight_layout(rect=(0, 0.05, 1, 1))
out = ROOT / "results" / SCEN
fig.savefig(out / "fig_pilot_ry_vs_gcr.pdf")
fig.savefig(out / "fig_pilot_ry_vs_gcr.png", dpi=400)
print("saved")
