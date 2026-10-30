"""Build the 0.25 deg pilot grid over Rajasthan.

Cell centres sit at x.125 / x.375 / x.625 / x.875 so they coincide with the
native NEX-GDDP-CMIP6 grid (Thrasher et al., 2022) and need no regridding.
A cell is kept when its centre falls inside the state boundary.
"""
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parents[1]
RES = 0.25
ANCHOR = (26.375, 73.125)  # cell containing ICAR-CAZRI Jodhpur (26.27 N, 73.02 E)


def build(state="Rajasthan"):
    states = gpd.read_file(ROOT / "data/boundaries/Admin2.shp")
    poly = states.loc[states.ST_NM == state, "geometry"].union_all()
    minx, miny, maxx, maxy = poly.bounds
    lats = np.arange(np.floor(miny / RES) * RES + RES / 2, maxy, RES)
    lons = np.arange(np.floor(minx / RES) * RES + RES / 2, maxx, RES)
    rows = []
    for la in lats:
        for lo in lons:
            if poly.contains(Point(lo, la)):
                rows.append((round(la, 3), round(lo, 3)))
    cells = pd.DataFrame(rows, columns=["lat", "lon"])
    cells.insert(0, "cell_id", [f"R{i:04d}" for i in range(len(cells))])
    cells["anchor"] = (cells.lat == ANCHOR[0]) & (cells.lon == ANCHOR[1])
    return cells


if __name__ == "__main__":
    cells = build()
    out = ROOT / "data/grid_rajasthan_025.csv"
    cells.to_csv(out, index=False)
    print(f"{len(cells)} cells written to {out}")
    print(cells[cells.anchor])
