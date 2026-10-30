"""Ground irradiance under agrivoltaic arrays (2D infinite-row view-factor model).

Each configuration is reduced to its cross-section perpendicular to the rows.
Rows repeat every pitch P = (module width) / GCR. For points across the
cultivated part of one pitch we compute
  * the beam-transmission fraction as a function of the projected solar
    zenith angle (beam reaches the point only if the ray to the sun misses
    every module segment), and
  * the isotropic sky view factor (2D: dF = 0.5 cos(phi) dphi over unblocked
    directions).
Hourly GHI is reconstructed from the daily total by scaling a clear-sky
profile (Ineichen, pvlib) and split into beam and diffuse with Erbs. The daily
shading factor of each strip is

  f_d = sum_h [ T_b(theta_p) * DNI * cos(z) + SVF * DHI ] / sum_h GHI

and the shaded DSSAT SRAD is f_d * SRAD. Ground-reflected light, light
through module gaps and circumsolar diffuse are ignored (stated assumptions;
all slightly underestimate under-panel light).
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import pvlib

ANGLES = np.arange(-89.75, 90.0, 0.5)  # projected zenith grid (deg)


@dataclass
class Config:
    name: str
    x_azimuth: float              # azimuth (deg) of the +x axis of the cross-section
    segments: list                # module segments in one row [(x1,y1,x2,y2), ...] (m)
    module_width: float           # module width used in GCR (m, sum of segment lengths)
    uncultivated: float = 0.0     # strip width per row not cropped (m)
    meta: dict = field(default_factory=dict)


def make_config(kind: str, tilt=None) -> Config:
    """Configurations fixed in Week 1 (geometry values documented in the doc)."""
    if kind == "south_fixed":     # elevated, E-W rows, modules face south
        tilt = 25.0 if tilt is None else tilt   # ~ latitude of Jodhpur (26.3 N)
        W, H = 2.0, 3.0           # 2 m slant width, 3 m lowest-edge clearance
        b = np.radians(tilt)
        seg = [(0.0, H, W * np.cos(b), H + W * np.sin(b))]  # +x = north, low edge south
        return Config(kind, 0.0, seg, W, 0.0, dict(tilt=tilt, clearance=H))
    if kind == "ew_fixed":        # elevated, N-S rows, east and west faces (ridge)
        tilt = 10.0 if tilt is None else tilt
        W, H = 2.0, 3.0
        b = np.radians(tilt)
        dx, dy = W * np.cos(b), W * np.sin(b)
        seg = [(0.0, H, dx, H + dy), (dx, H + dy, 2 * dx, H)]  # +x = east
        return Config(kind, 90.0, seg, 2 * W, 0.0, dict(tilt=tilt, clearance=H))
    if kind == "vertical":        # vertical bifacial, N-S rows, faces east and west
        h0, L = 0.8, 2.0          # DIN SPEC 91434 Category 2, 0.8 m bottom edge
        seg = [(0.0, h0, 0.0, h0 + L)]
        return Config(kind, 90.0, seg, L, 0.5, dict(bottom=h0, height=L))
    raise ValueError(kind)


def _ray_trans(x0, ang_deg, segs, pitch, nrow=40):
    """Transmission (0-1) of the ray from ground point(s) x0 at projected angle ang.

    A segment is (x1, y1, x2, y2) or (x1, y1, x2, y2, tau); tau is the fraction of
    light passing a partly filled row (e.g. 0.4 for 60% module density), 0 if opaque.
    """
    t = np.tan(np.radians(ang_deg))
    x0 = np.atleast_1d(x0)[:, None]
    trans = np.ones(x0.shape[0])
    ks = np.arange(-nrow, nrow + 1) * pitch
    for seg in segs:
        x1, y1, x2, y2 = seg[:4]
        tau = seg[4] if len(seg) > 4 else 0.0
        # ray: x = x0 + y t ; segment: (x1 + s(x2-x1) + k, y1 + s(y2-y1)), s in [0,1]
        dx, dy = x2 - x1, y2 - y1
        den = dx - dy * t
        if abs(den) < 1e-12:
            continue
        s_ = (x0 + y1 * t - x1 - ks[None, :]) / den
        y = y1 + s_ * dy
        nhit = ((s_ >= 0) & (s_ <= 1) & (y > 0)).sum(axis=1)
        trans *= tau ** nhit
    return trans


def _ray_blocked(x0, ang_deg, segs, pitch, nrow=40):
    """Kept for compatibility: True where transmission is below 0.5."""
    return _ray_trans(x0, ang_deg, segs, pitch, nrow) < 0.5


def point_geometry(segments, pitch, x):
    """Per-point beam transmission T_b(theta_p) [npts x nangle] and isotropic SVF [npts]."""
    tb = np.array([_ray_trans(x, a, segments, pitch) for a in ANGLES]).T
    phis = np.arange(-89.5, 90.0, 1.0)
    w = 0.5 * np.cos(np.radians(phis)) * np.radians(1.0)
    vis = np.array([_ray_trans(x, p, segments, pitch) for p in phis]).T
    svf = (vis * w).sum(axis=1) / w.sum()           # normalised so open ground = 1
    return tb, svf


def strip_geometry(cfg: Config, gcr: float, nstrip=5, npts=200):
    """Beam transmission T_b(theta_p) [nstrip x nangle] and SVF [nstrip] per strip."""
    pitch = cfg.module_width / gcr
    # cultivated span: whole pitch minus an uncultivated strip centred on the row footprint
    xs_row = np.mean([g[0] for g in cfg.segments] + [g[2] for g in cfg.segments])
    half = cfg.uncultivated / 2
    x = xs_row + half + (np.arange(npts) + 0.5) / npts * (pitch - cfg.uncultivated)
    tb, svf = point_geometry(cfg.segments, pitch, x)
    idx = np.array_split(np.arange(npts), nstrip)
    tb_s = np.array([tb[i].mean(axis=0) for i in idx])
    svf_s = np.array([svf[i].mean() for i in idx])
    cult_frac = (pitch - cfg.uncultivated) / pitch
    return dict(pitch=pitch, tb=tb_s, svf=svf_s, cult_frac=cult_frac)


def hourly_from_daily(lat, lon, dates, srad_mj, alt=250.0):
    """Hourly GHI/DNI/DHI (W/m2) consistent with daily SRAD (MJ/m2/d), local solar days."""
    times = pd.date_range(dates.min(), dates.max() + pd.Timedelta(hours=23),
                          freq="1h", tz="Asia/Kolkata") + pd.Timedelta(minutes=30)
    loc = pvlib.location.Location(lat, lon, tz="Asia/Kolkata", altitude=alt)
    sp = loc.get_solarposition(times)
    cs = loc.get_clearsky(times, model="ineichen", solar_position=sp)["ghi"]
    day = times.tz_localize(None).normalize()
    cs_day = cs.groupby(day).transform("sum") * 3600 / 1e6        # MJ/m2/d
    target = pd.Series(np.asarray(srad_mj), index=pd.DatetimeIndex(dates)).reindex(day).values
    ghi = (cs * np.where(cs_day > 0, target / cs_day, 0)).clip(lower=0)
    erbs = pvlib.irradiance.erbs(ghi, sp["apparent_zenith"], times)
    out = pd.DataFrame({"ghi": ghi, "dni": erbs["dni"].fillna(0), "dhi": erbs["dhi"].fillna(0),
                        "zen": sp["apparent_zenith"], "az": sp["azimuth"], "day": day}, index=times)
    out.loc[out.zen >= 90, ["ghi", "dni", "dhi"]] = 0.0
    return out


def daily_factors(hourly: pd.DataFrame, cfg: Config, geo: dict):
    """Daily ground-light factor per strip (DataFrame: index day, columns strip)."""
    z = np.radians(hourly.zen.clip(upper=89.9))
    az = np.radians(hourly.az)
    sx = np.sin(z) * np.cos(az - np.radians(cfg.x_azimuth))
    theta_p = np.degrees(np.arctan2(sx, np.cos(z)))
    beam_h = hourly.dni * np.cos(z)
    cols = {}
    for k in range(geo["tb"].shape[0]):
        tb = np.interp(theta_p, ANGLES, geo["tb"][k])
        g = tb * beam_h + geo["svf"][k] * hourly.dhi
        cols[k] = g
    gd = pd.DataFrame(cols, index=hourly.index).groupby(hourly.day.values).sum()
    gh = hourly.ghi.groupby(hourly.day.values).sum()
    f = gd.div(gh.where(gh > 0), axis=0).fillna(1.0).clip(0, 1)
    return f
