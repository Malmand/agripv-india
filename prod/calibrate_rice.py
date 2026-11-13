"""Rice nitrogen calibration on the VM (mode rice), as calibrate_n.py for wheat and pearl millet: per state, the N
level whose simulated open-field state yield (2-GCM mean, MapSPAM area and irrigation-share weighted) is closest to the
ICRISAT 1995-2014 state mean (rice_obs_state.csv, milled rice x 1.5 = paddy). States with < 20 kha of rice and states
without observations get the area-weighted median choice ('ALL'). Appends rice rows to calib_n.csv (read by
sim_india 'current') and writes calib_rice_state_yields.csv.
Usage: python calibrate_rice.py --summary /data/out/summary --grid grid_india_025_kharif.csv --app /opt/agripv
"""
import argparse, glob, os
import numpy as np
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--summary", required=True); ap.add_argument("--grid", required=True); ap.add_argument("--app", required=True)
a = ap.parse_args()
g = pd.read_csv(a.grid)
GCMS = ["GFDL-ESM4", "MPI-ESM1-2-HR"]


def state_yield(t):
    t = t[t.model.isin(GCMS) & (t.crop == "rice")]
    m = t.groupby(["cell", "water"]).open_mean.mean().reset_index()
    m = m.merge(g[["cell_id", "state", "rice_irr_share", "rice_ha"]].rename(columns={"cell_id": "cell"}), on="cell")
    irr = m.rice_irr_share.fillna(0)
    m["w"] = np.where(m.water == "ir", irr, 1 - irr)
    m["w"] = m.w / m.groupby("cell").w.transform("sum")
    c = m.assign(y=m.w * m.open_mean).groupby(["cell", "state", "rice_ha"]).y.sum().reset_index()
    return c.groupby("state").apply(lambda d: np.average(d.y, weights=d.rice_ha), include_groups=False).rename("sim").reset_index()


obs = pd.read_csv(os.path.join(a.app, "rice_obs_state.csv"))
lv = []
for f in sorted(glob.glob(os.path.join(a.summary, "ry_system_historical_n*_open.csv.gz"))):
    n = int(os.path.basename(f).split("_n")[1].split("_")[0])
    lv.append(state_yield(pd.read_csv(f)).assign(n=n))
lv = pd.concat(lv).merge(obs, on="state")
lv["err"] = (lv.sim / lv.obs - 1).abs()
best = lv.loc[lv.groupby("state").err.idxmin()]
best = best[best.obs_area >= 20]
d = best.sort_values("n"); cum = d.obs_area.cumsum().values
fb = int(d.n.values[np.searchsorted(cum, cum[-1] / 2)])
rows = pd.concat([best[["state", "n"]], pd.DataFrame({"state": ["ALL"], "n": [fb]})]).assign(crop="rice")[["state", "crop", "n"]]
cf = os.path.join(a.app, "calib_n.csv")
old = pd.read_csv(cf)
pd.concat([old[old.crop != "rice"], rows]).to_csv(cf, index=False)
lv.to_csv(os.path.join(a.summary, "calib_rice_state_yields.csv"), index=False)
print(best[["state", "n", "sim", "obs", "obs_area"]].round(0).to_string(index=False))
print("fallback (ALL):", fb)
