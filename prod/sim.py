"""One simulation task = one grid cell x one climate model x one period x one management.

Light cases (per task): open field; elevated south-facing and east-west rows at
GCR 0.1-0.5 with 5 strips each (yields averaged over strips, because light is
strongly non-uniform; averaging light first overstates RY by up to 0.47);
vertical bifacial at GCR 0.1-0.5 with pitch-mean light (light is near uniform;
strip vs pitch-mean RY differ by <= 0.005, tested at Jodhpur).

Management (Jodhpur-calibrated to ICRISAT DLD 1995-2014, see doc):
  farmer      wheat 60 kg N split, irrigate at 50% ASW; chickpea and groundnut
              rainfed and irrigated (20% ASW) systems, no N; pearl millet
              rainfed 10 kg N with auto-sowing in July
  recommended wheat 120 kg N split; chickpea, groundnut irrigated at 50% ASW
              with 20 kg N; pearl millet rainfed 40 kg N
CO2 (ppm, constant per period, from the weather file): historical 378,
ssp245 507, ssp585 563 (2041-2060 means, Meinshausen et al. 2020).
"""
import os
import sys
import warnings
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pv_shading as ps  # noqa: E402

CO2 = {"historical": 378.0, "ssp245": 507.0, "ssp585": 563.0}
GCRS = [0.1, 0.2, 0.3, 0.4, 0.5]
CONFIGS = ["south_fixed", "ew_fixed", "vertical"]
VARS = ["srad_MJ", "tmax_C", "tmin_C", "rain_mm", "dewp_C", "wind_ms"]

# crop, cultivar, (season start m,d), (sow m,d), ppop, row spacing, N schedule, irrig, ithrl, auto-sow window
_BASE = {
    "wheat": ("WheatV", "AW0071", (10, 15), (11, 15), 225, 22.5, None, (None, None)),
    "chickpea": ("Chickpea", "IB0004", (10, 1), (11, 1), 33, 30, None, (None, None)),
    "groundnut": ("Peanut", "IB0024", (6, 1), (6, 25), 33, 30, None, (None, None)),
    "pearl_millet": ("PearlMilletV", "IB0071", (6, 1), (7, 1), 11, 45, None, ((7, 1), (7, 31))),
}
SYSTEMS = {
    "farmer": {
        "wheat": ("wheat", [(0, 30), (30, 30)], "A", 50),
        "chickpea_rainfed": ("chickpea", [], "N", 20),
        "chickpea_irrigated": ("chickpea", [], "A", 20),
        "groundnut_rainfed": ("groundnut", [], "N", 20),
        "groundnut_irrigated": ("groundnut", [], "A", 20),
        "pearl_millet": ("pearl_millet", [(0, 10)], "N", 20),
    },
    "recommended": {
        "wheat": ("wheat", [(0, 60), (30, 60)], "A", 50),
        "chickpea_irrigated": ("chickpea", [(0, 20)], "A", 50),
        "groundnut_irrigated": ("groundnut", [(0, 20)], "A", 50),
        "pearl_millet": ("pearl_millet", [(0, 40)], "N", 20),
    },
}

_GEO = None


def geometry():
    """Strip geometry is location-independent: compute once per process."""
    global _GEO
    if _GEO is None:
        _GEO = {}
        for c in CONFIGS:
            cfg = ps.make_config(c)
            for g in GCRS:
                _GEO[(c, g)] = (cfg, ps.strip_geometry(cfg, g))
    return _GEO


def _imports():
    """Import DSSAT pieces lazily so each worker can set its own TMPDIR first."""
    from DSSATTools import DSSAT
    from DSSATTools.filex import (Field, Planting, Fertilizer, FertilizerEvent, InitialConditions,
                                  InitialConditionsLayer, SimulationControls, SCGeneral, SCOptions,
                                  SCMethods, SCManagement, SCOutputs, AMPlanting, AMIrrigation)
    import dssat_pilot as dp
    from dssat_inputs import weather_station, soil_from_soilgrids
    return locals()


FAILS = []
RETRIED = []


_BASE_WTH = {}


