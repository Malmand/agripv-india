"""Tornado chart of the national APV potential (east-west, RY >= 0.80, slope <= 5%, robust nitrogen, 1995-2014):
one assumption changed at a time from the base case, bars from the base to each tested value, sorted by span.
Reads results/potential/numbers.json (sens.*, field.*, fut.*), so it follows the same numbers as Table S11.
Mid-century climate is drawn as the range of the five paired GCM changes (fut.change_lo..hi) applied to the base.
Usage: python src/fig_tornado.py [--numbers results/potential/numbers.json] [--out results/figures]
"""
import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt

plt.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42, "axes.linewidth": 0.8,
                     "xtick.direction": "out", "ytick.direction": "out"})
C_DOWN, C_UP = "#D55E00", "#0072B2"   # Okabe-Ito vermillion / blue, as in the reconciliation waterfall


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--numbers", type=Path, default=Path("results/potential/numbers.json"))
    ap.add_argument("--out", type=Path, default=Path("results/figures"))
    a = ap.parse_args()
    d = json.loads(a.numbers.read_text())
    r, v = d["raw"], d["values"]
    tw = lambda k: r[k] / 1e6                      # sens.*.cap are MWp
    base = tw("sens.base.cap")
    lo_g, hi_g = (float(x) for x in v["sens.base.range"].replace("−", "-").split("–"))
    # (label, low value, low tag, high value, high tag); None = one-sided
    rows = [("Shade response", r["field.ew.t80.cap_twp"], "field observations", None, None),
            ("Yield threshold τ", tw("sens.thr90.cap"), "0.90", tw("sens.thr66.cap"), "0.66"),
            ("Nitrogen management", None, None, tw("sens.n_calib.cap"), "calibrated alone"),
            ("Season rule", tw("sens.season.cap") if "sens.season.cap" in r else None, "16 of 20 seasons", None, None),
            ("Module efficiency", tw("sens.eta20.cap"), "20%", tw("sens.eta24.cap"), "24%"),
            ("Terrain slope limit", None, None, tw("sens.slope_none.cap"), "none"),
            ("Climate model (GCM)", lo_g, "", hi_g, ""),
            ]
    if "fut.change_lo" in r:
        rows.append(("Mid-century climate, SSP5-8.5", base * (1 + r["fut.change_lo"] / 100), "",
                     base * (1 + max(r["fut.change_hi"], 0) / 100), ""))
    rows = [x for x in rows if x[1] is not None or x[3] is not None]
    span = lambda x: max(abs((x[1] or base) - base), abs((x[3] or base) - base))
    rows.sort(key=span)                             # largest at the top

    fig, ax = plt.subplots(figsize=(6.3, 3.3), constrained_layout=True)
    h = 0.62
    for i, (lab, lo, lt, hi, ht) in enumerate(rows):
        if lo is not None and lo < base:
            ax.barh(i, lo - base, h, left=base, color=C_DOWN, lw=0)
            if lt:
                ax.text(lo - 0.4, i, f"{lo:.1f} ({lt})", ha="right", va="center", fontsize=6.5)
        if hi is not None and hi > base:
            ax.barh(i, hi - base, h, left=base, color=C_UP, lw=0)
            if ht:
                ax.text(hi + 0.4, i, f"{hi:.1f} ({ht})", ha="left", va="center", fontsize=6.5)
        if not lt and not ht:                       # ranges without a named case: print the span
            ax.text(max(hi, base) + 0.4, i, f"{lo:.1f}–{hi:.1f}", ha="left", va="center", fontsize=6.5)
    ax.axvline(base, color="black", lw=0.8)
    ax.text(base + 0.4, len(rows) - 0.45, f"Base {base:.1f} TWp", ha="left", va="bottom", fontsize=7)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([x[0] for x in rows], fontsize=7.5)
    ax.set_xlim(8, 56)
    ax.set_ylim(-0.6, len(rows) - 0.1)
    ax.set_xlabel("National capacity (TWp)", fontsize=8.5)
    ax.tick_params(axis="x", labelsize=7.5)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=C_DOWN, label="Lowers the potential"), Patch(color=C_UP, label="Raises the potential")],
              fontsize=6.5, loc="upper right", bbox_to_anchor=(1.0, 0.97), frameon=False)
    a.out.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out / "fig_tornado.pdf")
    fig.savefig(a.out / "fig_tornado.png", dpi=400)
    print("wrote", a.out / "fig_tornado.pdf")


if __name__ == "__main__":
    main()
