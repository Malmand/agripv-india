"""Calibrate DSSAT management to ICRISAT DLD district yields (Jodhpur, 1995-2014).

Grid search over nitrogen rate and irrigation trigger (auto-irrigation when
available soil water in the top 30 cm falls below ITHRL %), Penman-Monteith ET,
SoilGrids soil. Score = |mean bias| / district mean; r = Pearson correlation of
annual series. Season year = sowing year (ICRISAT agricultural year).
"""
import sys, itertools, warnings
from pathlib import Path
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
import dssat_pilot as dp
from dssat_inputs import soil_from_soilgrids, weather_station

w = pd.read_csv(ROOT / "data/weather/jodhpur_power_1995_2014.csv")
ws = weather_station(w, "OPNJ", 26.375, 73.125)
soil = soil_from_soilgrids(ROOT / "data/soil/soilgrids_R0214.json")
dld = pd.read_csv(ROOT / "data/yields/rajasthan_dld_full.csv")
j = dld[(dld["Dist Name"] == "Jodhpur") & dld.Year.between(1995, 2014)].set_index("Year")
OBS = {"wheat": j["WHEAT YIELD (Kg per ha)"], "chickpea": j["CHICKPEA YIELD (Kg per ha)"],
       "groundnut": j["GROUNDNUT YIELD (Kg per ha)"]}

_orig_irr = dp.AMIrrigation
def run(crop, n, irrig, ithrl):
    base = dict(dp.CROPS[crop])
    split = [(0, n / 2), (30, n / 2)] if crop == "wheat" else [(0, n)]
    dp.CROPS[crop] = {**base, "n": split if n > 0 else [], "irrig": irrig}
    dp.AMIrrigation = lambda **k: _orig_irr(**{**k, "ithrl": ithrl})
    try:
        y = dp.run_one(crop, ws, soil, evapo="F").set_index("season").hwam
    finally:
        dp.CROPS[crop] = base
        dp.AMIrrigation = _orig_irr
    return y

GRID = {"wheat": (["A"], [40, 60, 90, 120], [20, 35, 50]),
        "chickpea": (["N", "A"], [0, 20], [20, 35]),
        "groundnut": (["N", "A"], [0, 20], [20, 35, 50])}
rows = []
for crop, (irrs, ns, ths) in GRID.items():
    obs = OBS[crop]
    for irrig, n, th in itertools.product(irrs, ns, ths):
        if irrig == "N" and th != ths[0]:
            continue
        y = run(crop, n, irrig, th)
        c = y.index.intersection(obs.index)
        rows.append(dict(crop=crop, irrig=irrig, N=n, ithrl=th if irrig == "A" else None,
                         model_mean=round(y[c].mean()), obs_mean=round(obs[c].mean()),
                         bias_pct=round(100 * (y[c].mean() / obs[c].mean() - 1)),
                         model_sd=round(y[c].std()), obs_sd=round(obs[c].std()),
                         r=round(np.corrcoef(y[c], obs[c])[0, 1], 2)))
        print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv(ROOT / "results/calibration_dld_jodhpur.csv", index=False)
