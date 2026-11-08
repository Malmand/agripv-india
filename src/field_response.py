"""Field-response scenario: rescale the simulated relative yield (RY) so that its dependence on the reduction in
ground light follows the observations compiled by Jha et al. (2026), then rerun the potential.

 1. Observed curve per crop: decreasing (isotonic) fit of observed RY against reduction in solar radiation, anchored at
    (0, 1). Wheat <- wheat and durum wheat; chickpea and groundnut <- grain legumes; pearl millet <- maize (no millet in the data).
 2. Mean ground-light reduction red(config, GCR) from the light model at a representative central-Indian site and season
    (as in shade_response_check.py).
 3. Correction c(red) = min(1, observed(red) / national median simulated RY(red)), per crop and nitrogen case
    (simulated median from the east-west curves). RY_field = RY_sim * c(red(config, GCR)). Spatial differences between cells
    are kept; only the average response is aligned with the observations.
 4. postprocess_india.py is run on the rescaled RY (robust case: lower GCR_max of calibrated and recommended nitrogen).
Usage: python3 src/field_response.py [path/to/Data_Clean.xlsx] [--variant=nosoy|c3|millet_c3] [--skip-run] [--relight]
Outputs: results/shade_field_curves.csv, results/shade_light_reduction.csv, results/potential_field/*"""
import sys, pathlib, subprocess, tempfile, shutil
import numpy as np, pandas as pd
R = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / "prod"))

SEASON = {"wheat": ("2019-11-15", 120, 16.0), "chickpea": ("2019-11-01", 110, 16.0),
          "pearl_millet": ("2019-07-01", 90, 19.0), "groundnut": ("2019-07-01", 110, 19.0)}
OBS = {"wheat": lambda d: d.Crop.isin(["Wheat", "Durum wheat"]), "chickpea": lambda d: d.Crop_type.eq("Grain legumes"),
       "groundnut": lambda d: d.Crop_type.eq("Grain legumes"), "pearl_millet": lambda d: d.Crop_type.eq("Maize")}
# proxy-choice sensitivity (Supplement S14): alternative observation sets for the same four crops
VARIANTS = {
    "main": {},
    "nosoy": {"chickpea": lambda d: d.Crop_type.eq("Grain legumes") & ~d.Crop.eq("Soybean"),
              "groundnut": lambda d: d.Crop_type.eq("Grain legumes") & ~d.Crop.eq("Soybean")},
    "c3": {"wheat": lambda d: d.Crop_type.eq("C3 cereals") | d.Crop.isin(["Wheat", "Durum wheat"])},
    "millet_c3": {"pearl_millet": lambda d: d.Crop_type.isin(["Maize", "C3 cereals"])},
}
LAT, LON = 25.0, 78.0
GR = np.round(np.arange(0, 0.9 + 1e-9, 0.01), 2)

def pava_decreasing(x, y):
    o = np.argsort(x); x, y = np.asarray(x)[o], np.asarray(y)[o]
    blocks = [[v, 1.0, v] for v in y]            # mean, weight, (value)
    out = []
    for v in y:
        out.append([v, 1])
        while len(out) > 1 and out[-2][0] < out[-1][0]:       # violation of decreasing order
            m2, w2 = out.pop(); m1, w1 = out.pop(); out.append([(m1 * w1 + m2 * w2) / (w1 + w2), w1 + w2])
    fit = np.concatenate([[m] * w for m, w in out]); return x, fit

def observed_curves(path):
    d = pd.read_excel(path).rename(columns={"RSR (%)": "rsr", "Yield (%)": "ry"}); d["rsr"] /= 100; d["ry"] /= 100
    rows = []
    for crop, f in OBS.items():
        o = d[f(d) & (d.rsr <= 0.8)]
        x = np.r_[0.0, o.rsr.values]; y = np.r_[1.0, np.minimum(o.ry.values, 1.0)]    # gains above 1 are not credited
        xs, fit = pava_decreasing(x, y)
        curve = np.interp(GR, xs, fit); curve[0] = 1.0
        rows += [dict(crop=crop, rsr=a, ry_obs=b, n_obs=len(o)) for a, b in zip(GR, curve)]
    return pd.DataFrame(rows)

