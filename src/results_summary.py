"""Headline numbers for the Results text, from postprocess_india.py outputs.

Writes <pp>/headline_numbers.md: India totals (crops combined, slope <= 5%) by layout and
threshold, crop-level GCR_max and share of area at the simulated GCR limit, top states,
calibrated vs robust, and mid-century change if future stages are present.
Usage: python results_summary.py --pp results/potential --stages historical_current [ssp585_current ...]
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def fmt_range(m, lo, hi, scale, nd=1):
    return f"{m / scale:.{nd}f} ({lo / scale:.{nd}f}–{hi / scale:.{nd}f})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pp", required=True, type=Path)
    ap.add_argument("--stages", nargs="+", required=True)
    a = ap.parse_args()
    out = ["# Headline numbers (median over 5 GCMs, range in brackets)", ""]
    base = a.stages[0]
    for st in a.stages:
        f = a.pp / f"india_combined_{st}.csv"
        if not f.exists():
            continue
        t = pd.read_csv(f)
        t = t[t.slope_rule == "le5"].sort_values(["thr", "config"])
        out += [f"## {st}: crops combined, slope ≤ 5%", "",
                "| Layout | τ | Land (Mha) | Capacity (TWp) | Energy (PWh/yr) |", "|---|---|---|---|---|"]
        for r in t.itertuples():
            en = fmt_range(r.energy_gwh_median, r.energy_gwh_min, r.energy_gwh_max, 1e6, 2) if np.isfinite(r.energy_gwh_median) and r.energy_gwh_median > 0 else "n/a"
            out.append(f"| {r.config} | {r.thr:.2f} | {r.land_ha_median / 1e6:.2f} | "
                       f"{fmt_range(r.cap_mwp_median, r.cap_mwp_min, r.cap_mwp_max, 1e6, 2)} | {en} |")
        out.append("")
        c = pd.read_csv(a.pp / f"cell_crop_{st}.csv.gz")
        c = c[(c.slope_rule == "le5") & (c.thr.round(2) == 0.8) & (c.elig_ha > 0)]
        w = c.groupby(["crop", "config"]).apply(lambda d: pd.Series({
            "gcr_aw": np.average(d.gcr_max, weights=d.elig_ha),
            "share_at_cap": np.average(d.at_cap.astype(float), weights=d.elig_ha) if "at_cap" in d else np.nan}),
            include_groups=False).reset_index()
        out += [f"### {st}: area-weighted GCR_max at τ = 0.80 (all GCMs pooled)", "",
                "| Crop | Layout | GCR_max | Share of area at simulated GCR limit |", "|---|---|---|---|"]
        out += [f"| {r.crop} | {r.config} | {r.gcr_aw:.2f} | {r.share_at_cap:.0%} |" for r in w.itertuples()]
        out.append("")
        s = pd.read_csv(a.pp / f"state_combined_{st}.csv")
        s = s[(s.slope_rule == "le5") & (s.thr.round(2) == 0.8)]
        top = s.groupby("state").cap_mwp_median.max().sort_values(ascending=False).head(8)
        out += [f"### {st}: top states, best layout, τ = 0.80 (GWp)", ""]
        out += [f"- {k}: {v / 1e3:.0f}" for k, v in top.items()]
        out.append("")
    # mid-century change against the first stage
    b = a.pp / f"india_combined_{base}.csv"
    for st in a.stages[1:]:
        f = a.pp / f"india_combined_{st}.csv"
        if not (b.exists() and f.exists()) or "robust" in st or "recommended" in st:
            continue
        x = pd.read_csv(b).merge(pd.read_csv(f), on=["config", "thr", "slope_rule"], suffixes=("_h", "_f"))
        x = x[x.slope_rule == "le5"]
        out += [f"## Change {base} → {st} (capacity, %)", ""]
        out += [f"- {r.config}, τ {r.thr:.2f}: {100 * (r.cap_mwp_median_f / r.cap_mwp_median_h - 1):+.0f}%" for r in x.itertuples()]
        out.append("")
    (a.pp / "headline_numbers.md").write_text("\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()
