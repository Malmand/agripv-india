"""India run: one task = one grid cell x one climate model x one period x one management.

Differences from the Rajasthan run (sim.py), decided after the Rajasthan results:
  * crops and water regimes per cell from MapSPAM 2010: a crop is simulated only
    where it is grown (>= 1000 ha per cell); irrigated and rainfed variants are
    simulated where each makes up >= 10% of that crop's area (else the dominant one);
  * sowing per cell from the GGCMI Phase 3 crop calendar (wheat: swh; pearl
    millet: mil; groundnut: nut; chickpea: local wheat date - 14 days, because the
    GGCMI pulses class is a kharif calendar). Rainfed kharif crops use automatic
    sowing in a +-15 day window around the calendar date (monsoon onset);
  * GCR set per crop: 0.1-0.5 for all, plus 0.05 for chickpea and groundnut, plus
    0.6 and 0.7 for wheat and pearl millet (their RY stays >= 0.8 at 0.5 in Rajasthan);
  * management "recommended" is the main case (adequate N; shading effects on
    N-starved wheat and millet are masked by N dilution), "farmer" a sensitivity.
Light: south-facing 5 strips, E-W 3 strips mirrored to 5, vertical pitch-mean.
CO2 per period from the weather file (historical 378, ssp245 507, ssp585 563 ppm).
"""
import os
import sys
import warnings
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pv_shading as ps  # noqa: E402
import sim  # noqa: E402  (make_station, _imports, geometry helpers, retry wrapper)

CO2 = sim.CO2
CONFIGS = ["south_fixed", "ew_fixed", "vertical"]
BASE_GCR = [0.1, 0.2, 0.3, 0.4, 0.5]
EXTRA_GCR = {"wheat": [0.6, 0.7], "pearl_millet": [0.6, 0.7], "chickpea": [0.05], "groundnut": [0.05]}
MIN_SHARE = 0.10

# crop -> (DSSAT class, cultivar, plants m-2, row spacing cm)
CULT = {"wheat": ("WheatV", "AW0071", 225, 22.5), "chickpea": ("Chickpea", "IB0004", 33, 30),
        "groundnut": ("Peanut", "IB0024", 33, 30), "pearl_millet": ("PearlMilletV", "IB0071", 11, 45)}
# (crop, water) -> management: N schedule [(days after sowing, kg N/ha)], irrigation threshold (% ASW)
MGMT = {
    "recommended": {("wheat", "ir"): ([(0, 60), (30, 60)], 50), ("wheat", "rf"): ([(0, 60)], None),
                    ("chickpea", "ir"): ([(0, 20)], 50), ("chickpea", "rf"): ([(0, 20)], None),
                    ("groundnut", "ir"): ([(0, 20)], 50), ("groundnut", "rf"): ([(0, 20)], None),
                    ("pearl_millet", "ir"): ([(0, 40)], 50), ("pearl_millet", "rf"): ([(0, 40)], None)},
    "farmer": {("wheat", "ir"): ([(0, 30), (30, 30)], 50), ("wheat", "rf"): ([(0, 30)], None),
               ("chickpea", "ir"): ([], 20), ("chickpea", "rf"): ([], None),
               ("groundnut", "ir"): ([], 20), ("groundnut", "rf"): ([], None),
               ("pearl_millet", "ir"): ([(0, 10)], 20), ("pearl_millet", "rf"): ([(0, 10)], None)},
}
_GEO = {}
CROPS_ONLY = None            # e.g. {"wheat", "pearl_millet"} for the N calibration sweep
_CALIB = None


def calib_table():
    """State nitrogen rates for the 'current' scenario (from the N calibration sweep)."""
    global _CALIB
    if _CALIB is None:
        p = HERE / "calib_n.csv"
        _CALIB = pd.read_csv(p).set_index(["state", "crop"]).n.to_dict() if p.exists() else {}
    return _CALIB


def mgmt_for(mgmt, crop, water, state):
    """(N schedule, irrigation threshold) for one system.
    'farmer' / 'recommended': fixed national rules (MGMT).
    'nXXX': calibration sweep, XXX kg N/ha for wheat and pearl millet (legumes as farmer).
    'current': state-calibrated N for wheat and pearl millet (legumes as farmer)."""
    if mgmt in MGMT:
        return MGMT[mgmt][(crop, water)]
    if crop in ("chickpea", "groundnut"):
        return MGMT["farmer"][(crop, water)]
    if mgmt.startswith("n") and mgmt[1:].isdigit():
        n = float(mgmt[1:])
    elif mgmt == "current":
        n = calib_table().get((state, crop), calib_table().get(("ALL", crop), 60.0))
    else:
        raise ValueError(mgmt)
    ithrl = 50 if water == "ir" else None
    if crop == "wheat" and water == "ir":
        return [(0, n / 2), (30, n / 2)], ithrl
    return [(0, n)], ithrl


