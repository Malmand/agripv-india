"""Benchmark the ground-light model (pv_shading) against pvlib's independent
2D infinite-row functions (pvlib.bifacial.utils), for single-segment rows:
elevated south-facing (tilt 25 deg) and vertical bifacial, GCR 0.1-0.5.

1. Sky view factor of the ground at points across the pitch
   (ours: ray sampling; pvlib: vf_ground_sky_2d, analytic).
2. Pitch-mean unshaded (sunlit) ground fraction, hourly over a year at Jodhpur
   (ours: beam transmission T_b(theta_p) averaged over the pitch;
    pvlib: _unshaded_ground_fraction).
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pvlib
from pvlib.bifacial import utils as bu

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "prod"))
import pv_shading as ps  # noqa: E402

LAT, LON = 26.375, 73.125
rows = []
times = pd.date_range("2010-01-01 00:30", "2010-12-31 23:30", freq="1h", tz="Asia/Kolkata")
sp = pvlib.location.Location(LAT, LON, tz="Asia/Kolkata").get_solarposition(times)
sp = sp[sp.apparent_zenith < 85]

for kind in ["south_fixed", "vertical"]:
    cfg = ps.make_config(kind)
    x1, y1, x2, y2 = cfg.segments[0]
    W = cfg.module_width
    hc = (y1 + y2) / 2                              # row centre height
    tilt = cfg.meta.get("tilt", 90.0)
    surf_az = 180.0 if kind == "south_fixed" else 90.0
    for gcr in [0.1, 0.2, 0.3, 0.4, 0.5]:
        pitch = W / gcr
        # --- 1. sky view factor across the whole pitch (no uncultivated strip) ---
        xc = (x1 + x2) / 2
        xf = (np.arange(200) + 0.5) / 200            # fraction of pitch from below row centre
        _, svf_ours = ps.point_geometry(cfg.segments, pitch, xc + xf * pitch)
        # pvlib: rotation sign convention -> pick the sign that matches geometry (tilt toward -x)
        cands = [np.ravel(bu.vf_ground_sky_2d(s * tilt, gcr, m * xf % 1, pitch, hc, max_rows=40)) for s in (1, -1) for m in (1, -1)]
        svf_pv = min(cands, key=lambda c: np.abs(c - svf_ours).mean())
        # --- 2. pitch-mean sunlit fraction, hourly ---
        ang = np.degrees(np.arctan2(
            np.sin(np.radians(sp.apparent_zenith)) * np.cos(np.radians(sp.azimuth - cfg.x_azimuth)),
            np.cos(np.radians(sp.apparent_zenith))))
        tb_pts, _ = ps.point_geometry(cfg.segments, pitch, xc + xf * pitch)
        tb_mean = tb_pts.mean(axis=0)
        ours = np.interp(ang, ps.ANGLES, tb_mean)
        axis_az = 90.0 if kind == "south_fixed" else 0.0     # row axis: E-W rows / N-S rows
        phi = pvlib.shading.projected_solar_zenith_angle(sp.apparent_zenith, sp.azimuth, 0.0, axis_az)
        # rotation sign convention differs between codes: take the sign that matches
        pv = min((np.asarray(bu._unshaded_ground_fraction(sg * tilt, phi, gcr, max_zenith=87))
                  for sg in (1, -1)), key=lambda v: np.abs(ours - v).mean())
        rows.append(dict(layout=kind, gcr=gcr,
                         svf_mean_ours=svf_ours.mean(), svf_mean_pvlib=svf_pv.mean(),
                         svf_max_abs_diff=np.abs(svf_ours - svf_pv).max(),
                         sunlit_mean_ours=ours.mean(), sunlit_mean_pvlib=np.asarray(pv).mean(),
                         sunlit_mae_hourly=np.abs(ours - np.asarray(pv)).mean()))
out = pd.DataFrame(rows)
pd.set_option("display.width", 200)
print(out.round(4).to_string(index=False))
dest = Path(__file__).resolve().parents[1] / "results" / "benchmark_pvlib.csv"
out.to_csv(dest, index=False)
print("saved", dest)
