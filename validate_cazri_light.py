"""Validate the 2D light model against measured PPFD at ICAR-CAZRI Jodhpur.

Data: Santra, Meena, Yadav (2021) Biosystems Engineering 209, 74-93.
  Site 26.2577 N, 72.9929 E. Rows E-W, modules face south, tilt 26 deg,
  lowest edge 0.5 m, module 1.64 m (portrait slant length).
  Block 1: one full row,                    interspace 2.95 m
  Block 2: full bottom row + 60% top row,   interspace 5.55 m
  Block 3: two full rows + 60% top row,     interspace 8.90 m
  PPFD measured 10 cm above ground on clear days 20-24 Dec 2018 in
  09-10, 12-13 and 15-16 h windows (Table 4).

Compared quantity: PPFD relative to the unshaded interspace ("no shade"
column), for the area below the PV array and for the whole system. Ratios
cancel the radiometric-to-quantum conversion. The model uses Ineichen
clear-sky beam and diffuse with pvlib's Linke turbidity climatology.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pvlib

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
import pv_shading as ps  # noqa: E402

LAT, LON, ALT = 26.2577, 72.9929, 230.0
TILT, H0, L = 26.0, 0.5, 1.64
B = np.radians(TILT)

# measured (Santra et al. 2021, Table 4): below-PV, no-shade, whole-system PPFD
MEAS = {
    "Block 1": {"09:30": (75, 426, 217), "12:30": (135, 1164, 641), "15:30": (79, 413, 221)},
    "Block 2": {"09:30": (108, 483, 300), "12:30": (108, 1199, 693), "15:30": (130, 472, 304)},
    "Block 3": {"09:30": (96, 521, 304), "12:30": (106, 1215, 706), "15:30": (92, 440, 265)},
}
BLOCKS = {  # (list of module-row transmittances bottom->top, interspace m, measurement date)
    "Block 1": ([0.0], 2.95, "2018-12-24"),
    "Block 2": ([0.0, 0.4], 5.55, "2018-12-20"),
    "Block 3": ([0.0, 0.0, 0.4], 8.90, "2018-12-22"),
}


def geometry(taus, interspace):
    segs, x, y = [], 0.0, H0
    for tau in taus:  # +x = north; low edge at the south
        x2, y2 = x + L * np.cos(B), y + L * np.sin(B)
        segs.append((x, y, x2, y2, tau))
        x, y = x2, y2
    footprint = x
    return segs, footprint, footprint + interspace


def run(par_diffuse_boost=1.0, npts=400):
    loc = pvlib.location.Location(LAT, LON, tz="Asia/Kolkata", altitude=ALT)
    rows = []
    for blk, (taus, isp, day) in BLOCKS.items():
        segs, fp, pitch = geometry(taus, isp)
        x = (np.arange(npts) + 0.5) / npts * pitch
        tb, svf = ps.point_geometry(segs, pitch, x)
        below = x <= fp
        for hhmm, (m_below, m_open, m_total) in MEAS[blk].items():
            # hourly mean over the measurement window (10-min steps)
            times = pd.date_range(f"{day} {int(hhmm[:2]) :02d}:00", periods=7, freq="10min",
                                  tz="Asia/Kolkata")
            sp = loc.get_solarposition(times)
            cs = loc.get_clearsky(times, model="ineichen", solar_position=sp)
            z = np.radians(sp.apparent_zenith.values)
            az = np.radians(sp.azimuth.values)
            theta_p = np.degrees(np.arctan2(np.sin(z) * np.cos(az), np.cos(z)))  # +x north
            dhi = cs.dhi.values * par_diffuse_boost
            bh = cs.ghi.values - cs.dhi.values           # beam on horizontal
            g = np.array([np.interp(theta_p, ps.ANGLES, tb[i]) * bh + svf[i] * dhi
                          for i in range(npts)]).mean(axis=1)
            sunlit = (~below) & (np.array([np.interp(theta_p, ps.ANGLES, tb[i]).mean()
                                           for i in range(npts)]) > 0.99)
            ref = g[sunlit].mean()
            rows.append(dict(block=blk, time=hhmm, diffuse_frac=float((dhi / (bh + dhi)).mean()),
                             mod_below=g[below].mean() / ref, obs_below=m_below / m_open,
                             mod_total=g.mean() / ref, obs_total=m_total / m_open))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    out = []
    for boost, label in [(1.0, "broadband diffuse"), (1.4, "PAR diffuse x1.4")]:
        d = run(boost)
        d["case"] = label
        out.append(d)
    res = pd.concat(out)
    res.to_csv(ROOT / "results/validation_cazri_light.csv", index=False)
    pd.set_option("display.width", 160)
    print(res.round(3).to_string(index=False))
    for case, d in res.groupby("case"):
        for v in ["below", "total"]:
            e = d[f"mod_{v}"] - d[f"obs_{v}"]
            r = np.corrcoef(d[f"mod_{v}"], d[f"obs_{v}"])[0, 1]
            print(f"{case:18s} {v:5s} bias {e.mean():+.3f}  RMSE {np.sqrt((e**2).mean()):.3f}  r {r:.2f}")