def geometry(config, gcr):
    if (config, gcr) not in _GEO:
        cfg = ps.make_config(config)
        _GEO[(config, gcr)] = (cfg, ps.strip_geometry(cfg, gcr))
    return _GEO[(config, gcr)]


def systems_for(cell):
    """List of (crop, water, sow_doy) simulated in this cell."""
    out = []
    for crop in CULT:
        if CROPS_ONLY and crop not in CROPS_ONLY:
            continue
        if not bool(cell[f"sim_{crop}"]):
            continue
        irr = float(cell[f"{crop}_irr_share"]) if pd.notna(cell[f"{crop}_irr_share"]) else 0.0
        waters = [w for w, sh in (("ir", irr), ("rf", 1 - irr)) if sh >= MIN_SHARE]
        if not waters:
            waters = ["ir" if irr >= 0.5 else "rf"]
        for w in waters:
            if crop == "chickpea":
                doy = float(cell["wheat_sow_doy_ir"]) - 14
            elif crop == "groundnut" and w == "rf":
                # GGCMI rainfed groundnut for India is a generic gap-fill (1 Jun or 1 Oct);
                # kharif groundnut is sown at monsoon onset, like rainfed pearl millet
                doy = float(cell["pearl_millet_sow_doy_rf"])
            else:
                doy = float(cell[f"{crop}_sow_doy_{w}"])
            out.append((crop, w, int(round(doy)) if np.isfinite(doy) else None))
    return [s for s in out if s[2] is not None]


def _dates(y0, doy, rabi):
    """Sowing date in the first simulated season; rabi crops sown Jan-May go to year y0+1."""
    yr = y0 + 1 if (rabi and doy < 152) else y0
    sow = date(yr, 1, 1) + timedelta(days=int(doy) - 1)
    return sow, sow - timedelta(days=30)


def run_one(L, crop, water, doy, mg, ws, soil, y0, nyears):
    clsname, cul, ppop, plrs = CULT[crop]
    dp = L["dp"]
    cls = getattr(dp, clsname)
    rabi = crop in ("wheat", "chickpea") or (crop == "groundnut" and (doy < 152 or doy > 273))
    pdate, sdate = _dates(y0, doy, rabi)
    last_wth_year = y0 + nyears - 1
    # seasons whose harvest must fit inside the weather record
    nyers = (last_wth_year - sdate.year) if rabi else (last_wth_year - sdate.year + 1)
    nsched, ithrl = mg
    auto = (water == "rf" and crop in ("pearl_millet", "groundnut") and not rabi)
    field = L["Field"](id_field="CELL0001", wsta=ws, id_soil=soil, flsa=0, flob=0, fldt="DR000",
                       fldd=0, flds=0)
    planting = L["Planting"](pdate=pdate, ppop=ppop, ppoe=ppop, plrs=plrs, plrd=0, pldp=5,
                             plme="S", plds="R")
    fert = (L["Fertilizer"](table=[L["FertilizerEvent"](fdate=pdate + timedelta(days=d), fmcd="FE005",
                                                        facd="AP002", fdep=5, famn=a) for d, a in nsched])
            if nsched else None)
    ic = L["InitialConditions"](pcr=cls.code, icdat=sdate, table=[
        L["InitialConditionsLayer"](icbl=l["slb"], sh2o=round(l["slll"] + 0.5 * (l["sdul"] - l["slll"]), 3),
                                    snh4=0.5, sno3=1.0) for l in soil.table])
    am_plant = (L["AMPlanting"](pfrst=pdate - timedelta(days=15), plast=pdate + timedelta(days=15),
                                ph2ol=40, ph2ou=100, ph2od=30, pstmx=40, pstmn=10) if auto else None)
    sc = L["SimulationControls"](
        general=L["SCGeneral"](sdate=sdate, nyers=nyers),
        options=L["SCOptions"](water="Y", nitro="Y", symbi="Y" if crop in ("chickpea", "groundnut") else "N",
                               co2="W"),
        methods=L["SCMethods"](evapo="F"),
        management=L["SCManagement"](plant="A" if auto else "R", irrig="A" if ithrl else "N",
                                     ferti="R" if nsched else "N", harvs="M"),
        outputs=L["SCOutputs"](grout="N", caout="N", waout="N", niout="N", miout="N", diout="N",
                               vbose="N", chout="N", opout="N"),
        planting=am_plant, irrigation=L["AMIrrigation"](imdep=30, ithrl=ithrl or 50, ithru=100))
    dssat = L["DSSAT"]()
    try:
        kw = dict(field=field, cultivar=cls(cul), planting=planting, initial_conditions=ic,
                  simulation_controls=sc, verbose=False)
        if fert is not None:
            kw["fertilizer"] = fert
        dssat.run_treatment(**kw)
        summ = dssat.output_files.get("Summary", "")
    finally:
        dssat.close()
    return dp.parse_summary(summ)[["season", "hwam", "irri"]]


