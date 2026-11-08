"""Simulated relative yield (RY) against mean ground-light reduction, per crop (east-west layout, calibrated N).
Light reduction = 1 - season-mean strip-mean ground-light factor at a representative central-India site
(25 N, 78 E) for a rabi (sow 15 Nov, 120 d) and a kharif (sow 1 Jul, 100 d) season. Writes
results/shade_response_check.csv and results/figures/fig_shade_response_check.{pdf,png}."""
import sys, pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
R = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / "prod"))
import pv_shading as ps

SEASON = {"wheat": ("2019-11-15", 120, 16.0), "chickpea": ("2019-11-01", 110, 16.0),
          "pearl_millet": ("2019-07-01", 90, 19.0), "groundnut": ("2019-07-01", 110, 19.0)}
LAT, LON = 25.0, 78.0
ry = pd.concat([pd.read_csv(R / f"runs/s1/summary/ry_crop_historical_{m}.csv.gz").assign(nmode=m)
                for m in ("current", "recommended")])
ry = ry[(ry.config == "ew_fixed")]
rows = []
for crop, (start, nd, srad) in SEASON.items():
    dates = pd.date_range(start, periods=nd + 2)
    hourly = ps.hourly_from_daily(LAT, LON, dates, np.full(len(dates), srad))
    cfg = ps.make_config("ew_fixed")
    d = ry[ry.crop == crop]
    for (nm, g), sub in d.groupby(["nmode", "gcr"]):
        geo = ps.strip_geometry(cfg, g)
        f = ps.daily_factors(hourly, cfg, geo).iloc[1:nd + 1]
        red = 1 - float(f.mean(axis=1).mean())
        rows.append(dict(crop=crop, nmode=nm, gcr=g, light_reduction=red, ry_med=sub.ry.median(),
                         ry_p25=sub.ry.quantile(.25), ry_p75=sub.ry.quantile(.75), n=len(sub)))
t = pd.DataFrame(rows).sort_values(["crop", "nmode", "gcr"])
t.to_csv(R / "results/shade_response_check.csv", index=False, float_format="%.4f")
print(t.round(3).to_string(index=False))
print("\nlight reduction at median RY = 0.80 (interpolated):")
OI = {"wheat": "#0072B2", "chickpea": "#D55E00", "pearl_millet": "#009E73", "groundnut": "#E69F00"}
LAB = {"wheat": "Wheat", "chickpea": "Chickpea", "pearl_millet": "Pearl millet", "groundnut": "Groundnut"}
fig, ax = plt.subplots(figsize=(3.4, 3.0))
ax.plot([0, 1], [1, 0], color="0.6", lw=0.6, ls=":", label="Proportional loss")
ax.plot([], [], "k-o", ms=2.5, lw=0.9, label="Calibrated nitrogen"); ax.plot([], [], "k--s", ms=2.5, lw=0.9, label="Recommended nitrogen")
for (crop, nm), s in t.groupby(["crop", "nmode"]):
    s = s.sort_values("light_reduction")
    x = np.r_[0, s.light_reduction.values]; y = np.r_[1, s.ry_med.values]
    ax.plot(x, y, "-o" if nm == "current" else "--s", ms=2.5, lw=0.9, color=OI[crop],
            label=LAB[crop] if nm == "current" else None)
    x80 = np.interp(0.80, y[::-1], x[::-1]) if y.min() <= 0.8 else np.nan
    print(f"  {crop} {nm}: {x80:.3f}")
ax.axhline(0.80, color="k", lw=0.5, ls="--")
ax.set_xlabel("Mean reduction in ground light (–)", fontsize=8); ax.set_ylabel("Median relative yield (–)", fontsize=8)
ax.set_xlim(0, 0.8); ax.set_ylim(0.1, 1.15)
for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
ax.tick_params(direction="out", labelsize=7); ax.legend(fontsize=6.5, frameon=False, loc="lower left")
fig.tight_layout(); fig.savefig(R / "results/figures/fig_shade_response_check.pdf"); fig.savefig(R / "results/figures/fig_shade_response_check.png", dpi=300)
