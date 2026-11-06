"""Run one stage (period x management) of the India grid over all models and cells.

One task = one cell x one model -> out/<period>_<mgmt>/<model>/<cell>.csv (skipped if present,
so the run resumes after any stop). --open-only runs only the open-field case (fast
validation stage). Each worker gets its own TMPDIR before DSSATTools is imported.
"""
import argparse
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
MODELS = "GFDL-ESM4,IPSL-CM6A-LR,MPI-ESM1-2-HR,MRI-ESM2-0,UKESM1-0-LL"


def init_worker():
    d = f"/tmp/w{os.getpid()}"
    os.makedirs(d, exist_ok=True)
    os.environ["TMPDIR"] = d
    import tempfile
    tempfile.tempdir = d
    sys.path.insert(0, str(HERE))


def work(args):
    npy, meta, cell, soil, period, mgmt, model, out, open_only, crops = args
    import sim_india
    if open_only:
        sim_india.CONFIGS = []
    if crops:
        sim_india.CROPS_ONLY = set(crops.split(","))
    t = time.time()
    try:
        n = sim_india.task(npy, meta, cell, soil, period, mgmt, model, out)
        return out, n, time.time() - t, None
    except Exception:
        import traceback
        return out, 0, time.time() - t, traceback.format_exc()[-1500:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", required=True, help="folder with cells_<model>_<scen>.npy and _meta.npz")
    ap.add_argument("--grid", required=True)
    ap.add_argument("--soil", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--period", required=True, choices=["historical", "ssp245", "ssp585"])
    ap.add_argument("--mgmt", required=True, help="farmer | recommended | current | nXXX (N sweep)")
    ap.add_argument("--crops", default="", help="comma list to restrict crops (calibration sweep)")
    ap.add_argument("--models", default=MODELS)
    ap.add_argument("--only", default="", help="file with one cell_id per line, or comma list")
    ap.add_argument("--open-only", action="store_true")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    a = ap.parse_args()

    grid = pd.read_csv(a.grid)
    grid["row"] = np.arange(len(grid))
    only = set()
    if a.only:
        only = set(open(a.only).read().split()) if os.path.exists(a.only) else set(a.only.split(","))
    stage = f"{a.period}_{a.mgmt}" + ("_open" if a.open_only else "") + os.environ.get("AGRIPV_STAGE_SUFFIX", "")
    tasks = []
    for model in a.models.split(","):
        npy = os.path.join(a.cells, f"cells_{model}_{a.period}.npy")
        meta = dict(np.load(npy.replace(".npy", "_meta.npz"), allow_pickle=True))
        assert list(meta["cell_id"]) == list(grid.cell_id), "grid and climate file differ"
        odir = os.path.join(a.out, stage, model)
        os.makedirs(odir, exist_ok=True)
        for cell in grid.to_dict("records"):
            if only and cell["cell_id"] not in only:
                continue
            out = os.path.join(odir, f"{cell['cell_id']}.csv")
            if not os.path.exists(out):
                tasks.append((npy, meta, cell, os.path.join(a.soil, f"{cell['cell_id']}.json"),
                              a.period, a.mgmt, model, out, a.open_only, a.crops))
    print(f"{stage}: {len(tasks)} tasks to run, {a.workers} workers", flush=True)
    if not tasks:
        return 0
    t0, fails = time.time(), 0
    ctx = mp.get_context("spawn")
    with ctx.Pool(a.workers, initializer=init_worker, maxtasksperchild=50) as pool:
        for k, (out, n, dt, err) in enumerate(pool.imap_unordered(work, tasks, chunksize=1), 1):
            if err:
                fails += 1
                print(f"FAIL {out}: {err}", flush=True)
            if k % 48 == 0 or k == len(tasks):
                el = time.time() - t0
                print(f"{k}/{len(tasks)} done, {fails} failed, {el / 3600:.2f} h elapsed, "
                      f"ETA {el / k * (len(tasks) - k) / 3600:.1f} h, last task {dt:.0f} s", flush=True)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
