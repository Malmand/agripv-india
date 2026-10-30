"""Week 2 pilot run for the CAZRI Jodhpur cell (R0214, 26.375 N 73.125 E).

Outputs
  results/pilot_strips.csv   season x crop x config x GCR x strip yields
  results/pilot_ry.csv       field-level relative yield per season
  results/pilot_summary.csv  mean, P10 and pass/fail at 66/80/90% thresholds
  results/light_factors.csv  annual and crop-season mean ground-light factor
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
import pv_shading as ps                                     # noqa: E402
from dssat_inputs import soil_from_soilgrids, loamy_sand_profile, weather_station  # noqa: E402
from dssat_pilot import run_one, CROPS                      # noqa: E402

LAT, LON = 26.375, 73.125
CONFIGS = {"south_fixed": "S", "ew_fixed": "E", "vertical": "V"}
GCRS = [0.1, 0.2, 0.3, 0.4, 0.5]
THRESH = [0.66, 0.80, 0.90]


def main(soil_kind="soilgrids", evapo="R", tag=""):
    """soil_kind: 'soilgrids' or 'loamy_sand'; evapo: 'R' Priestley-Taylor/Ritchie, 'F' FAO-56 PM."""
    out = ROOT / "results" / (tag or f"{soil_kind}_{evapo}")
    out.mkdir(parents=True, exist_ok=True)
    w = pd.read_csv(ROOT / "data/weather/jodhpur_power_1995_2014.csv", parse_dates=["date"])
    soil = (loamy_sand_profile() if soil_kind == "loamy_sand"
            else soil_from_soilgrids(ROOT / "data/soil/soilgrids_R0214.json"))
    hourly = ps.hourly_from_daily(LAT, LON, w.date, w.srad_MJ)

    rows, light = [], []
    for crop in CROPS:
        base = run_one(crop, weather_station(w, "OPNJ", LAT, LON), soil, evapo=evapo)
        base["crop"], base["config"], base["gcr"], base["strip"] = crop, "open", 0.0, -1
        rows.append(base)
    for cfg_name, c1 in CONFIGS.items():
        cfg = ps.make_config(cfg_name)
        for gi, gcr in enumerate(GCRS, start=1):
            geo = ps.strip_geometry(cfg, gcr)
            f = ps.daily_factors(hourly, cfg, geo)
            f.index = pd.to_datetime(f.index)
            for k in f.columns:
                light.append(dict(config=cfg_name, gcr=gcr, strip=k, cult_frac=geo["cult_frac"],
                                  annual=f[k].mean(),
                                  rabi=f[k][f.index.month.isin([11, 12, 1, 2, 3])].mean(),
                                  kharif=f[k][f.index.month.isin([6, 7, 8, 9, 10])].mean()))
                ws_df = w.copy()
                ws_df["srad_MJ"] = (w.srad_MJ.values * f[k].reindex(w.date).values).round(1)
                insi = f"{c1}{gi}{k + 1}J"
                ws = weather_station(ws_df, insi, LAT, LON)
                for crop in CROPS:
                    r = run_one(crop, ws, soil, evapo=evapo)
                    r["crop"], r["config"], r["gcr"], r["strip"] = crop, cfg_name, gcr, k
                    r["cult_frac"] = geo["cult_frac"]
                    rows.append(r)
            print(f"done {cfg_name} GCR {gcr}", flush=True)

    strips = pd.concat(rows, ignore_index=True)
    strips.to_csv(out / "pilot_strips.csv", index=False)
    pd.DataFrame(light).to_csv(out / "light_factors.csv", index=False)

    openf = strips[strips.config == "open"][["crop", "season", "hwam"]].rename(columns={"hwam": "open"})
    sh = strips[strips.config != "open"]
    field = (sh.groupby(["crop", "config", "gcr", "season"])
               .agg(strip_mean=("hwam", "mean"), cult_frac=("cult_frac", "first")).reset_index())
    field["field_yield"] = field.strip_mean * field.cult_frac
    field = field.merge(openf, on=["crop", "season"])
    field["ry"] = np.where(field.open > 0, field.field_yield / field.open, np.nan)
    field.to_csv(out / "pilot_ry.csv", index=False)

    mo = field.groupby("crop").open.transform("mean")
    field["valid"] = field.open >= 0.2 * mo
    summ = (field.groupby(["crop", "config", "gcr"])
                 .apply(lambda d: pd.Series({
                     "ry": d.field_yield.sum() / d.open.sum(),
                     "ry_sd": d.loc[d.valid, "ry"].std(),
                     "ry_p10": d.loc[d.valid, "ry"].quantile(0.10),
                     "n_valid": int(d.valid.sum()), "n": len(d)}), include_groups=False)
                 .reset_index())
    for t in THRESH:
        summ[f"pass_{int(t * 100)}"] = summ.ry >= t
    summ.to_csv(out / "pilot_summary.csv", index=False)
    openy = openf.groupby("crop").open.agg(["mean", "std", "min", "max"])
    openy.to_csv(out / "open_field_yield.csv")
    print(openy.round(0))
    print(summ.round(3).to_string())


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--soil", default="soilgrids", choices=["soilgrids", "loamy_sand"])
    ap.add_argument("--evapo", default="R", choices=["R", "F"])
    a = ap.parse_args()
    main(a.soil, a.evapo)
