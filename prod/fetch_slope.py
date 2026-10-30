"""Run in Google Cloud Shell: terrain slope per 0.25 deg India grid cell from the
Copernicus DEM GLO-90 (public AWS bucket, no login).

For every cell: mean elevation (m), mean slope (%), and the share of the cell's area
with slope <= 5% and <= 10% (thresholds used in PV / agrivoltaic siting studies).
Only the 1x1 deg tiles that contain grid cells are read. Output: slope_india.csv.
Usage:  python3 fetch_slope.py grid_india_025.csv
"""
import csv
import sys
import urllib.request

import numpy as np
import rasterio

BASE = "https://copernicus-dem-90m.s3.amazonaws.com"


def tile_url(lat0, lon0):
    ns = f"N{lat0:02d}" if lat0 >= 0 else f"S{-lat0:02d}"
    ew = f"E{lon0:03d}" if lon0 >= 0 else f"W{-lon0:03d}"
    name = f"Copernicus_DSM_COG_30_{ns}_00_{ew}_00_DEM"
    return f"{BASE}/{name}/{name}.tif"


def main(grid_csv):
    cells = list(csv.DictReader(open(grid_csv)))
    tiles = {}
    for c in cells:
        lat, lon = float(c["lat"]), float(c["lon"])
        tiles.setdefault((int(np.floor(lat)), int(np.floor(lon))), []).append(c)
    print(f"{len(cells)} cells in {len(tiles)} DEM tiles", flush=True)
    out = []
    for k, ((lat0, lon0), cs) in enumerate(sorted(tiles.items()), 1):
        url = tile_url(lat0, lon0)
        try:
            with rasterio.open(url) as src:
                z = src.read(1).astype("float64")
                t = src.transform
        except Exception as e:      # no tile = sea; cells keep NaN
            print(f"  no tile {lat0} {lon0}: {e}", flush=True)
            for c in cs:
                out.append((c["cell_id"], "", "", "", ""))
            continue
        ny, nx = z.shape
        lats = t.f + (np.arange(ny) + 0.5) * t.e
        dy = abs(t.e) * 111320.0
        dx = abs(t.a) * 111320.0 * np.cos(np.radians(lats))[:, None]
        gy, gx = np.gradient(z)
        slope = 100.0 * np.hypot(gx / dx, gy / dy)               # percent
        lons = t.c + (np.arange(nx) + 0.5) * t.a
        for c in cs:
            la, lo = float(c["lat"]), float(c["lon"])
            r = (lats >= la - 0.125) & (lats < la + 0.125)
            q = (lons >= lo - 0.125) & (lons < lo + 0.125)
            s = slope[np.ix_(r, q)]
            e = z[np.ix_(r, q)]
            if s.size == 0:
                out.append((c["cell_id"], "", "", "", ""))
                continue
            out.append((c["cell_id"], f"{e.mean():.0f}", f"{s.mean():.2f}",
                        f"{(s <= 5).mean():.3f}", f"{(s <= 10).mean():.3f}"))
        if k % 20 == 0:
            print(f"{k}/{len(tiles)} tiles", flush=True)
    with open("slope_india.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cell_id", "elev_m", "slope_mean_pct", "frac_slope_le5", "frac_slope_le10"])
        w.writerows(out)
    print("wrote slope_india.csv", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
