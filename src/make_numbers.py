"""Every result number quoted in the manuscript, in one file: results/potential/numbers.json.

Reads the postprocess_india.py outputs for every stage present and writes
  {"meta": {...}, "values": {key: formatted text}, "raw": {key: float}}
The JS builders (paper/methods/lib.js fill()) replace {key} in the Results, Discussion and
highlights with values[key]; keys of stages that are missing (2050, robust) are simply absent, and
fill() then drops the optional sentence or shows [pending]. Graphical-abstract numbers (ga.*) use
the same definitions as paper/methods/graphical_abstract.py.

Key scheme (main case: east-west layout, RY >= 0.80, calibrated N, slope <= 5%):
  <p>.<layout>.t<66|80|90>.<cap_twp|cap_twp_m|cap_twp_lo|cap_twp_hi|cap_gwp|land_mha|energy_pwh|density|sy>
      p      = hist (historical_current), robust (historical_current_robust), ssp245, ssp585
      layout = south, ew, vertical
  <p>.<layout>.t80.<none|le10>.cap_twp       slope sensitivity
  <p>.<layout>.t80.gcr_<crop>, atcap_<crop>   area-weighted mean GCR_max per crop, share at simulated limit
  hist.*      land_share, legume_area_share, legume_cap_share, gcr_p05, gcr_p95, cereal_gcr_med,
              vertical_gt06_share, top<1-3>_state / top<1-3>_gwp, best_layout
  main.*      aliases of hist.ew.t80.* plus cmp_teri, cmp_fhg (comparison phrases)
  robust.*    change_pct (signed), reduction_pct, top_states (largest absolute reductions)
  ssp245.*, ssp585.*  change_pct (+ per-layout), change_lo / change_hi (GCM range of the change),
              agree4_share (share of land where >= 4 of 5 GCMs agree on the sign), gcr_<crop>_delta
  calib.*     state-yield calibration statistics (results/validation_before_after.csv)
  ga.*        headline, range, change_2050, gcr_<crop>
Usage: python src/make_numbers.py [--pp results/potential] [--validation results/validation_before_after.csv]
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

STAGES = {"hist": "historical_current", "robust": "historical_current_robust",
          "ssp245": "ssp245_current", "ssp585": "ssp585_current"}
LAYOUTS = {"south": "south_fixed", "ew": "ew_fixed", "vertical": "vertical"}
LAYOUT_TEXT = {"south_fixed": "south-facing", "ew_fixed": "east-west", "vertical": "vertical"}
THRS = {"t66": 0.66, "t80": 0.8, "t90": 0.9}
CROPS = ["wheat", "chickpea", "pearl_millet", "groundnut"]
LEGUMES, CEREALS = ["chickpea", "groundnut"], ["wheat", "pearl_millet"]
MAIN_LAYOUT, MAIN_THR = "ew_fixed", 0.8
TERI, FHG_HI = (1.2, 2.1), 13.8       # TW, published Indian estimates quoted in Section 4.1
MINUS = "−"


def twp_nd(mwp):
    x = mwp / 1e6
    return 0 if x >= 10 else 1 if x >= 1 else 2


def twp(mwp, nd=None):
    return f"{mwp / 1e6:.{twp_nd(mwp) if nd is None else nd}f}"


def twp_range(med, lo, hi):
    """Median, min, max with the decimals of the median, more if the range would collapse (1.1-1.1)."""
    nd = twp_nd(med)
    while twp(lo, nd) == twp(hi, nd) and nd < twp_nd(med) + 2:
        nd += 1
    return twp(med, nd), twp(lo, nd), twp(hi, nd)


def pct(x, signed=False):
    s = "0" if abs(x) < 0.5 else f"{x:+.0f}" if signed else f"{x:.0f}"
    return s.replace("-", MINUS)


def wmedian(x, w):
    o = np.argsort(x)
    x, w = np.asarray(x)[o], np.asarray(w)[o]
    c = np.cumsum(w)
    return float(np.interp(0.5 * c[-1], c, x)) if c[-1] > 0 else np.nan


def wquant(x, w, q):
    o = np.argsort(x)
    x, w = np.asarray(x)[o], np.asarray(w)[o]
    c = np.cumsum(w)
    return float(np.interp(q * c[-1], c, x))


class Numbers:
    def __init__(self):
        self.values, self.raw = {}, {}

    def put(self, key, raw, text):
        if raw is None or (isinstance(raw, float) and not np.isfinite(raw)):
            return
        self.raw[key] = float(raw) if not isinstance(raw, str) else raw
        self.values[key] = text


def sel(t, cfg, thr, rule="le5"):
    r = t[(t.config == cfg) & (t.thr.round(2) == round(thr, 2)) & (t.slope_rule == rule)]
    return r.iloc[0] if len(r) else None


def stage_numbers(N, p, pp, st):
    t = pd.read_csv(pp / f"india_combined_{st}.csv")
    for lk, cfg in LAYOUTS.items():
        for tk, thr in THRS.items():
            r = sel(t, cfg, thr)
            if r is None:
                continue
            k = f"{p}.{lk}.{tk}"
            N.put(f"{k}.cap_twp", r.cap_mwp_median, twp(r.cap_mwp_median))
            md, lo, hi = twp_range(r.cap_mwp_median, r.cap_mwp_min, r.cap_mwp_max)
            N.put(f"{k}.cap_twp_m", r.cap_mwp_median, md)   # median at the precision of its range
            N.put(f"{k}.cap_twp_lo", r.cap_mwp_min, lo)
            N.put(f"{k}.cap_twp_hi", r.cap_mwp_max, hi)
            N.put(f"{k}.cap_gwp", r.cap_mwp_median / 1e3, f"{r.cap_mwp_median / 1e3:,.0f}")
            N.put(f"{k}.land_mha", r.land_ha_median / 1e6, f"{r.land_ha_median / 1e6:.1f}")
            N.put(f"{k}.density", r.cap_mwp_median / r.land_ha_median, f"{r.cap_mwp_median / r.land_ha_median:.2f}")
            if r.energy_gwh_median > 0:
                N.put(f"{k}.energy_pwh", r.energy_gwh_median / 1e6, f"{r.energy_gwh_median / 1e6:.1f}")
                N.put(f"{k}.energy_pwh_lo", r.energy_gwh_min / 1e6, f"{r.energy_gwh_min / 1e6:.1f}")
                N.put(f"{k}.energy_pwh_hi", r.energy_gwh_max / 1e6, f"{r.energy_gwh_max / 1e6:.1f}")
                sy = 1000 * r.energy_gwh_median / r.cap_mwp_median
                N.put(f"{k}.sy", sy, f"{sy:,.0f}")
        for rule in ("none", "le10"):
            r = sel(t, cfg, MAIN_THR, rule)
            if r is not None:
                N.put(f"{p}.{lk}.t80.{rule}.cap_twp", r.cap_mwp_median, twp(r.cap_mwp_median))
    # best layout at tau 0.80
    b = t[(t.thr.round(2) == MAIN_THR) & (t.slope_rule == "le5")].sort_values("cap_mwp_median")
    if len(b):
        N.put(f"{p}.best_layout", LAYOUT_TEXT.get(b.iloc[-1].config, b.iloc[-1].config),
              LAYOUT_TEXT.get(b.iloc[-1].config, b.iloc[-1].config))
    # crop GCR_max (same definition as the graphical abstract: map_gcr gcr_med, weighted by eligible area)
    m = pd.read_csv(pp / f"map_gcr_{st}.csv.gz")
    m = m[(m.thr.round(2) == MAIN_THR) & (m.elig_ha > 0)]
    c = pd.read_csv(pp / f"cell_crop_{st}.csv.gz")
    c = c[(c.slope_rule == "le5") & (c.thr.round(2) == MAIN_THR) & (c.elig_ha > 0)]
    for lk, cfg in LAYOUTS.items():
        for crop in CROPS:
            d = m[(m.config == cfg) & (m.crop == crop)]
            if len(d):
                g = np.average(d.gcr_med, weights=d.elig_ha)
                N.put(f"{p}.{lk}.t80.gcr_{crop}", g, f"{g:.2f}")
            e = c[(c.config == cfg) & (c.crop == crop)]
            if len(e):
                s = 100 * np.average(e.at_cap.astype(float), weights=e.elig_ha)
                N.put(f"{p}.{lk}.t80.atcap_{crop}", s, pct(s))
    return t, m, c


def hist_extras(N, pp, t, m, c):
    st = STAGES["hist"]
    main = sel(t, MAIN_LAYOUT, MAIN_THR)
    allland = sel(t, MAIN_LAYOUT, MAIN_THR, "none")
    if main is not None and allland is not None:
        s = 100 * main.land_ha_median / allland.land_ha_median
        N.put("hist.land_share", s, pct(s))
    by = pd.read_csv(pp / f"india_by_crop_{st}.csv")
    by = by[(by.config == MAIN_LAYOUT) & (by.thr.round(2) == MAIN_THR) & (by.slope_rule == "le5")]
    if len(by):
        leg = by.crop.isin(LEGUMES)
        a = 100 * by.elig_ha_median[leg].sum() / by.elig_ha_median.sum()
        k = 100 * by.cap_mwp_median[leg].sum() / by.cap_mwp_median.sum()
        N.put("hist.legume_area_share", a, pct(a))
        N.put("hist.legume_cap_share", k, pct(k))
    d = m[m.config == MAIN_LAYOUT]
    if len(d):
        N.put("hist.gcr_p05", wquant(d.gcr_med, d.elig_ha, 0.05), f"{wquant(d.gcr_med, d.elig_ha, 0.05):.2f}")
        N.put("hist.gcr_p95", wquant(d.gcr_med, d.elig_ha, 0.95), f"{wquant(d.gcr_med, d.elig_ha, 0.95):.2f}")
        ce = d[d.crop.isin(CEREALS)]
        if len(ce):
            x = wmedian(ce.gcr_med, ce.elig_ha)
            N.put("hist.cereal_gcr_med", x, f"{x:.2f}")
    v = c[c.config == "vertical"]
    if len(v) and v.cap_mwp.sum() > 0:
        x = 100 * v.cap_mwp[v.gcr_max > 0.6 + 1e-9].sum() / v.cap_mwp.sum()
        N.put("hist.vertical_gt06_share", x, pct(x))
    for lk, cfg in LAYOUTS.items():     # specific yield at GCR_max, area-weighted median cell
        e = c[(c.config == cfg) & c.yield_kwh_kwp.notna()]
        if len(e):
            x = wmedian(e.yield_kwh_kwp, e.elig_ha)
            N.put(f"hist.{lk}.sy_med", x, f"{x:,.0f}")
    s = pd.read_csv(pp / f"state_combined_{st}.csv")
    s = s[(s.config == MAIN_LAYOUT) & (s.thr.round(2) == MAIN_THR) & (s.slope_rule == "le5")]
    top = s.sort_values("cap_mwp_median", ascending=False).head(3)
    for i, r in enumerate(top.itertuples(), 1):
        N.put(f"hist.top{i}_state", r.state, r.state)
        N.put(f"hist.top{i}_gwp", r.cap_mwp_median / 1e3, f"{r.cap_mwp_median / 1e3:,.0f}")


def main_aliases(N):
    for k in list(N.values):
        if k.startswith("hist.ew.t80.") and k.count(".") == 3:
            name = k.split(".")[-1]
            N.values[f"main.{name}"], N.raw[f"main.{name}"] = N.values[k], N.raw[k]
    cap = N.raw.get("main.cap_twp")
    if cap is None:
        return
    cap_tw = cap / 1e6 if cap > 1e3 else cap   # raw holds MWp
    word = "below" if cap_tw < TERI[0] else "above" if cap_tw > TERI[1] else "within"
    N.put("main.cmp_teri", word, word)
    ratio = FHG_HI / cap_tw
    if ratio > 1.1:
        phr = f"{ratio:.1f} times smaller than"
    elif ratio < 1 / 1.1:
        phr = f"{1 / ratio:.1f} times larger than"
    else:
        phr = "close to"
    N.put("main.cmp_fhg", phr, phr)


def robust_numbers(N, pp):
    f, b = pp / f"india_combined_{STAGES['hist']}.csv", pp / f"india_combined_{STAGES['robust']}.csv"
    if not (f.exists() and b.exists()):
        return
    x = pd.read_csv(f).merge(pd.read_csv(b), on=["config", "thr", "slope_rule"], suffixes=("_c", "_r"))
    x = x[x.slope_rule == "le5"]
    for r in x.itertuples():
        lk = {v: k for k, v in LAYOUTS.items()}.get(r.config)
        tk = {round(v, 2): k for k, v in THRS.items()}.get(round(r.thr, 2))
        if lk is None or tk is None:
            continue
        ch = 100 * (r.cap_mwp_median_r / r.cap_mwp_median_c - 1)
        N.put(f"robust.{lk}.{tk}.change_pct", ch, pct(ch, True))
        if (r.config, round(r.thr, 2)) == (MAIN_LAYOUT, MAIN_THR):
            N.put("robust.change_pct", ch, pct(ch, True))
            N.put("robust.reduction_pct", -ch, pct(-ch))
    s1 = pd.read_csv(pp / f"state_combined_{STAGES['hist']}.csv")
    s2 = pd.read_csv(pp / f"state_combined_{STAGES['robust']}.csv")
    k = ["state", "config", "thr", "slope_rule"]
    s = s1.merge(s2, on=k, suffixes=("_c", "_r"))
    s = s[(s.config == MAIN_LAYOUT) & (s.thr.round(2) == MAIN_THR) & (s.slope_rule == "le5")]
    s = s.assign(loss=s.cap_mwp_median_c - s.cap_mwp_median_r).sort_values("loss", ascending=False)
    s = s[s.loss > 0].head(2)
    if len(s):
        N.put("robust.top_states", " and ".join(s.state), " and ".join(s.state))


def future_numbers(N, pp, p):
    st, hs = STAGES[p], STAGES["hist"]
    f, h = pp / f"india_combined_{st}.csv", pp / f"india_combined_{hs}.csv"
    if not (f.exists() and h.exists()):
        return
    x = pd.read_csv(h).merge(pd.read_csv(f), on=["config", "thr", "slope_rule"], suffixes=("_h", "_f"))
    x = x[x.slope_rule == "le5"]
    for r in x.itertuples():
        lk = {v: k for k, v in LAYOUTS.items()}.get(r.config)
        tk = {round(v, 2): k for k, v in THRS.items()}.get(round(r.thr, 2))
        if lk and tk:
            ch = 100 * (r.cap_mwp_median_f / r.cap_mwp_median_h - 1)
            N.put(f"{p}.{lk}.{tk}.change_pct", ch, pct(ch, True))
    r = x[(x.config == MAIN_LAYOUT) & (x.thr.round(2) == MAIN_THR)]
    if len(r):
        ch = 100 * (r.iloc[0].cap_mwp_median_f / r.iloc[0].cap_mwp_median_h - 1)
        N.put(f"{p}.change_pct", ch, pct(ch, True))
    # per-GCM change and sign agreement, cell level (crops combined)
    k = ["cell", "model"]
    ch = pd.read_csv(pp / f"cell_combined_{hs}.csv.gz")
    cf = pd.read_csv(pp / f"cell_combined_{st}.csv.gz")
    q = lambda d: d[(d.config == MAIN_LAYOUT) & (d.thr.round(2) == MAIN_THR) & (d.slope_rule == "le5")]
    ch, cf = q(ch), q(cf)
    tot = ch.groupby("model").cap_mwp.sum().to_frame("h").join(cf.groupby("model").cap_mwp.sum().rename("f"))
    if len(tot):
        d = 100 * (tot.f / tot.h - 1)
        N.put(f"{p}.change_lo", d.min(), pct(d.min(), True))
        N.put(f"{p}.change_hi", d.max(), pct(d.max(), True))
    cc = ch[k + ["cap_mwp", "land_ha"]].merge(cf[k + ["cap_mwp"]], on=k, suffixes=("_h", "_f"))
    if len(cc):
        cc["sgn"] = np.sign(np.round(cc.cap_mwp_f - cc.cap_mwp_h, 6))
        a = cc.groupby("cell").agg(up=("sgn", lambda s: (s > 0).sum()), dn=("sgn", lambda s: (s < 0).sum()),
                                   land=("land_ha", "first"))
        ag = (a[["up", "dn"]].max(axis=1) >= 4)
        x = 100 * np.average(ag, weights=a.land) if a.land.sum() > 0 else np.nan
        N.put(f"{p}.agree4_share", x, pct(x))
    for crop in CROPS:
        g0, g1 = N.raw.get(f"hist.ew.t80.gcr_{crop}"), N.raw.get(f"{p}.ew.t80.gcr_{crop}")
        if g0 is not None and g1 is not None:
            N.put(f"{p}.gcr_{crop}_delta", g1 - g0, f"{g1 - g0:+.2f}".replace("-", MINUS))


def ga_numbers(N):
    """Same text as graphical_abstract.py (ew_fixed, tau 0.8, slope <= 5%, badge = SSP2-4.5)."""
    med, lo, hi = (N.raw.get(f"hist.ew.t80.{k}") for k in ("cap_twp", "cap_twp_lo", "cap_twp_hi"))
    if med is not None:
        if med >= 1e6:
            nd = 1 if round(lo / 1e6, 1) != round(hi / 1e6, 1) else 2
            N.put("ga.headline", med, f"{med / 1e6:.1f} TWp")
            N.put("ga.range", lo, f"GCM range {lo / 1e6:.{nd}f}–{hi / 1e6:.{nd}f}")
        else:
            N.put("ga.headline", med, f"{med / 1e3:.0f} GWp")
            N.put("ga.range", lo, f"GCM range {lo / 1e3:.0f}–{hi / 1e3:.0f}")
    if "ssp245.change_pct" in N.raw:
        N.put("ga.change_2050", N.raw["ssp245.change_pct"], N.values["ssp245.change_pct"] + "%")
    for crop in CROPS:
        if f"hist.ew.t80.gcr_{crop}" in N.raw:
            N.put(f"ga.gcr_{crop}", N.raw[f"hist.ew.t80.gcr_{crop}"], N.values[f"hist.ew.t80.gcr_{crop}"])


def calib_numbers(N, f):
    if not f.exists():
        return
    d = pd.read_csv(f)
    d = d[d.obs_area >= 50]
    for crop in CEREALS:
        for case in ("before", "after"):
            s = d[(d.crop == crop) & (d.case == case)]
            if len(s) < 3:
                continue
            r = np.corrcoef(s.obs, s.sim)[0, 1]
            mape = 100 * np.average((s.sim / s.obs - 1).abs(), weights=s.obs_area)
            N.put(f"calib.{crop}.{case}.r", r, f"{r:.2f}")
            N.put(f"calib.{crop}.{case}.mape", mape, pct(mape))
            N.put(f"calib.{crop}.{case}.n", len(s), f"{len(s)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pp", type=Path, default=Path("results/potential"))
    ap.add_argument("--validation", type=Path, default=Path("results/validation_before_after.csv"))
    a = ap.parse_args()
    N = Numbers()
    present = {p: st for p, st in STAGES.items() if (a.pp / f"india_combined_{st}.csv").exists()}
    for p, st in present.items():
        t, m, c = stage_numbers(N, p, a.pp, st)
        if p == "hist":
            hist_extras(N, a.pp, t, m, c)
    main_aliases(N)
    robust_numbers(N, a.pp)
    for p in ("ssp245", "ssp585"):
        future_numbers(N, a.pp, p)
    ga_numbers(N)
    calib_numbers(N, a.validation)
    out = {"meta": {"stages": present, "main_case": {"layout": MAIN_LAYOUT, "thr": MAIN_THR, "slope": "le5",
                                                     "management": "calibrated N"},
                    "units": "cap_twp TWp (raw MWp), cap_gwp GWp, land_mha Mha, energy_pwh PWh/yr, "
                             "density MWp/ha, sy kWh/kWp/yr, *_share and *_pct in %"},
           "values": dict(sorted(N.values.items())), "raw": dict(sorted(N.raw.items()))}
    f = a.pp / "numbers.json"
    f.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"wrote {f}: {len(N.values)} numbers, stages {', '.join(present) or 'none'}")


if __name__ == "__main__":
    main()
