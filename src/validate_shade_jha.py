"""Compare simulated RY against reduction in ground light (results/shade_response_check.csv, east-west layout)
with the observations compiled by Jha et al. (2026), https://doi.org/10.3390/agronomy16100985
(data: https://github.com/AditiJha26/Analysis-of-the-Effect-of-Shade-on-Crop-Yield-in-Agrivoltaic-Systems, Data_Clean.xlsx).
Usage: python3 src/validate_shade_jha.py path/to/Data_Clean.xlsx"""
import sys, pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
R = pathlib.Path(__file__).resolve().parents[1]
d = pd.read_excel(sys.argv[1]).rename(columns={"RSR (%)": "rsr", "Yield (%)": "ry"})
d["rsr"] /= 100; d["ry"] /= 100
m = pd.read_csv(R / "results/shade_response_check.csv")
def curve(crop, nm):
    g = m[(m.crop == crop) & (m.nmode == nm)].sort_values("light_reduction")
    return np.r_[0, g.light_reduction.values], np.r_[1, g.ry_med.values]
GROUPS = {  # label: (observation filter, model crop(s))
    "Wheat": (d.Crop.isin(["Wheat", "Durum wheat"]), ["wheat"]),
    "Grain legumes (chickpea, groundnut)": (d.Crop_type.eq("Grain legumes"), ["chickpea", "groundnut"]),
    "Maize (proxy for pearl millet)": (d.Crop_type.eq("Maize"), ["pearl_millet"]),
}
rows = []; fig, axs = plt.subplots(1, 3, figsize=(7.0, 2.6), sharey=True)
for ax, (lab, (msk, crops)) in zip(axs, GROUPS.items()):
    XM = 0.5 if 'legume' in lab else 0.7        # simulated GCR range limit (legumes to 0.5)
    o = d[msk & (d.rsr <= XM)]
    ax.plot([0, 1], [1, 0], color="0.6", lw=0.6, ls=":")
    ax.scatter(o.rsr, o.ry.clip(upper=1.4), s=7, c="0.55", alpha=0.6, lw=0, label=f"Observed (n = {len(o)})")
    for nm, ls, col in (("current", "-", "#0072B2"), ("recommended", "--", "#D55E00")):
        ys = [np.interp(o.rsr, *curve(c, nm)) for c in crops]
        pred = np.mean(ys, axis=0)
        x = np.linspace(0, XM, 50); ycurve = np.mean([np.interp(x, *curve(c, nm)) for c in crops], axis=0)
        ax.plot(x, ycurve, ls, color=col, lw=1.0, label=("Calibrated nitrogen" if nm == "current" else "Recommended nitrogen"))
        e = pred - o.ry.values
        rows.append(dict(group=lab, nmode=nm, n=len(o), n_studies=o.Reference.nunique(),
                         bias=e.mean(), rmse=np.sqrt((e ** 2).mean()), mae=np.abs(e).mean()))
    ax.set_title(lab, fontsize=7); ax.set_xlabel("Reduction in light (–)", fontsize=8)
    ax.set_xlim(0, 0.72); ax.set_ylim(0, 1.4)
    for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
    ax.tick_params(direction="out", labelsize=7)
axs[0].set_ylabel("Relative yield (–)", fontsize=8); axs[0].legend(fontsize=5.5, frameon=False, loc="lower left")
for a, t in zip(axs, "ABC"): a.text(-0.02, 1.12, t, transform=a.transAxes, fontsize=10, fontweight="bold")
fig.tight_layout(); fig.savefig(R / "results/figures/fig_shade_validation_jha.pdf"); fig.savefig(R / "results/figures/fig_shade_validation_jha.png", dpi=300)
t = pd.DataFrame(rows); t.to_csv(R / "results/shade_validation_jha.csv", index=False, float_format="%.3f")
print(t.round(3).to_string(index=False))
# binned observed medians and model values for the text
bins = []
for lab, (msk, crops) in GROUPS.items():
    o = d[msk & (d.rsr <= (0.5 if 'legume' in lab else 0.7))]
    b = o.groupby(pd.cut(o.rsr, [-.01, .15, .30, .45, .60, .70]), observed=True).agg(n=("ry", "size"), obs_med=("ry", "median"), x=("rsr", "mean"))
    for nm in ("current", "recommended"):
        b["model_" + nm] = [np.mean([np.interp(xx, *curve(c, nm)) for c in crops]) for xx in b.x]
    b["group"] = lab; bins.append(b.reset_index(drop=True))
bt = pd.concat(bins); bt.to_csv(R / "results/shade_validation_jha_bins.csv", index=False, float_format="%.3f")
print(bt.round(2).to_string(index=False))
