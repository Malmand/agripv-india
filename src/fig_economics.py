#!/usr/bin/env python3
"""Fig: cost-supply curve of the yield-constrained APV potential (screening economics)."""
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
R = Path(__file__).resolve().parent.parent
S = pd.read_csv(R / "results/economics/econ_supply.csv")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7, "axes.linewidth": 0.7, "pdf.fonttype": 42})
fig, ax = plt.subplots(figsize=(3.5, 2.6), dpi=300)
grid = np.linspace(0, 40, 400)
sty = {0.0: ("#0072B2", "-", "No structure premium"), 0.25: ("#E69F00", "--", "+25% (Indian ministry estimate)"), 0.38: ("#D55E00", ":", "+38% (Schindele et al.)")}
for p, (col, ls, lab) in sty.items():
    cur = []
    for m, g in S[S.premium == p].groupby("model"):
        cur.append(np.interp(grid, g.cum_twp.values, g.lcoe.values, left=np.nan, right=np.nan))
    med = np.nanmedian(np.array(cur), axis=0); lo = np.nanmin(np.array(cur), axis=0); hi = np.nanmax(np.array(cur), axis=0)
    ax.fill_between(grid, lo, hi, color=col, alpha=0.18, lw=0)
    ax.plot(grid, med, color=col, ls=ls, lw=1.2, label=lab)
ax.axhline(2.95, color="k", lw=0.6); ax.text(0.5, 2.92, "Ceiling tariff 2.95", fontsize=6, va="top")
ax.axhline(2.775, color="0.4", lw=0.6, ls="-."); ax.text(39.5, 2.745, "Auction 2.77–2.78", fontsize=6, va="top", ha="right", color="0.3")
ax.set_xlim(0, 40); ax.set_ylim(2.2, 4.6)
ax.set_xlabel("Cumulative capacity (TWp)"); ax.set_ylabel("Levelised cost (Rs kWh$^{-1}$)")
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.tick_params(direction="out", width=0.6, length=3)
ax.legend(frameon=False, fontsize=6, loc="upper left", title="Elevated-structure premium", title_fontsize=6)
fig.tight_layout()
for e in ("png", "pdf"): fig.savefig(R / f"results/figures/fig_economics.{e}", dpi=600 if e == "png" else None)
print("ok")
