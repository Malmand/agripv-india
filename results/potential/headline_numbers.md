# Headline numbers (median over 5 GCMs, range in brackets)

## historical_current: crops combined, slope ≤ 5%

| Layout | τ | Land (Mha) | Capacity (TWp) | Energy (PWh/yr) |
|---|---|---|---|---|
| ew_fixed | 0.66 | 39.67 | 51.14 (50.76–51.36) | 90.68 (90.06–91.05) |
| south_fixed | 0.66 | 39.67 | 40.30 (40.11–40.47) | 77.24 (76.91–77.53) |
| vertical | 0.66 | 39.67 | 47.60 (47.51–47.69) | 58.59 (58.51–58.67) |
| ew_fixed | 0.80 | 39.67 | 45.50 (45.48–45.90) | 81.14 (81.13–81.81) |
| south_fixed | 0.80 | 39.67 | 34.32 (33.97–34.42) | 66.49 (65.86–66.65) |
| vertical | 0.80 | 39.67 | 42.02 (41.81–42.30) | 52.74 (52.53–53.03) |
| ew_fixed | 0.90 | 39.67 | 40.02 (39.82–40.48) | 71.66 (71.33–72.43) |
| south_fixed | 0.90 | 39.67 | 28.99 (28.47–29.15) | 56.59 (55.66–56.88) |
| vertical | 0.90 | 39.67 | 37.15 (36.81–37.43) | 46.96 (46.61–47.34) |

### historical_current: area-weighted GCR_max at τ = 0.80 (all GCMs pooled)

| Crop | Layout | GCR_max | Share of area at simulated GCR limit |
|---|---|---|---|
| chickpea | ew_fixed | 0.27 | 6% |
| chickpea | south_fixed | 0.20 | 0% |
| chickpea | vertical | 0.25 | 9% |
| groundnut | ew_fixed | 0.32 | 5% |
| groundnut | south_fixed | 0.32 | 2% |
| groundnut | vertical | 0.31 | 11% |
| pearl_millet | ew_fixed | 0.58 | 1% |
| pearl_millet | south_fixed | 0.51 | 0% |
| pearl_millet | vertical | 0.59 | 86% |
| wheat | ew_fixed | 0.62 | 42% |
| wheat | south_fixed | 0.44 | 0% |
| wheat | vertical | 0.55 | 75% |

### historical_current: top states, best layout, τ = 0.80 (GWp)

- Uttar Pradesh: 14324
- Rajasthan: 7711
- Madhya Pradesh: 6554
- Haryana: 3458
- Bihar: 3149
- Punjab: 2522
- Gujarat: 2396
- Maharashtra: 2248

## Vertical layout, DIN cap GCR_max ≤ 0.6 (main) vs uncapped, historical_current (TWp)

- τ 0.66: capped 47.60, uncapped 53.06 (-10%)
- τ 0.80: capped 42.02, uncapped 47.19 (-11%)
- τ 0.90: capped 37.15, uncapped 40.79 (-9%)

## Sanity checks

### historical_current: capacity density and specific yield (slope ≤ 5%)

| Layout | τ | MWp per ha of land | kWh/kWp/yr |
|---|---|---|---|
| ew_fixed | 0.66 | 1.29 | 1773 |
| south_fixed | 0.66 | 1.02 | 1917 |
| vertical | 0.66 | 1.20 | 1231 |
| ew_fixed | 0.80 | 1.15 | 1783 |
| south_fixed | 0.80 | 0.87 | 1937 |
| vertical | 0.80 | 1.06 | 1255 |
| ew_fixed | 0.90 | 1.01 | 1790 |
| south_fixed | 0.90 | 0.73 | 1952 |
| vertical | 0.90 | 0.94 | 1264 |

- historical_current: vertical layout, share of eligible area with uncapped GCR_max > 0.6 (DIN 15% land loss, capped at 0.6 in the main case): τ 0.66 65%, τ 0.80 62%, τ 0.90 45%

### historical_current: open-field yield (kg/ha, 5-GCM median, SPAM-area weighted)

| Crop | Cells | India mean | States matched | Sim/obs (matched states) | Sim/calibration sim |
|---|---|---|---|---|---|
| chickpea | 1462 | 834 | 15 | 1.04 | 1.02 |
| groundnut | 897 | 2689 | 13 | 2.40 | 1.01 |
| pearl_millet | 1024 | 982 | 9 | 1.14 | 1.08 |
| wheat | 2095 | 2803 | 15 | 1.00 | 1.00 |

Legumes are compared with uncalibrated (farmer N) runs; groundnut sim/obs about 2.7 is known.
