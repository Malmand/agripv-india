#!/usr/bin/env python3
"""Screening-level economics of the yield-constrained APV potential (robust case, east-west, tau 0.80, slope <= 5%).

Inputs (all sourced in the manuscript):
  * minimum support prices (MSP) of the four crops, Government of India (PIB, 1 Oct 2025 and 13 May 2026);
  * observed state mean yields 1995-2014 (ICRISAT district database, area weighted);
  * PV price: levelised tariff of the PM-KUSUM Component A in Gujarat, ceiling Rs 2.95/kWh and discovered Rs 2.77-2.78/kWh
    (GERC order, Petition 2603 of 2026);
  * elevated-structure cost premium, +38% on LCOE over ground-mounted PV (Schindele et al. 2020, Appl Energy 265:114737) and +25-30% (Union Minister for New and Renewable Energy, Oct 2026).
The cost of ground-mounted PV is set to the discovered auction price (Rs 2.775/kWh) at the national median specific yield
of our array; cell LCOE scales inversely with its simulated specific yield. This is a screening estimate, not a project
appraisal: it ignores land lease, grid connection, crop input costs and the value of the crop under shade beyond RY.
Outputs: results/economics/{econ_numbers.json, econ_supply.csv, econ_scenarios.csv}
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path

R = Path(__file__).resolve().parent.parent
OUT = R / "results" / "economics"
OUT.mkdir(parents=True, exist_ok=True)
PP = R / "results" / "potential"
TAU, SLOPE, CFG = 0.80, "le5", "ew_fixed"

MSP = {"wheat": 2585.0, "chickpea": 5875.0, "pearl_millet": 2900.0, "groundnut": 7517.0}   # Rs per quintal (100 kg)
TARIFF_CEIL, TARIFF_AUCTION = 2.95, 2.775                                                  # Rs per kWh
PREMIA = (0.0, 0.25, 0.30, 0.38)                                                                  # APV structure premium on LCOE
BASE_PREM = 0.38

# observed state yields (kg/ha), ICRISAT 1995-2014, area weighted
d = pd.read_csv(R / "data/yields/kaggle_raw/ICRISAT-District Level Data.csv")
d = d[(d.Year >= 1995) & (d.Year <= 2014)]
cols = {"wheat": "WHEAT", "chickpea": "CHICKPEA", "pearl_millet": "PEARL MILLET", "groundnut": "GROUNDNUT"}
state_map = {"Orissa": "Odisha"}
d["state"] = d["State Name"].replace(state_map)
yld = {}
for crop, nm in cols.items():
    g = d.groupby("state")[[f"{nm} AREA (1000 ha)", f"{nm} PRODUCTION (1000 tons)"]].sum()
    g = g[g.iloc[:, 0] > 0]
    s = (g.iloc[:, 1] / g.iloc[:, 0]) * 1000.0           # kg/ha
    s["__national__"] = g.iloc[:, 1].sum() / g.iloc[:, 0].sum() * 1000.0
    yld[crop] = s

cc = pd.read_csv(PP / "cell_crop_historical_current_robust.csv.gz")
cc = cc[(cc.config == CFG) & (cc.slope_rule == SLOPE) & (cc.thr.round(2) == TAU)].copy()
cb = pd.read_csv(PP / "cell_combined_historical_current_robust.csv.gz")
cb = cb[(cb.config == CFG) & (cb.slope_rule == SLOPE) & (cb.thr.round(2) == TAU)].copy()
cb["sy"] = cb.energy_gwh / cb.cap_mwp * 1000.0           # kWh per kWp per year

def crop_yield(r):
    s = yld[r.crop]
    return s.get(r.state, s["__national__"])
cc["y_kg"] = cc.apply(crop_yield, axis=1)
cc["value_rs"] = cc.elig_ha * cc.y_kg / 100.0 * cc.crop.map(MSP)     # gross crop value of the eligible area, Rs/yr

rows, sup, nums = [], [], {}
for m, g in cb.groupby("model"):
    sy0 = np.average(g.sy, weights=g.cap_mwp) if False else float(np.median(np.repeat(g.sy.values, np.maximum(1, (g.cap_mwp.values / 50).astype(int)))))
    crop_val = cc[cc.model == m].value_rs.sum()
    e_gwh, cap, ha = g.energy_gwh.sum(), g.cap_mwp.sum(), g.land_ha.sum()
    rec = dict(model=m, sy_ref=sy0, crop_value_bn=crop_val / 1e9, crop_loss_max_bn=(1 - TAU) * crop_val / 1e9,
               energy_twh=e_gwh / 1e3, cap_twp=cap / 1e6, land_mha=ha / 1e6,
               rev_ceil_bn=e_gwh * 1e6 * TARIFF_CEIL / 1e9, rev_auction_bn=e_gwh * 1e6 * TARIFF_AUCTION / 1e9)
    for p in PREMIA:
        lcoe = TARIFF_AUCTION * (1 + p) * sy0 / g.sy
        rec[f"lcoe_w_{int(p*100)}"] = float(np.average(lcoe, weights=g.energy_gwh))
        rec[f"share_ceil_{int(p*100)}"] = 100 * g.cap_mwp[lcoe <= TARIFF_CEIL].sum() / cap
        rec[f"share_auction_{int(p*100)}"] = 100 * g.cap_mwp[lcoe <= TARIFF_AUCTION + 1e-9].sum() / cap
        net = (TARIFF_CEIL - lcoe) * g.energy_gwh * 1e6           # Rs/yr net PV margin at the ceiling tariff
        rec[f"net_bn_{int(p*100)}"] = net.sum() / 1e9
        rec[f"net_pos_bn_{int(p*100)}"] = net[net > 0].sum() / 1e9
        rec[f"adder_{int(p*100)}"] = float(max(0.0, np.average(lcoe, weights=g.energy_gwh) - TARIFF_CEIL))
        if m == "GFDL-ESM4" or True:
            o = np.argsort(lcoe.values)
            sup.append(pd.DataFrame(dict(model=m, premium=p, lcoe=lcoe.values[o], cum_twp=np.cumsum(g.cap_mwp.values[o]) / 1e6)))
    rows.append(rec)
S = pd.DataFrame(rows)
S.to_csv(OUT / "econ_scenarios.csv", index=False)
SUP = pd.concat(sup)
SUP.to_csv(OUT / "econ_supply.csv", index=False)

med = S.median(numeric_only=True)
rng = lambda c: (float(S[c].min()), float(S[c].max()))
N = {}
def put(k, v, f): N[k] = {"raw": float(v), "txt": f}
put("econ.crop_value_bn", med.crop_value_bn, f"{med.crop_value_bn:,.0f}")
put("econ.crop_loss_max_bn", med.crop_loss_max_bn, f"{med.crop_loss_max_bn:.0f}")
put("econ.crop_value_per_ha", med.crop_value_bn * 1e9 / (med.land_mha * 1e6) / 1e3, f"{med.crop_value_bn * 1e9 / (med.land_mha * 1e6) / 1e3:.0f}")
put("econ.rev_ceil_bn", med.rev_ceil_bn, f"{med.rev_ceil_bn:,.0f}")
put("econ.rev_ceil_tn", med.rev_ceil_bn / 1e3, f"{med.rev_ceil_bn / 1e3:.0f}")
put("econ.rev_per_ha_lakh", med.rev_ceil_bn * 1e9 / (med.land_mha * 1e6) / 1e5, f"{med.rev_ceil_bn * 1e9 / (med.land_mha * 1e6) / 1e5:.0f}")
put("econ.ratio_rev_crop", med.rev_ceil_bn / med.crop_value_bn, f"{med.rev_ceil_bn / med.crop_value_bn:.0f}")
put("econ.sy_ref", med.sy_ref, f"{med.sy_ref:,.0f}")
for p in PREMIA:
    k = int(p * 100)
    put(f"econ.lcoe_{k}", med[f"lcoe_w_{k}"], f"{med[f'lcoe_w_{k}']:.2f}")
    put(f"econ.share_ceil_{k}", med[f"share_ceil_{k}"], f"{med[f'share_ceil_{k}']:.0f}")
    put(f"econ.adder_{k}", med[f"adder_{k}"], f"{med[f'adder_{k}']:.2f}")
    put(f"econ.net_{k}", med[f"net_bn_{k}"], f"{med[f'net_bn_{k}']:,.0f}")
    put(f"econ.net_per_ha_{k}", med[f"net_bn_{k}"] * 1e9 / (med.land_mha * 1e6) / 1e3, f"{med[f'net_bn_{k}'] * 1e9 / (med.land_mha * 1e6) / 1e3:,.0f}")
    # twp that clears the ceiling tariff
    tw = np.median([ (SUP[(SUP.model == m) & (SUP.premium == p) & (SUP.lcoe <= TARIFF_CEIL)].cum_twp.max() if ((SUP.model == m) & (SUP.premium == p) & (SUP.lcoe <= TARIFF_CEIL)).any() else 0.0) for m in S.model])
    put(f"econ.twp_ceil_{k}", tw, f"{tw:.1f}")
# yield-protected value: tariff adder that would cover the structure premium, per hectare vs crop value
prem_cost_per_kwh = TARIFF_AUCTION * BASE_PREM
put("econ.prem_per_kwh", prem_cost_per_kwh, f"{prem_cost_per_kwh:.2f}")
put("econ.prem_bn", prem_cost_per_kwh * med.energy_twh * 1e9 / 1e9, f"{prem_cost_per_kwh * med.energy_twh:,.0f}")
put("econ.prem_ratio_crop", prem_cost_per_kwh * med.energy_twh / med.crop_value_bn, f"{prem_cost_per_kwh * med.energy_twh / med.crop_value_bn:.1f}")
put("econ.msp_wheat", MSP["wheat"], f"{MSP['wheat']:,.0f}")

e_ha = med.energy_twh * 1e9 / (med.land_mha * 1e6)              # kWh per ha per year
cv_ha = med.crop_value_bn * 1e9 / (med.land_mha * 1e6)          # Rs per ha per year
be_ceil = 100 * (TARIFF_CEIL / TARIFF_AUCTION - 1)              # premium that exhausts the ceiling tariff, % (median yield)
be_crop = 100 * cv_ha / (TARIFF_AUCTION * e_ha)                 # premium whose cost equals the crop value per ha, %
put("econ.be_ceil_pct", be_ceil, f"{be_ceil:.0f}")
put("econ.be_crop_pct", be_crop, f"{be_crop:.1f}")
put("econ.e_ha_mwh", e_ha / 1e3, f"{e_ha / 1e3:,.0f}")
put("econ.adder_per_ha_lakh", med.adder_38 * e_ha / 1e5, f"{med.adder_38 * e_ha / 1e5:.0f}")
put("econ.adder25_per_ha_lakh", med.adder_25 * e_ha / 1e5, f"{med.adder_25 * e_ha / 1e5:.0f}")
put("econ.prem_per_ha_lakh", prem_cost_per_kwh * e_ha / 1e5, f"{prem_cost_per_kwh * e_ha / 1e5:.0f}")
put("econ.crop_value_per_ha_lakh", cv_ha / 1e5, f"{cv_ha / 1e5:.2f}")
put("econ.tariff_ceiling", TARIFF_CEIL, f"{TARIFF_CEIL:.2f}")
put("econ.tariff_auction", TARIFF_AUCTION, "2.77–2.78")
json.dump(N, open(OUT / "econ_numbers.json", "w"), indent=1)
for k, v in N.items(): print(k, v["txt"])
print(S[["model", "crop_value_bn", "energy_twh", "sy_ref", "lcoe_w_38", "share_ceil_38"]])
