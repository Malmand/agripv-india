"""Cell-level share of eligible rabi land (wheat, chickpea) followed by a kharif crop that is not simulated,
from MapSPAM 2010 (data/grid_india_025_kharif.csv). Headline case: east-west, tau 0.80, slope <= 5%, robust.
Upper: simulated kharif crops (pearl millet, groundnut) take rabi land first, as in the potential; the rest of the
rabi land carries other kharif crops as far as their area reaches. Proportional: the double-cropped part of the
rabi land, min(R, Ks + Ko), is shared by simulated and other kharif crops in proportion to area.
Other kharif: rice, maize, soybean, cotton, sorghum, pigeonpea (sugarcane is annual and excluded).
Writes results/kharif_overlap_spam.csv; prints national shares and the capacity they carry.
"""
import json
import numpy as np
import pandas as pd

g = pd.read_csv("data/grid_india_025_kharif.csv").set_index("cell_id")
R = g.wheat_ha + g.chickpea_ha
Ks = g.pearl_millet_ha + g.groundnut_ha
oth = ["rice", "maize", "soybean", "cotton", "sorghum", "pigeonpea"]
Ko = sum(g[f"{c}_ha"] for c in oth)
rest = (R - np.minimum(R, Ks)).clip(lower=0)
dbl = np.minimum(R, Ks + Ko)
den = (Ks + Ko).where(Ks + Ko > 0)
sh = pd.DataFrame(index=g.index)
sh["up"] = np.minimum(rest, Ko) / R.where(R > 0)
sh["prop"] = (dbl * Ko / den).fillna(0) / R.where(R > 0)
# rice first (as in the potential with rice, postprocess --rice-stage), the rest split by area among the others
sh["up_rice"] = (np.minimum(rest, g.rice_ha) / R.where(R > 0)).fillna(0)
Kn = Ko - g.rice_ha
for c in oth[1:]:
    sh[f"up_{c}"] = ((sh.up - sh.up_rice) * g[f"{c}_ha"] / Kn.where(Kn > 0)).fillna(0)
sh = sh.fillna(0)
c = pd.read_csv("results/potential/cell_crop_historical_current_robust.csv.gz")
c = c[(c.config == "ew_fixed") & (c.thr == 0.8) & (c.slope_rule == "le5") & c.crop.isin(["wheat", "chickpea"])]
cc = pd.read_csv("results/potential/cell_combined_historical_current_robust.csv.gz")
cc = cc[(cc.config == "ew_fixed") & (cc.thr == 0.8) & (cc.slope_rule == "le5")]
m0 = c.model.iloc[0]
el = c[c.model == m0].groupby("cell").elig_ha.sum()
w = el / el.sum()
res = {k: float((sh.loc[el.index, k] * w).sum() * 100) for k in sh.columns}
rab = c.groupby(["model", "cell"]).cap_mwp.sum().reset_index()
tot = cc.groupby("model").cap_mwp.sum()
cap = {}
for k in ["up", "prop", "up_rice"]:
    ex = rab.assign(x=rab.cap_mwp * rab.cell.map(sh[k])).groupby("model").x.sum()
    cap[k] = (round(float((ex / 1e6).median()), 1), round(float(((tot - ex) / 1e6).median()), 1))
out = sh.join(el.rename("elig_rabi_ha"), how="left")
out.to_csv("results/kharif_overlap_spam.csv")
json.dump({"share_pct": res, "cap_twp": {k: {"on_land": v[0], "remaining": v[1]} for k, v in cap.items()},
           "elig_rabi_mha": float(el.sum() / 1e6)}, open("results/kharif_overlap_spam.json", "w"), indent=1)
print("eligible rabi land Mha", round(el.sum() / 1e6, 1))
print("share of eligible rabi land followed by an unsimulated kharif crop (%):", {k: round(v, 1) for k, v in res.items()})
print("capacity on that land / remaining (TWp, GCM median) of", round(float(tot.median() / 1e6), 1), ":", cap)
