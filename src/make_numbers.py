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
  <p>.vertical.<tk>.nodin.cap_twp, <p>.din_cut_pct   vertical layout without the DIN cap (sensitivity)
  head.*      headline case: robust (historical_current_robust) when present, else calibrated N labelled
              "upper bound"; cap_twp(_m/_lo/_hi), energy_pwh, density, land_mha, gcr_<crop>, label,
              x_teri_lo/hi, x_fhg
  frame.*     cea_twh (India 2025-26 energy requirement, CEA LGBR 2026-27), <p>_multiple (annual energy / consumption),
              gw300/gw500 .land_mha .share (cropland needed at the headline density, % of eligible land)
  recon.*     reconciliation waterfall (reconcile.csv): d42/d75 .s<step>.twp, slope_pct, double_pct, yield_pct
  ga.*        headline, range, label, change_2050, gcr_<crop>, cover_<cereals|legumes>_pct
  <p>.ew.t80.gcr_<cereals|legumes>, cover_<..>_pct   group means (graphical-abstract definition)
  hist.wheat_n<N>.atcap/.area_share, hist.wheat_<lown|hin>.atcap/.area_share   wheat at the GCR limit by
              calibrated N level; hist.wheat_<atcap|notcap>.open_rel180 open yield at calibrated N / at 180 kg N
  calib.<crop>.spearman_nuse   rank correlation of calibrated N with state fertiliser N use
  <p>.energy_change_pct, sy_change_pct, irr_change_pct, pr_change_pct   mid-century energy change and its parts
  <p>.open_<crop>_pct, ry03_<crop>_delta   mid-century open-field yield change and RY change at GCR 0.3
  pilot.*, jodhpur.*   Rajasthan pilot (runs/rajasthan_final) and Jodhpur soil test (results/*_F)
  hist.din_gain_pct (uncapped vs capped vertical), recon.land_keep_pct
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
TERI_DENS = (0.42, 0.75)              # MW per ha, TERI fixed power density
# India's energy requirement 2025-26: 1,707,493 MU (energy supplied 1,706,985 MU). CEA, Load Generation Balance
# Report 2026-27, Section 2.1 (figure supplied by MO; URL to be added by MO).
CEA_TWH, CEA_VERIFIED = 1707.493, True
TARGETS_GW = (300, 500)
MINUS = "−"


def twp_nd(mwp):
    x = mwp / 1e6
    return 0 if x >= 10 else 1 if x >= 1 else 2


def twp(mwp, nd=None):
    return f"{mwp / 1e6:.{twp_nd(mwp) if nd is None else nd}f}"


def twp_range(med, lo, hi):
    """Median, min, max with the decimals of the median, more if the range would collapse (1.1-1.1)."""
    nd = max(twp_nd(med), 1)   # at least one decimal: "45.5 (45.5-45.9)", not "46 (45-46)"
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
        if "gcr_raw" in v:   # share of the uncapped vertical capacity above GCR 0.6 (removed by the DIN cap)
            raw = v.elig_ha * v.gcr_raw
            x = 100 * raw[v.gcr_raw > 0.6 + 1e-9].sum() / raw.sum()
            y = 100 * np.average(v.gcr_raw > 0.6 + 1e-9, weights=v.elig_ha)
            N.put("hist.vertical_gt06_area_share", y, pct(y))
        else:
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
        N.put(f"hist.top{i}_twp", r.cap_mwp_median / 1e6, f"{r.cap_mwp_median / 1e6:.1f}")
    if main is not None and len(top):
        x = 100 * top.cap_mwp_median.sum() / main.cap_mwp_median
        N.put("hist.top3_share", x, pct(x))


def ratio_text(x):
    return f"{x:.0f}" if x >= 10 else f"{x:.1f}"


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


def headline_numbers(N):
    """Headline case: robust when it exists (conservative), otherwise calibrated N as an upper bound."""
    robust = "robust.ew.t80.cap_twp" in N.raw
    src = "robust.ew.t80." if robust else "hist.ew.t80."
    for name in ("cap_twp", "cap_twp_m", "cap_twp_lo", "cap_twp_hi", "cap_gwp", "energy_pwh", "energy_pwh_lo",
                 "energy_pwh_hi", "density", "land_mha"):
        if src + name in N.raw:
            N.values[f"head.{name}"], N.raw[f"head.{name}"] = N.values[src + name], N.raw[src + name]
    for crop in CROPS:   # crop GCR_max of the headline case
        if src + f"gcr_{crop}" in N.raw:
            N.values[f"head.gcr_{crop}"], N.raw[f"head.gcr_{crop}"] = N.values[src + f"gcr_{crop}"], N.raw[src + f"gcr_{crop}"]
    lab = "robust" if robust else "upper bound"
    N.put("head.label", lab, lab)
    N.put("head.is_robust", float(robust), "yes" if robust else "no")
    cap = N.raw.get("head.cap_twp")
    if cap is None:
        return
    tw = cap / 1e6
    N.put("head.x_teri_lo", tw / TERI[1], ratio_text(tw / TERI[1]))   # multiple of TERI's upper value
    N.put("head.x_teri_hi", tw / TERI[0], ratio_text(tw / TERI[0]))   # multiple of TERI's lower value
    N.put("head.x_fhg", tw / FHG_HI, ratio_text(tw / FHG_HI))
    dens = N.raw.get("head.density")
    if dens:
        N.put("head.x_teri_dens_lo", dens / TERI_DENS[1], f"{dens / TERI_DENS[1]:.1f}")
        N.put("head.x_teri_dens_hi", dens / TERI_DENS[0], f"{dens / TERI_DENS[0]:.1f}")
        land = N.raw.get("head.land_mha")
        if land:   # our eligible land at TERI's fixed density: separates the land effect from the density effect
            lo, hi = land * TERI_DENS[0], land * TERI_DENS[1]   # Mha x MW/ha = TW
            N.put("head.teri_dens_twp_lo", lo, f"{lo:.0f}")
            N.put("head.teri_dens_twp_hi", hi, f"{hi:.0f}")


def framing_numbers(N):
    """Potential against India's electricity use and the land needed for national PV targets."""
    N.put("frame.cea_twh", CEA_TWH, f"{CEA_TWH:,.0f}")
    for p in ("main", "robust.ew.t80", "head"):
        e = N.raw.get(f"{p}.energy_pwh")
        if e is not None:
            x = 1000 * e / CEA_TWH
            N.put(f"frame.{p.split('.')[0]}_multiple", x, ratio_text(x))
    dens, land = N.raw.get("head.density"), N.raw.get("head.land_mha")
    if not dens or not land:
        return
    for gw in TARGETS_GW:
        mha = gw * 1e3 / dens / 1e6          # GWp -> MWp / (MWp/ha) -> ha -> Mha
        sh = 100 * mha / land
        N.put(f"frame.gw{gw}.land_mha", mha, f"{mha:.2f}")
        N.put(f"frame.gw{gw}.share", sh, f"{sh:.1f}")


def din_numbers(N, pp):
    """Vertical layout without the DIN SPEC 91434 cap (sensitivity)."""
    for p in ("hist", "robust"):
        f, u = pp / f"india_combined_{STAGES[p]}.csv", pp / f"india_combined_{STAGES[p]}_nodin.csv"
        if not (f.exists() and u.exists()):
            continue
        tc, tu = pd.read_csv(f), pd.read_csv(u)
        for tk, thr in THRS.items():
            rc, ru = sel(tc, "vertical", thr), sel(tu, "vertical", thr)
            if ru is None:
                continue
            N.put(f"{p}.vertical.{tk}.nodin.cap_twp", ru.cap_mwp_median, twp(ru.cap_mwp_median))
            if tk == "t80" and rc is not None and ru.cap_mwp_median > 0:
                x = 100 * (1 - rc.cap_mwp_median / ru.cap_mwp_median)
                N.put(f"{p}.din_cut_pct", x, pct(x))
                y = 100 * (ru.cap_mwp_median / rc.cap_mwp_median - 1)   # uncapped relative to capped
                N.put(f"{p}.din_gain_pct", y, pct(y))
        b = tu[(tu.thr.round(2) == MAIN_THR) & (tu.slope_rule == "le5")].sort_values("cap_mwp_median")
        if len(b):
            lay = LAYOUT_TEXT.get(b.iloc[-1].config, b.iloc[-1].config)
            N.put(f"{p}.nodin.best_layout", lay, lay)


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
    s2 = s2[(s2.config == MAIN_LAYOUT) & (s2.thr.round(2) == MAIN_THR) & (s2.slope_rule == "le5")]
    for i, r in enumerate(s2.sort_values("cap_mwp_median", ascending=False).head(3).itertuples(), 1):
        N.put(f"robust.top{i}_state", r.state, r.state)
        N.put(f"robust.top{i}_twp", r.cap_mwp_median / 1e6, f"{r.cap_mwp_median / 1e6:.1f}")
    tot = pd.read_csv(pp / f"india_combined_{STAGES['robust']}.csv")
    tot = tot[(tot.config == MAIN_LAYOUT) & (tot.thr.round(2) == MAIN_THR) & (tot.slope_rule == "le5")]
    if len(tot):
        x = 100 * s2.sort_values("cap_mwp_median", ascending=False).head(3).cap_mwp_median.sum() / tot.cap_mwp_median.iloc[0]
        N.put("robust.top3_share", x, pct(x))


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
    """Same text as graphical_abstract.py (ew_fixed, tau 0.8, slope <= 5%, badge = SSP5-8.5).
    Headline = robust case when present, else calibrated N labelled "upper bound"."""
    med, lo, hi = (N.raw.get(f"head.{k}") for k in ("cap_twp", "cap_twp_lo", "cap_twp_hi"))
    if "head.label" in N.values:
        N.put("ga.label", N.raw["head.is_robust"], "robust" if N.raw["head.is_robust"] else "upper bound")
    if med is not None:
        if med >= 1e6:
            nd = 1 if round(lo / 1e6, 1) != round(hi / 1e6, 1) else 2
            N.put("ga.headline", med, f"{med / 1e6:.1f} TWp")
            N.put("ga.range", lo, f"GCM range {lo / 1e6:.{nd}f}–{hi / 1e6:.{nd}f}")
        else:
            N.put("ga.headline", med, f"{med / 1e3:.0f} GWp")
            N.put("ga.range", lo, f"GCM range {lo / 1e3:.0f}–{hi / 1e3:.0f}")
    if "ssp585.change_pct" in N.raw:
        N.put("ga.change_2050", N.raw["ssp585.change_pct"], N.values["ssp585.change_pct"] + "%")
    for crop in CROPS:
        if f"head.gcr_{crop}" in N.raw:
            N.put(f"ga.gcr_{crop}", N.raw[f"head.gcr_{crop}"], N.values[f"head.gcr_{crop}"])
    src = "robust" if N.raw.get("head.is_robust") else "hist"
    for name in ("cereals", "legumes"):
        k = f"{src}.ew.t80.cover_{name}_pct"
        if k in N.raw:
            N.put(f"ga.cover_{name}_pct", N.raw[k], N.values[k])
            N.put(f"head.gcr_{name}", N.raw[f"{src}.ew.t80.gcr_{name}"], N.values[f"{src}.ew.t80.gcr_{name}"])


def reconcile_numbers(N, pp):
    """Waterfall from fixed density to this study (src/reconcile.py, main layout and threshold)."""
    f = pp / "reconcile.csv"
    if not f.exists():
        return
    t = pd.read_csv(f)
    t = t[(t.config == MAIN_LAYOUT) & (t.thr.round(2) == MAIN_THR)]
    for D, dk in ((0.42, "d42"), (0.75, "d75")):
        d = t[np.isclose(t.density_mw_ha, D)].set_index("step")
        for st, r in d.iterrows():
            N.put(f"recon.{dk}.s{st}.twp", r.gw_median / 1e3, f"{r.gw_median / 1e3:.1f}")
            N.put(f"recon.{dk}.s{st}.land_mha", r.land_mha, f"{r.land_mha:.1f}")
        if {1, 2, 3}.issubset(d.index):
            for st, name in ((2, "slope"), (3, "double")):
                x = 100 * (d.gw_median[st] / d.gw_median[st - 1] - 1)
                N.put(f"recon.{name}_pct", x, pct(x, True))
        if {1, 3}.issubset(d.index):
            x = 100 * (1 - d.land_mha[3] / d.land_mha[1])
            N.put("recon.land_cut_pct", x, pct(x))
            N.put("recon.land_keep_pct", 100 - x, pct(100 - x))
        if {3, 4}.issubset(d.index):
            x = 100 * (d.gw_median[4] / d.gw_median[3] - 1)
            N.put(f"recon.{dk}.yield_pct", x, pct(x, True))
        if {4, 5}.issubset(d.index):
            x = 100 * (d.gw_median[5] / d.gw_median[4] - 1)
            N.put("recon.robust_pct", x, pct(x, True))


def calib_numbers(N, f):
    if not f.exists():
        return
    d = pd.read_csv(f)
    d = d[d.obs_area >= 50]
    for crop in CROPS:
        for case in ("before", "after"):
            s = d[(d.crop == crop) & (d.case == case)]
            if len(s) < 3:
                continue
            r = np.corrcoef(s.obs, s.sim)[0, 1]
            mape = 100 * np.average((s.sim / s.obs - 1).abs(), weights=s.obs_area)
            ratio = np.average(s.sim / s.obs, weights=s.obs_area)           # area-weighted mean of state ratios
            pool = np.average(s.sim, weights=s.obs_area) / np.average(s.obs, weights=s.obs_area)
            N.put(f"calib.{crop}.{case}.r", r, f"{r:.2f}".replace("-", MINUS))
            N.put(f"calib.{crop}.{case}.mape", mape, pct(mape))
            N.put(f"calib.{crop}.{case}.n", len(s), f"{len(s)}")
            N.put(f"calib.{crop}.{case}.ratio", ratio, f"{ratio:.2f}")
            N.put(f"calib.{crop}.{case}.ratio_pool", pool, f"{pool:.2f}")


def group_numbers(N, p, m):
    """Cereal and legume group means of GCR_max (graphical-abstract definition: eligible-area-weighted mean of
    the five-GCM median map, all cells of the two crops pooled), main layout, tau 0.80."""
    d = m[m.config == MAIN_LAYOUT]
    for name, crops in (("cereals", CEREALS), ("legumes", LEGUMES)):
        e = d[d.crop.isin(crops)]
        if len(e):
            g = np.average(e.gcr_med, weights=e.elig_ha)
            N.put(f"{p}.ew.t80.gcr_{name}", g, f"{g:.2f}")
            N.put(f"{p}.ew.t80.cover_{name}_pct", 100 * g, f"{100 * g:.0f}")


def masking_numbers(N, c, calib_dir, calib_n):
    """Wheat at the simulated GCR limit by calibrated N level, and the open-field yield at calibrated N relative
    to 180 kg N/ha (irrigated system where simulated, else rainfed; mean of the two calibration GCMs)."""
    if not calib_n.exists():
        return
    cal = pd.read_csv(calib_n)
    cw = cal[cal.crop == "wheat"].set_index("state").n
    w = c[(c.crop == "wheat") & (c.config == MAIN_LAYOUT)].copy()
    if not len(w):
        return
    w["n"] = w.state.map(cw).fillna(cw.get("ALL", 60)).astype(int)
    tot = w.elig_ha.sum()
    for n, t in w.groupby("n"):
        s = 100 * np.average(t.at_cap.astype(float), weights=t.elig_ha)
        N.put(f"hist.wheat_n{n}.atcap", s, pct(s))
        N.put(f"hist.wheat_n{n}.area_share", 100 * t.elig_ha.sum() / tot, pct(100 * t.elig_ha.sum() / tot))
    for name, sel_ in (("lown", w.n <= 60), ("hin", w.n >= 90)):
        t = w[sel_]
        if len(t):
            s = 100 * np.average(t.at_cap.astype(float), weights=t.elig_ha)
            N.put(f"hist.wheat_{name}.atcap", s, pct(s))
            N.put(f"hist.wheat_{name}.area_share", 100 * t.elig_ha.sum() / tot, pct(100 * t.elig_ha.sum() / tot))
    o = {}
    for n in (30, 60, 90, 120, 180):
        f = calib_dir / f"ry_system_historical_n{n}_open.csv.gz"
        if not f.exists():
            return
        d = pd.read_csv(f)
        d = d[d.crop == "wheat"].groupby(["cell", "water"]).open_mean.mean().unstack()
        o[n] = d["ir"].fillna(d["rf"]) if "rf" in d else d["ir"]
    o = pd.DataFrame(o)
    cc = w.groupby("cell").agg(n=("n", "first"), atcap=("at_cap", "mean"), a=("elig_ha", "sum")).join(o, how="inner")
    cc["gap"] = [r[r.n] / r[180] for _, r in cc.iterrows()]
    for name, t in (("atcap", cc[cc.atcap >= 0.5]), ("notcap", cc[cc.atcap < 0.5])):
        if len(t):
            g = 100 * np.average(t.gap, weights=t.a)
            N.put(f"hist.wheat_{name}.open_rel180", g, pct(g))


def spearman_numbers(N, f, nuse_file):
    """Rank correlation of the calibrated state N level with state fertiliser N use (kg N per ha of gross cropped
    area, 1995-2014), states with >= 50 kha (same as src/calibrate_n.py)."""
    if not (f.exists() and nuse_file.exists()):
        return
    a = pd.read_csv(f)
    a = a[(a.case == "after") & (a.obs_area >= 50)]
    nu = pd.read_csv(nuse_file).rename(columns={"State Name": "state"})
    nu["state"] = nu.state.replace({"Orissa": "Odisha"})
    for crop in CEREALS:
        x = a[a.crop == crop].merge(nu, on="state", how="inner")
        if len(x) >= 3:
            r = x[["n", "kgN_per_ha_gca"]].corr(method="spearman").iloc[0, 1]
            N.put(f"calib.{crop}.spearman_nuse", r, f"{r:.2f}")


def energy_change_numbers(N, pp, summary, p):
    """Mid-century change in energy, specific yield, front plane-of-array irradiance and the remainder
    (performance ratio, mainly module temperature), main layout and threshold."""
    e0, e1 = N.raw.get(f"hist.ew.t80.energy_pwh"), N.raw.get(f"{p}.ew.t80.energy_pwh")
    if e0 and e1:
        x = 100 * (e1 / e0 - 1)
        N.put(f"{p}.energy_change_pct", x, pct(x, True))
    s0, s1 = N.raw.get("hist.ew.t80.sy"), N.raw.get(f"{p}.ew.t80.sy")
    if s0 and s1:
        x = 100 * (s1 / s0 - 1)
        N.put(f"{p}.sy_change_pct", x, pct(x, True))
    per = {"ssp245": "ssp245", "ssp585": "ssp585"}[p]
    fh, ff = summary / "energy_historical.csv", summary / f"energy_{per}.csv"
    cl = pp / f"cell_combined_{STAGES['hist']}.csv.gz"
    if not (fh.exists() and ff.exists() and cl.exists()):
        return
    x = pd.read_csv(fh).merge(pd.read_csv(ff), on=["cell", "config", "gcr"], suffixes=("_h", "_f"))
    x = x[x.config == MAIN_LAYOUT]
    land = pd.read_csv(cl)
    land = land[(land.config == MAIN_LAYOUT) & (land.thr.round(2) == MAIN_THR) & (land.slope_rule == "le5")]
    land = land.groupby("cell").land_ha.first()
    x = x.join(land, on="cell").dropna(subset=["land_ha"])
    if not len(x):
        return
    w = x.land_ha
    sy = np.average(x.yield_kwh_kwp_f, weights=w) / np.average(x.yield_kwh_kwp_h, weights=w) - 1
    poa = np.average(x.poa_front_kwh_m2_f * (1 + x.rear_gain_f), weights=w) / \
        np.average(x.poa_front_kwh_m2_h * (1 + x.rear_gain_h), weights=w) - 1
    pr = (1 + sy) / (1 + poa) - 1
    N.put(f"{p}.irr_change_pct", 100 * poa, f"{100 * poa:+.1f}".replace("-", MINUS))
    N.put(f"{p}.pr_change_pct", 100 * pr, f"{100 * pr:+.1f}".replace("-", MINUS))


def open_field_change_numbers(N, summary, c, p):
    """Mid-century change of open-field legume yields and of RY at GCR 0.3 (main layout); per cell the mean over
    GCMs, then the eligible-area-weighted median over cells. CO2 is included in the future runs."""
    fh, ff = summary / "ry_crop_historical_current.csv.gz", summary / f"ry_crop_{STAGES[p]}.csv.gz"
    if not (fh.exists() and ff.exists()):
        return
    k = ["cell", "crop", "config", "gcr"]
    a = pd.read_csv(fh)
    b = pd.read_csv(ff)
    a = a[(a.config == MAIN_LAYOUT) & (a.gcr.round(2) == 0.3)].groupby(k)[["open", "ry"]].mean()
    b = b[(b.config == MAIN_LAYOUT) & (b.gcr.round(2) == 0.3)].groupby(k)[["open", "ry"]].mean()
    x = a.join(b, lsuffix="_h", rsuffix="_f", how="inner").reset_index()
    el = c[c.config == MAIN_LAYOUT].groupby(["cell", "crop"]).elig_ha.mean().rename("w").reset_index()
    x = x.merge(el, on=["cell", "crop"])
    for crop in CROPS:
        t = x[(x.crop == crop) & (x.w > 0) & (x.open_h > 0)]
        if len(t):
            g = wmedian(100 * (t.open_f / t.open_h - 1), t.w)
            N.put(f"{p}.open_{crop}_pct", g, pct(g, True))
            r = wmedian(t.ry_f - t.ry_h, t.w)
            N.put(f"{p}.ry03_{crop}_delta", r, "0.00" if abs(r) < 0.005 else f"{r:+.2f}".replace("-", MINUS))


def pilot_numbers(N, pilot, jodhpur):
    """Rajasthan pilot (runs/rajasthan_final, SM Section S9) and the Jodhpur single-cell soil test (results/)."""
    f, g = pilot / "ry_ensemble.csv", pilot / "gcr_max.csv"
    if f.exists():
        d = pd.read_csv(f)
        N.put("pilot.n_cells", d.cell.nunique(), f"{d.cell.nunique()}")
        h = d[d.period == "historical"]
        for crop in ("wheat", "pearl_millet"):
            for mg in ("farmer", "recommended"):
                for gcr in (0.3, 0.5):
                    t = h[(h.system == crop) & (h.config == "south_fixed") & (h.mgmt == mg) & (h.gcr.round(2) == gcr)]
                    if len(t):
                        v = t.ry_med.median()
                        N.put(f"pilot.{crop}.south.{mg}.g{int(gcr * 10)}", v, f"{v:.2f}")
        kk = ["cell", "mgmt", "system", "config", "gcr"]
        x = h[kk + ["ry_med"]].merge(d[d.period == "ssp245"][kk + ["ry_med"]], on=kk)
        if len(x):
            v = (x.ry_med_y - x.ry_med_x).groupby([x.system, x.config]).median().abs().max()
            N.put("pilot.ssp245_ry_change_max", v, f"{v:.2f}")
    if g.exists():
        m = pd.read_csv(g)
        m = m[m.period == "historical"]
        med = m.groupby(["mgmt", "system", "config"]).gcr_max.median()
        for crop, systems in (("chickpea", ["chickpea_irrigated", "chickpea_rainfed", "chickpea_mix"]),
                              ("groundnut", ["groundnut_irrigated", "groundnut_rainfed"]),
                              ("wheat", ["wheat"]), ("pearl_millet", ["pearl_millet"])):
            v = med.loc["farmer"][med.loc["farmer"].index.get_level_values(0).isin(systems)]
            if len(v):
                N.put(f"pilot.{crop}.gcr_lo", v.min(), f"{v.min():.1f}")
                N.put(f"pilot.{crop}.gcr_hi", v.max(), f"{v.max():.1f}")
        if "recommended" in med.index.get_level_values(0):
            r = med.loc["recommended"].loc["wheat"]
            for cfg, lk in LAYOUTS.items():
                if lk in r.index:
                    N.put(f"pilot.wheat.rec.{cfg}.gcr", r[lk], f"{r[lk]:.1f}")
    for soil in ("soilgrids", "loamy_sand"):
        o, s = jodhpur / f"{soil}_F" / "open_field_yield.csv", jodhpur / f"{soil}_F" / "pilot_summary.csv"
        if o.exists():
            y = pd.read_csv(o).set_index("crop")["mean"].get("pearl_millet")
            if y is not None:
                N.put(f"jodhpur.{soil}.millet_open", y, f"{y:.0f}")
        if s.exists():
            t = pd.read_csv(s)
            t = t[(t.crop == "pearl_millet") & (t.config == "south_fixed") & (t.gcr.round(2) == 0.3)]
            if len(t):
                N.put(f"jodhpur.{soil}.millet_ry_s03", t.ry.iloc[0], f"{t.ry.iloc[0]:.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pp", type=Path, default=Path("results/potential"))
    ap.add_argument("--validation", type=Path, default=Path("results/validation_before_after.csv"))
    ap.add_argument("--summary", type=Path, default=Path("runs/s1/summary"), help="stage summaries (energy, ry_crop)")
    ap.add_argument("--calib-dir", type=Path, default=Path("runs/calib/cal"), help="N calibration sweep")
    ap.add_argument("--calib-n", type=Path, default=Path("prod/calib_n.csv"))
    ap.add_argument("--nuse", type=Path, default=Path("data/yields/state_n_use_1995_2014.csv"))
    ap.add_argument("--pilot", type=Path, default=Path("runs/rajasthan_final"))
    ap.add_argument("--jodhpur", type=Path, default=Path("results"), help="Jodhpur single-cell soil test")
    a = ap.parse_args()
    N = Numbers()
    present = {p: st for p, st in STAGES.items() if (a.pp / f"india_combined_{st}.csv").exists()}
    for p, st in present.items():
        t, m, c = stage_numbers(N, p, a.pp, st)
        group_numbers(N, p, m)
        if p == "robust":   # GCR_max spread for the robust headline (same definitions as hist_extras)
            d = m[m.config == MAIN_LAYOUT]
            if len(d):
                for q, nm in ((0.05, "gcr_p05"), (0.95, "gcr_p95")):
                    x = wquant(d.gcr_med, d.elig_ha, q)
                    N.put(f"robust.{nm}", x, f"{x:.2f}")
                ce = d[d.crop.isin(CEREALS)]
                if len(ce):
                    x = wmedian(ce.gcr_med, ce.elig_ha)
                    N.put("robust.cereal_gcr_med", x, f"{x:.2f}")
        if p == "hist":
            hist_extras(N, a.pp, t, m, c)
            masking_numbers(N, c, a.calib_dir, a.calib_n)
            c_hist = c
    main_aliases(N)
    robust_numbers(N, a.pp)
    headline_numbers(N)
    framing_numbers(N)
    din_numbers(N, a.pp)
    for p in ("ssp245", "ssp585"):
        future_numbers(N, a.pp, p)
        if p in present:
            energy_change_numbers(N, a.pp, a.summary, p)
            if "hist" in present:
                open_field_change_numbers(N, a.summary, c_hist, p)
    ga_numbers(N)
    reconcile_numbers(N, a.pp)
    calib_numbers(N, a.validation)
    spearman_numbers(N, a.validation, a.nuse)
    pilot_numbers(N, a.pilot, a.jodhpur)
    out = {"meta": {"stages": present, "main_case": {"layout": MAIN_LAYOUT, "thr": MAIN_THR, "slope": "le5",
                                                     "management": "calibrated N"},
                    "headline": N.values.get("head.label"), "din_cap_vertical": 0.6,
                    "cea_requirement_2025_26_twh": CEA_TWH,
                    "units": "cap_twp TWp (raw MWp), cap_gwp GWp, land_mha Mha, energy_pwh PWh/yr, "
                             "density MWp/ha, sy kWh/kWp/yr, *_share and *_pct in %"},
           "values": dict(sorted(N.values.items())), "raw": dict(sorted(N.raw.items()))}
    f = a.pp / "numbers.json"
    f.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"wrote {f}: {len(N.values)} numbers, stages {', '.join(present) or 'none'}")


if __name__ == "__main__":
    main()