def make_station(L, wdf, insi, co2):
    """DSSAT weather station for one light case, built fast.

    The full .WTH text is formatted once per task (open field, via DSSATTools);
    light cases only swap the SRAD column (characters 7-13 of each data row) and
    the station code. The station object itself carries a 2-day table, which
    DSSATTools only uses to name the file. Building the full station per case
    took ~25% of the run time; the written files are identical."""
    key = (wdf.attrs["tag"], co2)
    if key not in _BASE_WTH:
        ws = L["weather_station"](wdf, "BASE", wdf.attrs["lat"], wdf.attrs["lon"])
        ws["cco2"] = co2
        _BASE_WTH.clear()
        _BASE_WTH[key] = ws._write_wth().split("\n")
    lines = _BASE_WTH[key]
    srad = np.char.mod("%6.1f", wdf.srad_MJ.values)
    out, k = [], 0
    for ln in lines:
        if ln[:1].isdigit() and len(ln) > 13:
            ln = ln[:7] + srad[k] + ln[13:]
            k += 1
        elif ln.startswith("  BASE"):
            ln = "  " + insi + ln[6:]
        out.append(ln)
    assert k == len(srad), "weather rows mismatch"
    text = "\n".join(out)
    ws = L["weather_station"](wdf.iloc[[0, -1]], insi, wdf.attrs["lat"], wdf.attrs["lon"])
    object.__setattr__(ws, "_write_wth", lambda: text)
    return ws


def run_system(L, sysdef, ws, soil, y0, nyears, co2, insi, tries=3):
    """Run with retries: rare DSSAT start-up failures (MAKEFW error 18) do not
    reproduce on re-running identical inputs."""
    for k in range(tries):
        try:
            r = _run_system(L, sysdef, ws, soil, y0, nyears)
            if k:
                RETRIED.append((insi, sysdef[0], sysdef[2], k))
            return r
        except Exception as e:
            err = e
    FAILS.append((insi, sysdef[0], sysdef[2], repr(err)[:120]))
    return pd.DataFrame({"season": [], "hwam": []})


def _run_system(L, sysdef, ws, soil, y0, nyears):
    crop, nsched, irrig, ithrl = sysdef
    clsname, cul, sd, pd_, ppop, plrs, _, auto = _BASE[crop]
    dp = L["dp"]
    cls = getattr(dp, clsname)
    rabi = crop in ("wheat", "chickpea")
    nyers = nyears - 1 if rabi else nyears
    sdate, pdate = date(y0, *sd), date(y0, *pd_)
    field = L["Field"](id_field="CELL0001", wsta=ws, id_soil=soil, flsa=0, flob=0, fldt="DR000",
                       fldd=0, flds=0)
    planting = L["Planting"](pdate=pdate, ppop=ppop, ppoe=ppop, plrs=plrs, plrd=0, pldp=5,
                             plme="S", plds="R")
    fert = (L["Fertilizer"](table=[L["FertilizerEvent"](fdate=date.fromordinal(pdate.toordinal() + d),
                                                        fmcd="FE005", facd="AP002", fdep=5, famn=a)
                                   for d, a in nsched]) if nsched else None)
    ic = L["InitialConditions"](pcr=cls.code, icdat=sdate, table=[
        L["InitialConditionsLayer"](icbl=l["slb"], sh2o=round(l["slll"] + 0.5 * (l["sdul"] - l["slll"]), 3),
                                    snh4=0.5, sno3=1.0) for l in soil.table])
    am_plant = None
    if auto[0]:
        (m1, d1), (m2, d2) = auto
        am_plant = L["AMPlanting"](pfrst=date(y0, m1, d1), plast=date(y0, m2, d2), ph2ol=40, ph2ou=100,
                                   ph2od=30, pstmx=40, pstmn=10)
    sc = L["SimulationControls"](
        general=L["SCGeneral"](sdate=sdate, nyers=nyers),
        options=L["SCOptions"](water="Y", nitro="Y", symbi="Y" if crop in ("chickpea", "groundnut") else "N",
                               co2="W"),
        methods=L["SCMethods"](evapo="F"),
        management=L["SCManagement"](plant="A" if auto[0] else "R", irrig=irrig, ferti="R" if nsched else "N",
                                     harvs="M"),
        outputs=L["SCOutputs"](grout="N", caout="N", waout="N", niout="N", miout="N", diout="N",
                               vbose="N", chout="N", opout="N"),
        planting=am_plant, irrigation=L["AMIrrigation"](imdep=30, ithrl=ithrl, ithru=100))
    dssat = L["DSSAT"]()
    try:
        kw = dict(field=field, cultivar=cls(cul), planting=planting, initial_conditions=ic,
                  simulation_controls=sc, verbose=False)
        if fert is not None:
            kw["fertilizer"] = fert
        try:
            dssat.run_treatment(**kw)
        except Exception:
            if os.environ.get("AGRIPV_KEEP_FAIL"):
                import shutil
                shutil.copytree(dssat.run_path, f"{os.environ['AGRIPV_KEEP_FAIL']}/{ws['insi']}_{crop}_{irrig}",
                                dirs_exist_ok=True)
                open(f"{os.environ['AGRIPV_KEEP_FAIL']}/{ws['insi']}_{crop}_{irrig}/stdout.txt", "w").write(
                    getattr(dssat, "stdout", ""))
            raise
        summ = dssat.output_files.get("Summary", "")
    finally:
        dssat.close()
    out = dp.parse_summary(summ)
    return out[["season", "hwam"]]


