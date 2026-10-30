"""Week 2 pilot: open field vs shaded DSSAT runs for one cell.

For every crop, configuration, GCR and strip a weather file is written with
SRAD scaled by that strip's daily ground-light factor (pv_shading). Strip
yields are averaged and multiplied by the cultivated fraction to give the
field-level yield; relative yield (RY) = field yield / open-field yield, per
season, then summarised over seasons (mean and 10th percentile).

Management here is PROVISIONAL (standard agronomy for western Rajasthan) and
is replaced by the GGCMI Phase 3 calendar and ICRISAT-calibrated cultivars
in Week 3. Cultivars: CERES-Wheat Yecora Rojo (spring wheat placeholder),
CROPGRO-Chickpea JG 74, CERES-Millet ICMH 451, CROPGRO-Peanut TMV2.
"""
import os
import sys
import warnings
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent))
import pv_shading as ps                                   # noqa: E402
from dssat_inputs import soil_from_soilgrids, weather_station  # noqa: E402

from DSSATTools import DSSAT                              # noqa: E402
from DSSATTools.crop import Wheat, PearlMillet, DryBean, GENOTYPE_PATH, VERSION  # noqa: E402
from DSSATTools.filex import (Field, Planting, Fertilizer, FertilizerEvent,  # noqa: E402
                              InitialConditions, InitialConditionsLayer, SimulationControls,
                              SCGeneral, SCOptions, SCMethods, SCManagement, SCOutputs,
                              AMPlanting, AMIrrigation)

ROOT = Path(__file__).resolve().parents[1]


class VerbatimGenotype:
    """Write DSSAT's original .CUL/.ECO files unchanged.

    DSSATTools re-formats genotype rows and mis-pads short ecotype codes
    (e.g. 'DESI'), shifting columns. Copying the distributed files verbatim
    keeps the published cultivar coefficients exactly as released.
    """

    def _write_cul(self):
        return open(self.spe_path[:-3] + "CUL", encoding="latin-1").read()

    def _write_eco(self):
        return open(self.spe_path[:-3] + "ECO", encoding="latin-1").read()


class Chickpea(VerbatimGenotype, DryBean):
    code = "CH"
    spe_file = f"CHGRO{VERSION}.SPE"
    spe_path = os.path.join(GENOTYPE_PATH, spe_file)


class Peanut(VerbatimGenotype, DryBean):
    code = "PN"
    spe_file = f"PNGRO{VERSION}.SPE"
    spe_path = os.path.join(GENOTYPE_PATH, spe_file)


class WheatV(VerbatimGenotype, Wheat):
    pass


class PearlMilletV(VerbatimGenotype, PearlMillet):
    pass


# season start (sdate), sowing, management; years: number of seasons in 1995-2014
CROPS = {
    "wheat": dict(cls=WheatV, cul="AW0071", sdate=(10, 15), pdate=(11, 15), ppop=225, plrs=22.5,
                  n=[(0, 60), (30, 60)], irrig="A", auto_plant=None, nyers=19),
    "chickpea": dict(cls=Chickpea, cul="IB0004", sdate=(10, 1), pdate=(11, 1), ppop=33, plrs=30,
                     n=[(0, 20)], irrig="A", auto_plant=None, nyers=19),
    "pearl_millet": dict(cls=PearlMilletV, cul="IB0071", sdate=(6, 1), pdate=(7, 1), ppop=11, plrs=45,
                         n=[(0, 40)], irrig="N", auto_plant=((7, 1), (7, 31)), nyers=20),
    "groundnut": dict(cls=Peanut, cul="IB0024", sdate=(6, 1), pdate=(6, 25), ppop=33, plrs=30,
                      n=[(0, 20)], irrig="A", auto_plant=None, nyers=20),
}


def run_one(crop_key, wsta, soil, verbose=False, evapo="R"):
    c = CROPS[crop_key]
    y0 = 1995
    sdate = date(y0, *c["sdate"])
    pdate = date(y0, *c["pdate"])
    field = Field(id_field="JODH0001", wsta=wsta, id_soil=soil, flsa=0, flob=0, fldt="DR000",
                  fldd=0, flds=0)
    planting = Planting(pdate=pdate, ppop=c["ppop"], ppoe=c["ppop"], plrs=c["plrs"], plrd=0,
                        pldp=5, plme="S", plds="R")
    fert = Fertilizer(table=[FertilizerEvent(fdate=date.fromordinal(pdate.toordinal() + d),
                                             fmcd="FE005", facd="AP002", fdep=5, famn=a)
                             for d, a in c["n"]])
    # initial soil water: half of plant-available water, low mineral N
    ic = InitialConditions(pcr=c["cls"].code, icdat=sdate, table=[
        InitialConditionsLayer(icbl=l["slb"], sh2o=round(l["slll"] + 0.5 * (l["sdul"] - l["slll"]), 3),
                               snh4=0.5, sno3=1.0) for l in soil.table])
    plant_mode = "A" if c["auto_plant"] else "R"
    am_plant = None
    if c["auto_plant"]:
        (m1, d1), (m2, d2) = c["auto_plant"]
        am_plant = AMPlanting(pfrst=date(y0, m1, d1), plast=date(y0, m2, d2), ph2ol=40, ph2ou=100,
                              ph2od=30, pstmx=40, pstmn=10)
    sc = SimulationControls(
        general=SCGeneral(sdate=sdate, nyers=c["nyers"]),
        options=SCOptions(water="Y", nitro="Y", symbi="Y" if c["cls"] in (Chickpea, Peanut) else "N", co2="M"),
        methods=SCMethods(evapo=evapo),
        management=SCManagement(plant=plant_mode, irrig=c["irrig"], ferti="R", harvs="M"),
        outputs=SCOutputs(grout="N", caout="N", waout="N", niout="N", miout="N", diout="N",
                          vbose="N", chout="N", opout="N"),
        planting=am_plant, irrigation=AMIrrigation(imdep=30, ithrl=50, ithru=100))
    crop = c["cls"](c["cul"])
    dssat = DSSAT()
    try:
        dssat.run_treatment(field=field, cultivar=crop, planting=planting, fertilizer=fert,
                            initial_conditions=ic, simulation_controls=sc, verbose=verbose)
        summ = dssat.output_files.get("Summary", "")
    finally:
        dssat.close()
    return parse_summary(summ)


def parse_summary(text):
    lines = text.splitlines()
    hdr = next(i for i, l in enumerate(lines) if l.startswith("@"))
    cols = lines[hdr][1:].split()
    rows = []
    for l in lines[hdr + 1:]:
        if not l.strip():
            continue
        parts = l.split()
        rows.append(parts[:len(cols)])
    df = pd.DataFrame(rows, columns=cols[:len(rows[0])])
    out = pd.DataFrame({"season": pd.to_numeric(df["SDAT"]) // 1000,
                        "pdat": pd.to_numeric(df["PDAT"], errors="coerce"),
                        "hwam": pd.to_numeric(df["HWAM"], errors="coerce").clip(lower=0),
                        "irri": pd.to_numeric(df.get("IRCM", 0), errors="coerce")})
    return out
