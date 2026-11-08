"""Supplementary validation figures S1-S3 (journal style, PDF + PNG in results/figures/).

S1  state yields simulated vs observed, before/after N calibration (results/validation_before_after.csv)
S2  light model vs pvlib, sky view factor and sunlit fraction vs GCR (results/benchmark_pvlib.csv)
S3  light model vs CAZRI measured relative PPFD (results/validation_cazri_light.csv, broadband diffuse)

Run from the repository root: python src/fig_supp_validation.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/figures"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 7, "axes.linewidth": 0.75,
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.direction": "out", "ytick.direction": "out", "xtick.major.width": 0.75, "ytick.major.width": 0.75,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "axes.labelsize": 8, "legend.fontsize": 7,
    "legend.frameon": False, "pdf.fonttype": 42, "axes.grid": False,
})
OI = {"orange": "#E69F00", "sky": "#56B4E9", "green": "#009E73", "blue": "#0072B2",
      "vermillion": "#D55E00", "purple": "#CC79A7", "grey": "#999999"}


def panel(ax, lab):
    ax.text(-0.22, 1.04, lab, transform=ax.transAxes, fontsize=11, fontweight="bold", va="bottom")


def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf")
    fig.savefig(OUT / f"{name}.png", dpi=400)
    plt.close(fig)


# S1: state yields before and after calibration
def fig_s1():
    d = pd.read_csv(ROOT / "results/validation_before_after.csv")
    d = d[d.obs_area >= 50]
    crops = {"wheat": ("Wheat", OI["blue"], 5.0), "pearl_millet": ("Pearl millet", OI["orange"], 3.0)}
    cases = {"before": "farmer nitrogen", "after": "calibrated nitrogen"}
    fig, axs = plt.subplots(2, 2, figsize=(5.2, 5.0), constrained_layout=True)
    stats = {}
    for i, (crop, (name, col, lim)) in enumerate(crops.items()):
        for j, (case, title) in enumerate(cases.items()):
            ax = axs[i, j]
            s = d[(d.crop == crop) & (d.case == case)]
            x, y, w = s.obs / 1000, s.sim / 1000, s.obs_area
            ax.plot([0, lim], [0, lim], color="black", lw=0.6, ls=(0, (4, 2)), zorder=1)
            ax.scatter(x, y, s=8 + 40 * w / d.obs_area.max(), color=col, edgecolor="white", lw=0.4, zorder=2)
            r = np.corrcoef(x, y)[0, 1]
            mape = np.average((y / x - 1).abs(), weights=w)
            stats[(crop, case)] = (r, mape, len(s))
            ax.text(0.96, 0.04, f"r = {r:.2f}\nMean absolute\npercentage error = {100 * mape:.0f}%\nn = {len(s)} states",
                    transform=ax.transAxes, va="bottom", ha="right", fontsize=7)
            ax.set_xlim(0, lim); ax.set_ylim(0, lim); ax.set_aspect("equal")
            ax.set_title(f"{name}, {title}", fontsize=7.5, loc="left", pad=4)
            ax.set_xlabel("Observed yield (t ha$^{-1}$)")
            ax.set_ylabel("Simulated yield (t ha$^{-1}$)")
            panel(ax, "ABCD"[2 * i + j])
    save(fig, "figS1_yield_calibration")
    return stats


# S2: light model vs pvlib
def fig_s2():
    d = pd.read_csv(ROOT / "results/benchmark_pvlib.csv")
    lay = {"south_fixed": ("South-facing, tilt 25°", OI["blue"], "o"), "vertical": ("Vertical bifacial", OI["orange"], "s")}
    fig, axs = plt.subplots(1, 2, figsize=(5.4, 2.6), constrained_layout=True)
    for ax, q, ylab, lab in [(axs[0], "svf_mean", "Mean sky view factor (–)", "A"),
                             (axs[1], "sunlit_mean", "Mean hourly sunlit fraction (–)", "B")]:
        for k, (name, col, mk) in lay.items():
            s = d[d.layout == k]
            ax.plot(s.gcr, s[f"{q}_ours"], color=col, lw=1.0, label=f"{name}, this model")
            ax.plot(s.gcr, s[f"{q}_pvlib"], ls="none", marker=mk, ms=4.5, mfc="none", mec=col, mew=0.8,
                    label=f"{name}, pvlib")
        ax.set_xlim(0, 0.55); ax.set_ylim(0.4, 1.0)
        ax.set_xticks(np.arange(0, 0.51, 0.1))
        ax.set_xlabel("Ground coverage ratio (–)"); ax.set_ylabel(ylab)
        panel(ax, lab)
    axs[0].text(0.03, 0.04, f"Largest pointwise difference {d.svf_max_abs_diff.max():.3f}",
                transform=axs[0].transAxes, fontsize=6.5)
    axs[1].text(0.03, 0.04, f"Hourly mean absolute\nerror {d.sunlit_mae_hourly.min():.4f}–{d.sunlit_mae_hourly.max():.4f}",
                transform=axs[1].transAxes, fontsize=6.5)
    axs[0].legend(*axs[1].get_legend_handles_labels(), loc="upper right", fontsize=6, handlelength=1.6)
    save(fig, "figS2_light_vs_pvlib")


# S3: light model vs CAZRI measurements
def fig_s3():
    d = pd.read_csv(ROOT / "results/validation_cazri_light.csv")
    d = d[d.case == "broadband diffuse"]
    col = {"Block 1": OI["orange"], "Block 2": OI["blue"], "Block 3": OI["green"]}
    mk = {"09:30": "o", "12:30": "s", "15:30": "^"}
    tlab = {"09:30": "09–10 h", "12:30": "12–13 h", "15:30": "15–16 h"}
    fig, axs = plt.subplots(1, 2, figsize=(5.4, 2.95), constrained_layout=True)
    stats = {}
    for ax, v, title, lim, lab in [(axs[0], "total", "Whole system (pitch mean)", (0.4, 0.7), "A"),
                                   (axs[1], "below", "Below the photovoltaic array", (0.0, 0.6), "B")]:
        ax.plot(lim, lim, color="black", lw=0.6, ls=(0, (4, 2)))
        for _, r in d.iterrows():
            ax.plot(r[f"obs_{v}"], r[f"mod_{v}"], ls="none", marker=mk[r.time], ms=5,
                    color=col[r.block], mec="white", mew=0.5)
        e = d[f"mod_{v}"] - d[f"obs_{v}"]
        stats[v] = (e.mean(), np.sqrt((e ** 2).mean()))
        ax.text(0.96, 0.04, f"Bias {e.mean():+.3f}".replace("-", "\u2212") + f"\nRoot-mean-square\nerror {np.sqrt((e ** 2).mean()):.3f}",
                transform=ax.transAxes, va="bottom", ha="right", fontsize=7)
        ax.set_xlim(lim); ax.set_ylim(lim); ax.set_aspect("equal")
        ax.set_title(title, fontsize=7.5, loc="left", pad=4)
        ax.set_xlabel("Measured relative photon flux (–)")
        ax.set_ylabel("Modelled relative irradiance (–)")
        panel(ax, lab)
    h = [plt.Line2D([], [], ls="none", marker="o", color=c, ms=5, label=b) for b, c in col.items()]
    h += [plt.Line2D([], [], ls="none", marker=m, color="0.4", ms=5, label=tlab[t]) for t, m in mk.items()]
    fig.legend(handles=h, loc="outside lower center", ncol=6, fontsize=7)
    save(fig, "figS3_light_vs_cazri")
    return stats


if __name__ == "__main__":
    for k, v in fig_s1().items():
        print("S1", k, "r=%.2f MAPE=%.2f n=%d" % v)
    fig_s2()
    for k, v in fig_s3().items():
        print("S3", k, "bias=%+.3f rmse=%.3f" % v)
    print("saved to", OUT)