def task(npz_path, cell_index, soil_json, period, mgmt, model, out_csv):
    """Run one cell x model x period x management; write a CSV of yields."""
    import contextlib
    import io
    L = _imports()
    z = np.load(npz_path, allow_pickle=True)
    dates = pd.to_datetime(z["dates"])
    lat, lon = float(z["lat"][cell_index]), float(z["lon"][cell_index])
    cid = str(z["cell_id"][cell_index])
    wdf = pd.DataFrame(z["data"][cell_index], columns=VARS)
    wdf.insert(0, "date", dates)
    wdf.attrs.update(lat=lat, lon=lon)
    wdf.attrs["tag"] = f"{cid}|{model}|{period}"   # one base weather text per task
    soil = L["soil_from_soilgrids"](soil_json, soil_id=f"INSG{int(cid[1:]):06d}")
    y0, nyears = dates[0].year, dates[-1].year - dates[0].year + 1
    co2 = CO2[period]
    hourly = ps.hourly_from_daily(lat, lon, wdf.date, wdf.srad_MJ)
    systems = SYSTEMS[mgmt]
    rows = []

    def go(wd, insi, config, gcr, strip, cult_frac):
        with contextlib.redirect_stdout(io.StringIO()):
            ws = make_station(L, wd, insi, co2)
            for sname, sdef in systems.items():
                r = run_system(L, sdef, ws, soil, y0, nyears, co2, insi)
                for s, y in zip(r.season, r.hwam):
                    rows.append((cid, model, period, mgmt, sname, config, gcr, strip, cult_frac, int(s), y))

    go(wdf, "OPEN", "open", 0.0, -1, 1.0)
    for (config, gcr), (cfg, geo) in geometry().items():
        f = ps.daily_factors(hourly, cfg, geo)
        f.index = pd.to_datetime(f.index)
        if config == "vertical":
            cols = [("pm", f.mean(axis=1))]
        elif config == "ew_fixed":
            # E-W rows are mirror-symmetric about the row centre: strips 0/4 and 1/3
            # receive the same mean light (within 0.005 at Jodhpur), so simulate 0-2
            # and copy 0->4, 1->3 below (saves 18% of runs)
            cols = list(f.items())[:3]
        else:
            cols = list(f.items())
        for k, fk in cols:
            wd = wdf.copy()
            wd.attrs.update(wdf.attrs)
            wd["srad_MJ"] = (wdf.srad_MJ.values * fk.reindex(wdf.date).values).round(1)
            go(wd, f"{config[0].upper()}{int(gcr * 10)}{k if k != 'pm' else 'M'}X",
               config, gcr, -2 if k == "pm" else int(k), geo["cult_frac"])
    df = pd.DataFrame(rows, columns=["cell", "model", "period", "mgmt", "system", "config", "gcr",
                                     "strip", "cult_frac", "season", "hwam"])
    ew = df[(df.config == "ew_fixed") & df.strip.isin([0, 1])]
    df = pd.concat([df, ew.assign(strip=4 - ew.strip)], ignore_index=True)
    tmp = out_csv + ".part"
    df.to_csv(tmp, index=False)
    os.replace(tmp, out_csv)
    if FAILS or RETRIED:
        pd.DataFrame(FAILS + RETRIED).to_csv(out_csv + ".issues", index=False, header=False)
        FAILS.clear(); RETRIED.clear()
    return len(df)
