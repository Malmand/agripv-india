"""Relative yield under shade at farmer practice calibrated to ICRISAT DLD (Jodhpur).

wheat: 60 kg N/ha split, auto-irrigation at 50% ASW (district mean -11%)
chickpea: rainfed and irrigated (20% ASW trigger) systems; district = 26% irrigated mix
groundnut: rainfed and irrigated (20% ASW) systems
pearl millet: rainfed, 10 kg N/ha (district mean +22%, r = 0.45)
"""
import sys, warnings
from pathlib import Path
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
import dssat_pilot as dp, pv_shading as ps
from dssat_inputs import soil_from_soilgrids, weather_station

w = pd.read_csv(ROOT / "data/weather/jodhpur_power_1995_2014.csv", parse_dates=["date"])
soil = soil_from_soilgrids(ROOT / "data/soil/soilgrids_R0214.json")
h = ps.hourly_from_daily(26.375, 73.125, w.date, w.srad_MJ)
SYSTEMS = {  # name: (crop, N schedule, irrig, ithrl)
    "wheat_farmer": ("wheat", [(0, 30), (30, 30)], "A", 50),
    "chickpea_rainfed": ("chickpea", [], "N", 20),
    "chickpea_irrigated": ("chickpea", [], "A", 20),
    "groundnut_rainfed": ("groundnut", [], "N", 20),
    "groundnut_irrigated": ("groundnut", [], "A", 20),
    "pearl_millet_farmer": ("pearl_millet", [(0, 10)], "N", 20),
}
_irr = dp.AMIrrigation

def run(sysname, wdf, insi):
    crop, n, irrig, th = SYSTEMS[sysname]
    base = dict(dp.CROPS[crop])
    dp.CROPS[crop] = {**base, "n": n, "irrig": irrig}
    dp.AMIrrigation = lambda **k: _irr(**{**k, "ithrl": th})
    try:
        return dp.run_one(crop, weather_station(wdf, insi, 26.375, 73.125), soil, evapo="F").hwam.sum()
    finally:
        dp.CROPS[crop] = base
        dp.AMIrrigation = _irr

rows = []
openy = {s: run(s, w, "OPNJ") for s in SYSTEMS}
for cfg_name, c1 in [("south_fixed", "S"), ("ew_fixed", "E"), ("vertical", "V")]:
    cfg = ps.make_config(cfg_name)
    for gi, gcr in enumerate([0.1, 0.2, 0.3, 0.4, 0.5], 1):
        geo = ps.strip_geometry(cfg, gcr)
        f = ps.daily_factors(h, cfg, geo); f.index = pd.to_datetime(f.index)
        tot = {s: 0.0 for s in SYSTEMS}
        for k in f.columns:
            wdf = w.copy(); wdf["srad_MJ"] = (w.srad_MJ.values * f[k].reindex(w.date).values).round(1)
            for s in SYSTEMS:
                tot[s] += run(s, wdf, f"{c1}{gi}{k + 1}F")
        for s in SYSTEMS:
            rows.append(dict(system=s, config=cfg_name, gcr=gcr,
                             ry=tot[s] / len(f.columns) * geo["cult_frac"] / openy[s]))
        print("done", cfg_name, gcr, flush=True)
d = pd.DataFrame(rows)
# district-mix chickpea (26% irrigated) as area-weighted system
mix = []
for (c, g), gg in d[d.system.str.startswith("chickpea")].groupby(["config", "gcr"]):
    ri = gg.set_index("system").ry
    yi, yr = openy["chickpea_irrigated"], openy["chickpea_rainfed"]
    mix.append(dict(system="chickpea_district_mix", config=c, gcr=g,
                    ry=(0.26 * yi * ri["chickpea_irrigated"] + 0.74 * yr * ri["chickpea_rainfed"]) / (0.26 * yi + 0.74 * yr)))
d = pd.concat([d, pd.DataFrame(mix)])
d.to_csv(ROOT / "results/ry_farmer_practice.csv", index=False)
print(d.pivot_table(index=["system", "config"], columns="gcr", values="ry").round(2).to_string())
print({k: round(v / 20) for k, v in openy.items()})