def run_retry(L, *a, tries=3):
    for k in range(tries):
        try:
            return run_one(L, *a), k
        except Exception as e:
            err = e
    sim.FAILS.append((a[0], a[1], repr(err)[:120]))
    return pd.DataFrame({"season": [], "hwam": [], "irri": []}), tries


def task(npy_path, meta, cell, soil_json, period, mgmt, model, out_csv):
    """One cell x model x period x management. npy_path: memory-mapped [cell, day, var]."""
    import contextlib
    import io
    L = sim._imports()
    data = np.load(npy_path, mmap_mode="r")
    i = int(cell["row"])
    dates = pd.to_datetime(meta["dates"])
    lat, lon, cid = float(cell["lat"]), float(cell["lon"]), str(cell["cell_id"])
    wdf = pd.DataFrame(np.asarray(data[i]), columns=sim.VARS)
    wdf.insert(0, "date", dates)
    wdf.attrs.update(lat=lat, lon=lon, tag=f"{cid}|{model}|{period}")
    soil = L["soil_from_soilgrids"](soil_json, soil_id=f"IN{int(cid[1:]):08d}")
    y0, nyears = dates[0].year, dates[-1].year - dates[0].year + 1
    co2 = CO2[period]
    kf = os.environ.get("AGRIPV_SRAD_FACTORS")   # radiation bias test (radiation_ref.py); unset in production
    if kf:
        f = pd.read_csv(kf)
        k = f[f.cell == cid].sort_values("month").k.values
        if len(k) == 12:
            wdf["srad_MJ"] = (wdf.srad_MJ.values * k[wdf.date.dt.month.values - 1]).round(2)
    hourly = ps.hourly_from_daily(lat, lon, wdf.date, wdf.srad_MJ)
    systems = systems_for(cell)
    rows, retried = [], 0

    def go(wd, insi, config, gcr, strip, cult_frac, need):
        nonlocal retried
        with contextlib.redirect_stdout(io.StringIO()):
            ws = sim.make_station(L, wd, insi, co2)
            for crop, water, doy in need:
                mg = mgmt_for(mgmt, crop, water, cell.get("state"))
                r, k = run_retry(L, crop, water, doy, mg, ws, soil, y0, nyears)
                retried += k
                for s, y, irri in zip(r.season, r.hwam, r.irri):
                    rows.append((cid, model, period, mgmt, crop, water, config, gcr, strip, cult_frac,
                                 int(s), y, irri))

    go(wdf, "OPEN", "open", 0.0, -1, 1.0, systems)
    gcrs = sorted(set(BASE_GCR) | {g for c, _, _ in systems for g in EXTRA_GCR.get(c, [])})
    for config in CONFIGS:
        for gcr in gcrs:
            need = [s for s in systems if gcr in BASE_GCR or gcr in EXTRA_GCR.get(s[0], [])]
            cfg, geo = geometry(config, gcr)
            f = ps.daily_factors(hourly, cfg, geo)
            f.index = pd.to_datetime(f.index)
            if config == "vertical":
                cols = [("pm", f.mean(axis=1))]
            elif config == "ew_fixed":
                cols = list(f.items())[:3]          # mirror symmetry: strips 0/4 and 1/3
            else:
                cols = list(f.items())
            for k, fk in cols:
                wd = wdf.copy()
                wd.attrs.update(wdf.attrs)
                wd["srad_MJ"] = (wdf.srad_MJ.values * fk.reindex(wdf.date).values).round(1)
                tag = f"{config[0].upper()}{int(round(gcr * 100)):02d}{'M' if k == 'pm' else k}"
                go(wd, tag[:4], config, gcr, -2 if k == "pm" else int(k), geo["cult_frac"], need)
    df = pd.DataFrame(rows, columns=["cell", "model", "period", "mgmt", "crop", "water", "config", "gcr",
                                     "strip", "cult_frac", "season", "hwam", "irri"])
    ew = df[(df.config == "ew_fixed") & df.strip.isin([0, 1])]
    df = pd.concat([df, ew.assign(strip=4 - ew.strip)], ignore_index=True)
    tmp = out_csv + ".part"
    df.to_csv(tmp, index=False, float_format="%.6g")
    os.replace(tmp, out_csv)
    if sim.FAILS or retried:
        pd.DataFrame(sim.FAILS + [("retries", retried, "")]).to_csv(out_csv + ".issues", index=False, header=False)
        sim.FAILS.clear()
    return len(df)
