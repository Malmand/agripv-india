"""Adds the kharif crops that follow wheat and chickpea to the India grid (same cells and cell_id).
MapSPAM 2010 harvested area (ha) of rice, maize, soybean, cotton, sorghum, pigeonpea, sugarcane (all seasons),
aggregated from 5-arcmin pixels to the 0.25 deg cells as in build_india_grid.py; rice irrigated share;
rice sowing (transplanting) day from the GGCMI Phase 3 rice calendar (ri1, main season), nearest valid pixel.
sim_rice: rice >= MIN_HA in a cell where wheat or chickpea is simulated (rice after a rabi crop).
Writes data/grid_india_025_kharif.csv (all columns of grid_india_025.csv plus the new ones).
"""
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
INP = ROOT / "data" / "kharif_inputs"
MIN_HA = 1000.0
g = pd.read_csv(ROOT / "data" / "grid_india_025.csv")
s = pd.read_csv(INP / "spam_india_kharif_harv_ha.csv")
s["lat"] = np.floor(s.lat / 0.25) * 0.25 + 0.125
s["lon"] = np.floor(s.lon / 0.25) * 0.25 + 0.125
a = s.groupby(["lat", "lon"]).sum(numeric_only=True).reset_index()
g = g.merge(a, on=["lat", "lon"], how="left")
names = {"rice": "rice", "maiz": "maize", "soyb": "soybean", "cott": "cotton", "sorg": "sorghum", "pige": "pigeonpea",
         "sugc": "sugarcane"}
for k, n in names.items():
    g[f"{n}_ha"] = g[f"{k}_a"].fillna(0).round(0)
g["rice_irr_share"] = (g.rice_i / g.rice_a.where(g.rice_a > 0)).round(3)
g["sim_rice"] = (g.rice_ha >= MIN_HA) & (g.sim_wheat | g.sim_chickpea)
for w in ("ir", "rf"):
    ds = xr.open_dataset(INP / f"ri1_{w}_ggcmi_crop_calendar_phase3_v1.01.nc", decode_times=False)
    p = ds.planting_day.where(ds.planting_day > 0)
    for _ in range(3):
        p = p.fillna(p.rolling(lat=3, lon=3, center=True, min_periods=1).median())
    v = p.sel(lat=xr.DataArray(g.lat.values), lon=xr.DataArray(g.lon.values), method="nearest")
    g[f"rice_sow_doy_{w}"] = np.round(v.values).astype(float)
g = g.drop(columns=[c for c in g.columns if c[:5] in {f"{k}_" for k in names} and c[-2:] in ("_a", "_i", "_r")])
g.to_csv(ROOT / "data" / "grid_india_025_kharif.csv", index=False)
d = g[g.sim_rice]
print(f"rice cells {len(d)} (with wheat/chickpea), rice area there {d.rice_ha.sum()/1e6:.2f} Mha of {g.rice_ha.sum()/1e6:.2f} in grid; "
      f"irrigated share {np.average(d.rice_irr_share.fillna(0), weights=d.rice_ha):.2f}; "
      f"transplant DOY ir median {d.rice_sow_doy_ir.median():.0f} (p10 {d.rice_sow_doy_ir.quantile(.1):.0f}, p90 {d.rice_sow_doy_ir.quantile(.9):.0f}), rf {d.rice_sow_doy_rf.median():.0f}")