def light_reduction():
    import pv_shading as ps          # needs pvlib; only used when the light reduction is recomputed
    rows = []
    for crop, (start, nd, srad) in SEASON.items():
        dates = pd.date_range(start, periods=nd + 2)
        hourly = ps.hourly_from_daily(LAT, LON, dates, np.full(len(dates), srad))
        for config in ("south_fixed", "ew_fixed", "vertical"):
            cfg = ps.make_config(config)
            for g in (0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7):
                f = ps.daily_factors(hourly, cfg, ps.strip_geometry(cfg, g)).iloc[1:nd + 1]
                rows.append(dict(crop=crop, config=config, gcr=g, reduction=1 - float(f.mean(axis=1).mean())))
    return pd.DataFrame(rows)

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    var = next((a.split("=")[1] for a in sys.argv if a.startswith("--variant=")), "main")
    sfx = "" if var == "main" else "_" + var
    OBS.update(VARIANTS[var])
    cur = R / "results/shade_field_curves.csv"
    if args:                                      # xlsx given: rebuild the observed curves
        obs = observed_curves(args[0])
        if var == "main":
            obs.to_csv(cur, index=False, float_format="%.4f")
    else:                                         # no data file: use the committed curves (main variant only)
        assert var == "main", "variants need the Data_Clean.xlsx path"
        obs = pd.read_csv(cur)
    lrf = R / "results/shade_light_reduction.csv"
    if lrf.exists() and "--relight" not in sys.argv:
        lr = pd.read_csv(lrf)
    else:
        lr = light_reduction(); lr.to_csv(lrf, index=False, float_format="%.4f")
    SUM = R / "runs/s1/summary"; tmp = pathlib.Path(tempfile.mkdtemp())
    corr = {}
    for nm in ("current", "recommended"):
        ry = pd.read_csv(SUM / f"ry_crop_historical_{nm}.csv.gz")
        ew = ry[ry.config == "ew_fixed"]
        for crop in SEASON:
            sim = ew[ew.crop == crop].groupby("gcr").ry.median()
            red_ew = lr[(lr.crop == crop) & (lr.config == "ew_fixed")].set_index("gcr").reduction.reindex(sim.index)
            o = obs[obs.crop == crop]
            ratio = np.minimum(1.0, np.interp(red_ew.values, o.rsr.values, o.ry_obs.values) / sim.values)
            corr[(nm, crop)] = (np.r_[0, red_ew.values], np.r_[1, ratio])
        parts = []
        for (crop, config), d in ry.groupby(["crop", "config"]):
            red = lr[(lr.crop == crop) & (lr.config == config)].set_index("gcr").reduction
            red = np.interp(d.gcr.values, red.index.values, red.values, left=None)
            x, c = corr[(nm, crop)]
            parts.append(d.assign(ry=d.ry.values * np.interp(red, x, c)))
        pd.concat(parts).sort_index().to_csv(tmp / f"ry_crop_historical_{nm}.csv.gz", index=False)
    pd.DataFrame([dict(nmode=k[0], crop=k[1], reduction=a, factor=b) for k, (x, c) in corr.items() for a, b in zip(x, c)]) \
        .to_csv(R / ("results/shade_field_correction" + sfx + ".csv"), index=False, float_format="%.4f")
    if "--skip-run" not in sys.argv:
        en = SUM / "energy_historical_rc.csv"; en = en if en.exists() else SUM / "energy_historical.csv"
        out = R / ("results/potential_field" + sfx); out.mkdir(exist_ok=True)
        subprocess.run([sys.executable, str(R / "prod/postprocess_india.py"), "--summary", str(tmp), "--stage", "historical_current",
                        "--robust-with", "historical_recommended", "--grid", str(R / "data/grid_india_025.csv"),
                        "--slope", str(R / "data/slope_india.csv"), "--energy", str(en), "--din-cap", "0.6", "--outdir", str(out)], check=True)
    shutil.rmtree(tmp)
