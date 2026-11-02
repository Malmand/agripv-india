# Headline numbers (median over 5 GCMs, range in brackets)

## historical_current: crops combined, slope ≤ 5%

| Layout | τ | Land (Mha) | Capacity (TWp) | Energy (PWh/yr) |
|---|---|---|---|---|
| ew_fixed | 0.66 | 39.67 | 51.14 (50.76–51.36) | 90.68 (90.06–91.05) |
| south_fixed | 0.66 | 39.67 | 40.30 (40.11–40.47) | 77.24 (76.91–77.53) |
| vertical | 0.66 | 39.67 | 53.06 (53.00–53.16) | 62.97 (62.92–63.06) |
| ew_fixed | 0.80 | 39.67 | 45.50 (45.48–45.90) | 81.14 (81.13–81.81) |
| south_fixed | 0.80 | 39.67 | 34.32 (33.97–34.42) | 66.49 (65.86–66.65) |
| vertical | 0.80 | 39.67 | 47.19 (46.91–47.28) | 57.00 (56.73–57.15) |
| ew_fixed | 0.90 | 39.67 | 40.02 (39.82–40.48) | 71.66 (71.33–72.43) |
| south_fixed | 0.90 | 39.67 | 28.99 (28.47–29.15) | 56.59 (55.66–56.88) |
| vertical | 0.90 | 39.67 | 40.79 (40.11–40.91) | 49.99 (49.30–50.23) |

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
| pearl_millet | vertical | 0.68 | 86% |
| wheat | ew_fixed | 0.62 | 42% |
| wheat | south_fixed | 0.44 | 0% |
| wheat | vertical | 0.63 | 75% |

### historical_current: top states, best layout, τ = 0.80 (GWp)

- Uttar Pradesh: 14661
- Rajasthan: 8353
- Madhya Pradesh: 6677
- Haryana: 3765
- Bihar: 3149
- Punjab: 2522
- Gujarat: 2407
- Maharashtra: 2376

## Sanity checks

### historical_current: capacity density and specific yield (slope ≤ 5%)

| Layout | τ | MWp per ha of land | kWh/kWp/yr |
|---|---|---|---|
| ew_fixed | 0.66 | 1.29 | 1773 |
| south_fixed | 0.66 | 1.02 | 1917 |
| vertical | 0.66 | 1.34 | 1187 |
| ew_fixed | 0.80 | 1.15 | 1783 |
| south_fixed | 0.80 | 0.87 | 1937 |
| vertical | 0.80 | 1.19 | 1208 |
| ew_fixed | 0.90 | 1.01 | 1790 |
| south_fixed | 0.90 | 0.73 | 1952 |
| vertical | 0.90 | 1.03 | 1226 |

- historical_current: vertical layout, share of eligible area with GCR_max > 0.6 (DIN 15% land loss): τ 0.66 65%, τ 0.80 62%, τ 0.90 45%

### historical_current: open-field yield (kg/ha, 5-GCM median, SPAM-area weighted)

| Crop | Cells | India mean | States matched | Sim/obs (matched states) | Sim/calibration sim |
|---|---|---|---|---|---|
| chickpea | 1462 | 834 | 15 | 1.04 | 1.02 |
| groundnut | 897 | 2689 | 13 | 2.40 | 1.01 |
| pearl_millet | 1024 | 982 | 9 | 1.14 | 1.08 |
| wheat | 2095 | 2803 | 15 | 1.00 | 1.00 |

Legumes are compared with uncalibrated (farmer N) runs; groundnut sim/obs about 2.7 is known.
