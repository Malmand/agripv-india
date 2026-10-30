"""Build the India 0.25 deg simulation grid from MapSPAM 2010 and the GGCMI crop calendar.

For every 0.25 deg cell (centres at .125/.375/.625/.875) inside India:
  * harvested area (ha) of wheat, pearl millet, chickpea, groundnut, total and
    irrigated share, aggregated from SPAM 5-arcmin pixels;
  * a crop is simulated in a cell when its harvested area >= MIN_HA;
  * sowing day of year (GGCMI Phase 3, 0.5 deg, irrigated and rainfed), nearest
    valid calendar pixel. Wheat uses spring wheat (swh), the GGCMI class for
    South Asian rabi wheat; chickpea uses the pulses class (pea).
Writes data/grid_india_025.csv.
"""
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parents[1]
INP = ROOT / "data" / "india_inputs"
MIN_HA = 1000.0          # about 1.3% of a 0.25 deg cell (~75,000 ha)
CROPS = {"whea": "wheat", "pmil": "pearl_millet", "chic": "chickpea", "grou": "groundnut"}
CAL = {"wheat": "swh", "pearl_millet": "mil", "chickpea": "pea", "groundnut": "nut"}

s = pd.read_csv(INP / "spam_india_harv_ha.csv")
s["clat"] = np.floor(s.lat / 0.25) * 0.25 + 0.125
s["clon"] = np.floor(s.lon / 0.25) * 0.25 + 0.125
g = s.groupby(["clat", "clon"]).sum(numeric_only=True).drop(columns=["lon", "lat"]).reset_index()

india = gpd.read_file(ROOT / "data" / "boundaries" / "Admin2.shp").to_crs(4326)
shape = india.union_all() if hasattr(india, "union_all") else india.unary_union
inside = np.array([shape.contains(Point(x, y)) for x, y in zip(g.clon, g.clat)])
g = g[inside].reset_index(drop=True)
state = gpd.sjoin(gpd.GeoDataFrame(g[["clat", "clon"]], geometry=gpd.points_from_xy(g.clon, g.clat), crs=4326),
                  india[["ST_NM", "geometry"]], how="left", predicate="within")
g["state"] = state.groupby(level=0).ST_NM.first().values

out = g[["clat", "clon", "state"]].rename(columns={"clat": "lat", "clon": "lon"})
for k, crop in CROPS.items():
    out[f"{crop}_ha"] = g[f"{k}_a"].round(0)
    out[f"{crop}_irr_share"] = (g[f"{k}_i"] / g[f"{k}_a"].where(g[f"{k}_a"] > 0)).round(3)
    out[f"sim_{crop}"] = g[f"{k}_a"] >= MIN_HA

for crop, code in CAL.items():
    for w in ("ir", "rf"):
        ds = xr.open_dataset(INP / f"{code}_{w}_ggcmi_crop_calendar_phase3_v1.01.nc", decode_times=False)
        pdoy = ds.planting_day.where(ds.planting_day > 0)
        # nearest valid pixel: fill gaps by expanding 1-2 cells
        for _ in range(3):
            pdoy = pdoy.fillna(pdoy.rolling(lat=3, lon=3, center=True, min_periods=1).median())
        v = pdoy.sel(lat=xr.DataArray(out.lat.values), lon=xr.DataArray(out.lon.values), method="nearest")
        out[f"{crop}_sow_doy_{w}"] = np.round(v.values).astype("float")

out = out[out[[f"sim_{c}" for c in CROPS.values()]].any(axis=1)].reset_index(drop=True)
out.insert(0, "cell_id", [f"I{i:05d}" for i in range(len(out))])
out.to_csv(ROOT / "data" / "grid_india_025.csv", index=False)

print(f"{inside.sum()} land cells with any SPAM area in India; {len(out)} cells simulate at least one crop")
for c in CROPS.values():
    d = out[out[f"sim_{c}"]]
    print(f"  {c:13s} cells {len(d):5d}  area {d[f'{c}_ha'].sum() / 1e6:5.2f} Mha "
          f"(of {out[f'{c}_ha'].sum() / 1e6:5.2f})  irrigated {np.average(d[f'{c}_irr_share'].fillna(0), weights=d[f'{c}_ha']):.2f}"
          f"  sowing DOY irr median {d[f'{c}_sow_doy_ir'].median():.0f}, rf {d[f'{c}_sow_doy_rf'].median():.0f}")
print("crops per cell:", out[[f"sim_{c}" for c in CROPS.values()]].sum(axis=1).value_counts().sort_index().to_dict())
