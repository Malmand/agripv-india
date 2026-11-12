"""Progress and health report for the India run, written every 30 min to the bucket.

status.txt shows, per stage: tasks done / total, failures, ETA, and quick sanity
statistics from the finished tasks (open-field yield and RY at GCR 0.3 by crop),
plus compute hours and an approximate spend. Health rules stop the run early so
credit is not wasted on a broken run:
  * more than 2% of finished tasks failed, or
  * after >= 60 finished tasks, a crop's median open-field yield is outside a
    plausible range for India (kg/ha below), or
  * more than 5% of simulated seasons are crop failures (yield 0) under open field
    for an irrigated system.
On a halt it writes /data/HALT with the reason; the startup script will not resume
until the metadata key halt_ack=yes is set.
Exit code 3 = halt.
"""
import glob
import os
import random
import re
import sys
import time

import pandas as pd

DATA = os.environ.get("AGRIPV_DATA", "/data")
PLAUSIBLE = {"wheat": (800, 7000), "chickpea": (200, 3000), "groundnut": (200, 5000),
             "pearl_millet": (150, 4500)}
EUR_PER_H = 0.33   # e2-custom-12 (12 vCPU, 24 GB), europe-west1, approximate


def stage_stats(stage_dir, sample=150):
    files = glob.glob(os.path.join(stage_dir, "*", "*.csv"))
    if not files:
        return None
    pick = random.sample(files, min(sample, len(files)))
    d = pd.concat((pd.read_csv(f) for f in pick), ignore_index=True)
    op = d[d.config == "open"]
    res = {"files": len(files),
           "open_median": op.groupby("crop").hwam.median().round(0).to_dict(),
           "irrigated_zero_share": float((op[op.water == "ir"].hwam <= 0).mean()) if (op.water == "ir").any() else 0.0}
    if (d.config != "open").any():
        k = ["cell", "model", "crop", "water"]
        o = op.groupby(k).hwam.mean().rename("open")
        a = d[(d.config != "open") & (d.gcr.round(2) == 0.3)]
        a = a.groupby(k + ["config", "season"]).agg(y=("hwam", "mean"), cf=("cult_frac", "first")).reset_index()
        a = a.groupby(k + ["config"]).agg(y=("y", "mean"), cf=("cf", "first")).reset_index().join(o, on=k)
        a["ry"] = a.y * a.cf / a.open
        res["ry03_median"] = a.groupby(["crop", "config"]).ry.median().round(2).unstack().to_dict("index")
    return res


def main():
    log = open(os.path.join(DATA, "pipeline.log")).read() if os.path.exists(os.path.join(DATA, "pipeline.log")) else ""
    lines = [l for l in log.splitlines() if "warn" not in l.lower()]
    prog = [l for l in lines if re.search(r"\d+/\d+ done", l)]
    stages = [l for l in lines if "stage " in l or "tasks to run" in l or "===" in l][-6:]
    fails = len([l for l in lines if l.startswith("FAIL ")])
    up_h = float(open("/proc/uptime").read().split()[0]) / 3600
    out = [f"AgriPV India status  {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}",
           f"machine up {up_h:.1f} h this boot (about EUR {up_h * EUR_PER_H:.0f} this boot)", ""]
    out += stages + (prog[-1:] if prog else ["(no simulation progress yet: still downloading or converting)"])
    nex = len(glob.glob(f"{DATA}/nex/data/*/*/*/*.nc"))
    soil = len(glob.glob(f"{DATA}/soil/*.json"))
    npy = len([f for f in glob.glob(f"{DATA}/cells/*.npy") if "part" not in f])
    out += ["", f"inputs: climate files {nex}/1800, soil cells {soil}/2977, converted {npy}/15", ""]
    halt = []
    done_total = 0
    for sd in sorted(glob.glob(f"{DATA}/out/*")):
        if not os.path.isdir(sd) or sd.endswith("summary"):
            continue
        s = stage_stats(sd)
        if not s:
            continue
        done_total += s["files"]
        out.append(f"[{os.path.basename(sd)}] {s['files']} tasks finished")
        out.append(f"  open-field median yield (kg/ha): {s['open_median']}")
        if "ry03_median" in s:
            out.append(f"  RY at GCR 0.3, median: {s['ry03_median']}")
        # the N calibration sweep is deliberately extreme (30-180 kg N): no yield-range check there
        # cells run south -> north, so early files are all southern (low-yield wheat in Karnataka,
        # Maharashtra): only a coarse floor until one full climate-model pass (2977 cells) is done
        if s["files"] >= 60 and not re.search(r"_n\d+_open$", os.path.basename(sd)):
            # recommended-N stages also run south -> north, so they get the coarse floor too until a full pass
            # (ssp585_recommended stopped falsely at 346 tasks: southern wheat median 733 < 800)
            full_pass = s["files"] >= 2977 or "_open" in os.path.basename(sd)
            for crop, v in s["open_median"].items():
                lo, hi = PLAUSIBLE.get(crop, (0, 1e9)) if full_pass else (200, 9000)
                if not lo <= v <= hi:
                    halt.append(f"{os.path.basename(sd)}: {crop} median open yield {v} outside {lo}-{hi}")
            if s["irrigated_zero_share"] > 0.05:
                halt.append(f"{os.path.basename(sd)}: {s['irrigated_zero_share']:.0%} irrigated seasons failed")
    if done_total >= 50 and fails / max(done_total, 1) > 0.02:
        halt.append(f"{fails} failed tasks out of {done_total}")
    issues = len(glob.glob(f"{DATA}/out/*/*/*.issues"))
    out += ["", f"failed tasks so far: {fails}; tasks with DSSAT retries: {issues}",
            "HEALTH: " + ("STOP -> " + "; ".join(halt) if halt else "OK")]
    open(os.path.join(DATA, "status.txt"), "w").write("\n".join(out) + "\n")
    if halt:
        open(os.path.join(DATA, "HALT"), "w").write("\n".join(halt) + "\n")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
