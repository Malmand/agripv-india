"""Run the APV-DSSAT grid for one stage (period x management) over all models and cells.

One task = one cell x one model; output out/<period>_<mgmt>/<model>/<cell>.csv.
Finished tasks are skipped, so the run resumes after any interruption.
Each worker gets its own TMPDIR before importing DSSATTools (DSSATTools builds
its model folder under the temp dir at import time; shared folders race).
"""
import argparse
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def init_worker():
    d = f"/tmp/w{os.getpid()}"
    os.makedirs(d, exist_ok=True)
    os.environ["TMPDIR"] = d
    import tempfile
    tempfile.tempdir = d
    sys.path.insert(0, str(HERE))


def work(args):
    npz, idx, soil, period, mgmt, model, out = args
    import sim
    t = time.time()
    try:
        n = sim.task(npz, idx, soil, period, mgmt, model, out)
        return out, n, time.time() - t, None
    except Exception as e:  # keep going; failed tasks are retried on the next launch
        import traceback
        return out, 0, time.time() - t, traceback.format_exc()[-1500:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", required=True, help="folder with cells_<model>_<scen>.npz")
    ap.add_argument("--soil", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--period", required=True, choices=["historical", "ssp245", "ssp585"])
    ap.add_argument("--mgmt", required=True, choices=["farmer", "recommended"])
    ap.add_argument("--models", default="GFDL-ESM4,IPSL-CM6A-LR,MPI-ESM1-2-HR,MRI-ESM2-0,UKESM1-0-LL")
    ap.add_argument("--only", default="", help="comma list of cell ids (testing)")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    a = ap.parse_args()

    tasks = []
    for model in a.models.split(","):
        npz = os.path.join(a.cells, f"cells_{model}_{a.period}.npz")
        ids = np.load(npz, allow_pickle=True)["cell_id"]
        odir = os.path.join(a.out, f"{a.period}_{a.mgmt}", model)
        os.makedirs(odir, exist_ok=True)
        for i, cid in enumerate(ids):
            cid = str(cid)
            if a.only and cid not in a.only.split(","):
                continue
            out = os.path.join(odir, f"{cid}.csv")
            if not os.path.exists(out):
                tasks.append((npz, i, os.path.join(a.soil, f"{cid}.json"), a.period, a.mgmt, model, out))
    print(f"{a.period} {a.mgmt}: {len(tasks)} tasks to run, {a.workers} workers", flush=True)
    if not tasks:
        return 0
    t0, fails = time.time(), 0
    ctx = mp.get_context("spawn")
    with ctx.Pool(a.workers, initializer=init_worker, maxtasksperchild=50) as pool:
        for k, (out, n, dt, err) in enumerate(pool.imap_unordered(work, tasks), 1):
            if err:
                fails += 1
                print(f"FAIL {out}: {err}", flush=True)
            if k % 12 == 0 or k == len(tasks):
                el = time.time() - t0
                eta = el / k * (len(tasks) - k) / 3600
                print(f"{k}/{len(tasks)} done, {fails} failed, {el / 3600:.2f} h elapsed, "
                      f"ETA {eta:.1f} h, last task {dt:.0f} s", flush=True)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
