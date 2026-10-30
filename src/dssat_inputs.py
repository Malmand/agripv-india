"""DSSAT inputs: soil from SoilGrids via Saxton and Rawls (2006), weather stations, crops.

Soil hydraulic limits follow Saxton, K.E., Rawls, W.J. (2006) Soil water
characteristic estimates by texture and organic matter for hydrologic
solutions. Soil Sci. Soc. Am. J. 70, 1569-1578. This is the same
SoilGrids-plus-pedotransfer route used to build the Han et al. (2019) 10 km
DSSAT soil set, so the pilot soil can be swapped for that set without
changing the method.
"""
import json
from datetime import date

import numpy as np
import pandas as pd
from DSSATTools.soil import SoilProfile, SoilLayer
from DSSATTools.weather import WeatherStation


def saxton_rawls(sand, clay, om):
    """sand, clay as fractions; om in %. Returns LL (1500 kPa), DUL (33 kPa), SAT, Ksat (cm/h)."""
    S, C, OM = sand, clay, om
    t1500t = -0.024*S + 0.487*C + 0.006*OM + 0.005*S*OM - 0.013*C*OM + 0.068*S*C + 0.031
    t1500 = t1500t + (0.14*t1500t - 0.02)
    t33t = -0.251*S + 0.195*C + 0.011*OM + 0.006*S*OM - 0.027*C*OM + 0.452*S*C + 0.299
    t33 = t33t + (1.283*t33t**2 - 0.374*t33t - 0.015)
    ts33t = 0.278*S + 0.034*C + 0.022*OM - 0.018*S*OM - 0.027*C*OM - 0.584*S*C + 0.078
    ts33 = ts33t + (0.636*ts33t - 0.107)
    ts = t33 + ts33 - 0.097*S + 0.043
    B = (np.log(1500) - np.log(33)) / (np.log(t33) - np.log(t1500))
    lam = 1.0 / B
    ks_mm_h = 1930.0 * (ts - t33) ** (3 - lam)
    return t1500, t33, ts, ks_mm_h / 10.0


def soil_from_soilgrids(path, soil_id="INSG000214"):
    d = json.load(open(path))
    layers = []
    for i, (top, bot) in enumerate(d["depths_cm"]):
        sand, clay = d["sand_pct"][i] / 100, d["clay_pct"][i] / 100
        oc = d["soc_g_kg"][i] / 10.0               # % organic carbon
        ll, dul, sat, ks = saxton_rawls(sand, clay, 1.72 * oc)
        mid = (top + bot) / 2
        srgf = 1.0 if mid <= 15 else float(np.exp(-0.02 * mid))  # DSSAT default rule
        layers.append(SoilLayer(
            slb=bot, slll=round(ll, 3), sdul=round(dul, 3), ssat=round(sat, 3),
            srgf=round(srgf, 3), ssks=round(ks, 2), sbdm=d["bdod_kg_dm3"][i],
            sloc=round(oc, 2), slcl=d["clay_pct"][i], slsi=d["silt_pct"][i],
            slhw=d["ph_h2o"][i], scec=d["cec_cmol_kg"][i]))
    return SoilProfile(
        table=layers, name=soil_id, soil_data_source="SoilGrids2",
        soil_clasification="SCL", soil_series_name="SG2+SaxtonRawls2006",
        site="Jodhpur", country="IN", lat=d["lat"], long=d["lon"],
        salb=0.13, slu1=6.0, sldr=0.4, slro=75.0, slnf=1.0, slpf=1.0)


def weather_station(df, insi, lat, lon, elev=258.0):
    """df: date, srad_MJ, tmax_C, tmin_C, rain_mm (daily)."""
    t = pd.DataFrame({"date": pd.to_datetime(df["date"]).dt.date, "srad": df["srad_MJ"].round(1),
                      "tmax": df["tmax_C"], "tmin": df["tmin_C"], "rain": df["rain_mm"]})
    if "dewp_C" in df:                      # needed for FAO-56 Penman-Monteith
        t["dewp"] = df["dewp_C"].values
    if "wind_ms" in df:                     # DSSAT wants km/day
        t["wind"] = (df["wind_ms"] * 86.4).round(1).values
    tm = (df["tmax_C"] + df["tmin_C"]) / 2
    mon = tm.groupby(pd.to_datetime(df["date"]).dt.month).mean()
    return WeatherStation(table=t, lat=lat, long=lon, insi=insi, elev=elev,
                          tav=round(float(tm.mean()), 1), amp=round(float(mon.max() - mon.min()), 1),
                          refht=2.0, wndht=2.0)


def loamy_sand_profile(soil_id="INLS000214", lat=26.375, lon=73.125):
    """CAZRI farm soil is loamy sand (Poonia et al., 2022). Texture-class centroid
    (USDA loamy sand: ~82% sand, ~6% clay) with low arid-zone organic carbon,
    converted with Saxton and Rawls (2006). Used for site validation and as a
    soil-texture sensitivity case; not a measured profile."""
    depths = [5, 15, 30, 60, 100, 200]
    oc = [0.30, 0.25, 0.20, 0.15, 0.12, 0.10]
    layers = []
    for bot, c in zip(depths, oc):
        ll, dul, sat, ks = saxton_rawls(0.82, 0.06, 1.72 * c)
        top = [0] + depths
        mid = (top[depths.index(bot)] + bot) / 2
        srgf = 1.0 if mid <= 15 else float(np.exp(-0.02 * mid))
        layers.append(SoilLayer(slb=bot, slll=round(ll, 3), sdul=round(dul, 3), ssat=round(sat, 3),
                                srgf=round(srgf, 3), ssks=round(ks, 2), sbdm=1.55, sloc=c,
                                slcl=6.0, slsi=12.0, slhw=8.2, scec=6.0))
    return SoilProfile(table=layers, name=soil_id, soil_data_source="TexCentroid",
                       soil_clasification="LS", soil_series_name="LS centroid+SaxtonRawls2006",
                       site="Jodhpur", country="IN", lat=lat, long=lon,
                       salb=0.17, slu1=4.0, sldr=0.6, slro=65.0, slnf=1.0, slpf=1.0)
