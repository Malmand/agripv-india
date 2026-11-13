"""Share of the eligible rabi land (wheat, chickpea) whose kharif crop is not one of the simulated ones
(pearl millet, groundnut) and therefore is not checked against the yield rule. ICRISAT District Level Data,
1995-2014 mean areas by district. Rabi area R = wheat + chickpea; simulated kharif Ks = pearl millet + groundnut;
other kharif Ko = rice + maize + kharif sorghum + finger millet + pigeonpea + soybean + cotton + sesamum.
Upper estimate: as in the paper, Ks overlaps R first, the rest of R is followed by Ko as far as it reaches.
Lower estimate: the double-cropped part of R, min(R, Ks+Ko), is shared by Ks and Ko in proportion to area.
District shares are aggregated to states and weighted by each state's eligible rabi land in the headline case.
Usage: python src/kharif_overlap.py  -> results/kharif_overlap.csv, prints national shares
"""
import pandas as pd
d = pd.read_csv("data/yields/kaggle_raw/ICRISAT-District Level Data.csv")
d = d[(d.Year >= 1995) & (d.Year <= 2014)]
A = lambda c: f"{c} AREA (1000 ha)"
ko_cols = ["RICE", "MAIZE", "KHARIF SORGHUM", "FINGER MILLET", "PIGEONPEA", "SOYABEAN", "COTTON", "SESAMUM"]
cols = [A(c) for c in ["WHEAT", "CHICKPEA", "PEARL MILLET", "GROUNDNUT"] + ko_cols]
g = d.groupby(["State Name", "Dist Name"])[cols].mean().clip(lower=0).fillna(0)
R = g[A("WHEAT")] + g[A("CHICKPEA")]
Ks = g[A("PEARL MILLET")] + g[A("GROUNDNUT")]
Ko = sum(g[A(c)] for c in ko_cols)
rest = (R - Ks.clip(upper=R)).clip(lower=0)
up = rest.clip(upper=Ko)                                   # max overlap of R with unsimulated kharif
up_rice = rest.clip(upper=g[A("RICE")])                     # rice first
dbl = R.clip(upper=Ks + Ko)
lo = (dbl * Ko / (Ks + Ko).where(Ks + Ko > 0)).fillna(0)
t = pd.DataFrame({"R": R, "up": up, "up_rice": up_rice, "lo": lo,
                  "lo_rice": (dbl * g[A("RICE")] / (Ks + Ko).where(Ks + Ko > 0)).fillna(0)}).groupby(level=0).sum()
for k in ["up", "up_rice", "lo", "lo_rice"]:
    t[k + "_share"] = t[k] / t.R
# eligible rabi land by state, headline case (east-west, tau 0.80, slope <= 5%, robust), first model (land is model-independent)
c = pd.read_csv("results/potential/cell_crop_historical_current_robust.csv.gz")
c = c[(c.config == "ew_fixed") & (c.thr == 0.8) & (c.slope_rule == "le5") & c.crop.isin(["wheat", "chickpea"])]
c = c[c.model == c.model.iloc[0]]
el = c.groupby("state").elig_ha.sum()
name = {"Orissa": "Odisha", "Chhattisgarh": "Chhattisgarh", "Uttarakhand": "Uttarakhand", "Jharkhand": "Jharkhand",
        "Telangana": "Telangana"}
t.index = [name.get(s, s) for s in t.index]
el_t = el.copy()
# DLD keeps pre-2000 boundaries: merge new states into parents for the weights
parent = {"Telangana": "Andhra Pradesh", "Uttarakhand": "Uttar Pradesh", "Jharkhand": "Bihar", "Chhattisgarh": "Madhya Pradesh",
          "Ladakh": "Jammu & Kashmir", "Delhi": "Haryana", "Puducherry": "Tamil Nadu", "Goa": "Maharashtra"}
el_t.index = [parent.get(s, s) for s in el_t.index]
el_t = el_t.groupby(level=0).sum()
t = t.join(el_t.rename("elig_rabi_ha"), how="outer")
miss = t[t.R.isna() & (t.elig_rabi_ha > 0)]
if len(miss):
    print("eligible land without DLD state:", miss.elig_rabi_ha.round(0).to_dict())
t = t.dropna(subset=["R"]).fillna({"elig_rabi_ha": 0})
w = t.elig_rabi_ha / t.elig_rabi_ha.sum()
res = {k: float((t[k + "_share"] * w).sum() * 100) for k in ["lo", "up", "lo_rice", "up_rice"]}
t.to_csv("results/kharif_overlap.csv")
print(t[["elig_rabi_ha", "lo_share", "up_share", "up_rice_share"]].sort_values("elig_rabi_ha", ascending=False).round(2).head(12))
print({k: round(v, 1) for k, v in res.items()}, "eligible rabi Mha", round(el.sum() / 1e6, 1))
