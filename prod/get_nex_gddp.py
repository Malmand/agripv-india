"""Download NEX-GDDP-CMIP6 daily data for Rajasthan (AgriPV India project).

What it fetches
  Models    : GFDL-ESM4, IPSL-CM6A-LR, MPI-ESM1-2-HR, MRI-ESM2-0, UKESM1-0-LL (ISIMIP3b set)
  Scenarios : historical 1995-2014, ssp245 and ssp585 2041-2060
  Variables : rsds, tasmax, tasmin, pr, hurs, sfcWind
  Area      : 23.0-30.25 N, 69.5-78.25 E (all 0.25 deg cells covering Rajasthan)
  Total     : 1,800 files, about 1.8 GB, roughly 1 hour with 6 parallel downloads

Source: NASA NCCS THREDDS subset service (no login). Thrasher et al. (2022),
Scientific Data 9, 262.

How to run (Anaconda Prompt or any terminal with Python 3.8+; no extra packages):
    cd %USERPROFILE%\\Downloads\\nex_gddp_rajasthan
    python get_nex_gddp.py

Safe to stop and restart: finished files are skipped. Re-run until it reports
0 missing. Output goes to .\\data\\<model>\\<scenario>\\<var>\\<file>.nc
"""
import os
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "https://ds.nccs.nasa.gov/thredds"
ROOT = "AMES/NEX/GDDP-CMIP6"
MODELS = {"GFDL-ESM4": "r1i1p1f1", "IPSL-CM6A-LR": "r1i1p1f1", "MPI-ESM1-2-HR": "r1i1p1f1",
          "MRI-ESM2-0": "r1i1p1f1", "UKESM1-0-LL": "r1i1p1f2"}
PERIODS = {"historical": range(1995, 2015), "ssp245": range(2041, 2061), "ssp585": range(2041, 2061)}
if os.environ.get("AGRIPV_PERIODS"):                             # e.g. "historical" (rice VM)
    PERIODS = {k: v for k, v in PERIODS.items() if k in os.environ["AGRIPV_PERIODS"].split(",")}
VARS = ["rsds", "tasmax", "tasmin", "pr", "hurs", "sfcWind"]
BBOX = dict(north=30.25, south=23.0, west=69.5, east=78.25)   # Rajasthan (default)
if os.environ.get("AGRIPV_BBOX"):                                # "north,south,west,east"
    BBOX = dict(zip(["north", "south", "west", "east"], map(float, os.environ["AGRIPV_BBOX"].split(","))))
WORKERS = 6
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def get(url, tries=5, timeout=180):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # network hiccup or server busy: back off and retry
            if i == tries - 1:
                raise
            time.sleep(5 * (i + 1))


def catalog(model, scen, var):
    """Exact file names from the THREDDS catalog; keeps the newest version per year."""
    url = f"{BASE}/catalog/{ROOT}/{model}/{scen}/{MODELS[model]}/{var}/catalog.xml"
    names = re.findall(r'name="([^"]+\.nc)"', get(url).decode())
    best = {}
    for n in names:
        m = re.search(r"_(\d{4})(?:_v(\d+\.\d+))?\.nc$", n)
        if not m:
            continue
        yr, ver = int(m.group(1)), float(m.group(2) or 0)
        if yr not in best or ver > best[yr][0]:
            best[yr] = (ver, n)
    return {yr: n for yr, (ver, n) in best.items()}


def task_list():
    tasks = []
    for model in MODELS:
        for scen, years in PERIODS.items():
            for var in VARS:
                files = catalog(model, scen, var)
                for yr in years:
                    if yr not in files:
                        print(f"  not on server: {model} {scen} {var} {yr}")
                        continue
                    tasks.append((model, scen, var, yr, files[yr]))
        print(f"catalogued {model}", flush=True)
    return tasks


def fetch(model, scen, var, yr, fname):
    dest_dir = os.path.join(OUT, model, scen, var)
    dest = os.path.join(dest_dir, fname)
    if os.path.exists(dest) and os.path.getsize(dest) > 10_000:
        return "skip"
    os.makedirs(dest_dir, exist_ok=True)
    q = "&".join(f"{k}={v}" for k, v in BBOX.items())
    url = (f"{BASE}/ncss/grid/{ROOT}/{model}/{scen}/{MODELS[model]}/{var}/{fname}"
           f"?var={var}&{q}&horizStride=1"
           # each file holds one year; 'temporal=all' also works for UKESM's 360-day calendar,
           # where a Dec-31 end date is invalid (HTTP 400)
           f"&temporal=all&accept=netcdf4")
    data = get(url)
    if len(data) < 10_000:
        raise RuntimeError(f"suspiciously small response ({len(data)} bytes)")
    tmp = dest + ".part"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, dest)
    return "ok"


def main():
    print("Reading THREDDS catalogues ...", flush=True)
    tasks = task_list()
    print(f"{len(tasks)} files to check; downloading with {WORKERS} workers\n", flush=True)
    done = failed = 0
    t0 = time.time()
    with ThreadPoolExecutor(WORKERS) as ex:
        futs = {ex.submit(fetch, *t): t for t in tasks}
        for i, fu in enumerate(as_completed(futs), 1):
            t = futs[fu]
            try:
                fu.result()
                done += 1
            except Exception as e:
                failed += 1
                print(f"  FAILED {t[0]} {t[1]} {t[2]} {t[3]}: {e}", flush=True)
            if i % 25 == 0 or i == len(tasks):
                el = time.time() - t0
                print(f"{i}/{len(tasks)} done, {failed} failed, {el / 60:.1f} min elapsed", flush=True)
    missing = [t for t in tasks if not os.path.exists(os.path.join(OUT, t[0], t[1], t[2], t[4]))]
    print(f"\nFinished. {len(missing)} missing. "
          + ("All files present." if not missing else "Run the script again to retry them."))


if __name__ == "__main__":
    sys.exit(main())
