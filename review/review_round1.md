# Review, round 1

**Manuscript:** Yield-constrained agrivoltaic potential of India under current and mid-century climate
**Journal:** Applied Energy
**Material reviewed:** Manuscript_AgriPV_India.docx and Supplementary_Methods_AgriPV_India.docx, rebuilt on 4 November 2026
(`node paper/methods/build_methods.js`, `node paper/methods/build_supp.js`, numbers taken from
`results/potential/numbers.json`), the graphical abstract (`graphical_abstract_simple.png` and its caption), `highlights.txt`,
and Figs. 3 to 7 and S1 to S3. Numbers were checked against `results/potential/numbers.json`, `headline_numbers.md`,
`india_combined_*.csv`, `cell_crop_historical_current.csv.gz` and `results/validation_before_after.csv`. All 46 Crossref DOIs were
queried on api.crossref.org.
**Not flagged, as instructed:** the [pending] robust (recommended-nitrogen) case and the [pending] SSP2-4.5 results.

---

## 1. Summary of the submission

The authors couple a two-dimensional view-factor light model of five ground strips below three agrivoltaic (APV) layouts (south-facing elevated, east-west elevated ridge, vertical bifacial) with DSSAT 4.8 (CERES-Wheat, CERES-Millet, CROPGRO-Chickpea, CROPGRO-Peanut). They run it on 2977 cells of a 0.25° grid of India, driven by five NEX-GDDP-CMIP6 GCMs, for 1995 to 2014 and 2041 to 2060 (SSP2-4.5, SSP5-8.5). Nitrogen for wheat and pearl millet is calibrated by state against ICRISAT district statistics. For each cell, crop and layout the largest ground coverage ratio (GCR_max) that keeps relative yield (RY) at or above 0.66, 0.80 or 0.90 is found by interpolation. Capacity follows from module area times 0.22 kWp m⁻², on MapSPAM 2010 harvested area restricted to slopes of 5% or less, with rabi and kharif land overlapped. The main case (east-west, RY ≥ 0.80, calibrated N) gives 45.5 TWp on 39.7 Mha and 81.1 PWh yr⁻¹, about 48 times India's 2025-26 electricity requirement. The authors call this an upper bound because low nitrogen rates hide shade losses. A robust case with recommended nitrogen is pending. The SSP5-8.5 change is −1%. A waterfall figure reconciles the estimate with TERI (1.2 to 2.1 TW) and Fraunhofer ISE et al. (3.2 to 13.8 TW).

The topic fits Applied Energy, and the paper fills a real gap. National APV estimates for India use fixed power densities and crop rules rather than simulated yields, and the coupling of strip-resolved light with a calibrated crop model at national scale is new. The writing is mostly clear, the limitations section is honest, and the reconciliation figure (Fig. 7) is a useful device. However, the manuscript is incomplete as a journal submission (no abstract, no conclusions, a broken Section 3.4). The headline is a number the authors themselves describe as inflated. Several central claims rest on a Rajasthan pilot that is never described. The PV energy model gives specific yields that look high for India and is not validated. The uncertainty analysis covers only the GCM spread. These points need to be resolved before the paper can be judged on its results.

---

## 2. Major comments

**M1. The manuscript is not complete as a submission.**
- There is no Abstract and no Keywords. Applied Energy requires both, and the highlights (`highlights.txt`) are not part of the built manuscript.
- The Introduction ends with "Section 5 concludes", but there is no Section 5 (Conclusions). The manuscript ends with 4.6 Limitations and the references.
- Section 3.4 (Mid-century change) is two sentences: "Under SSP5-8.5 the change is −1% (GCM range −6% to 0%). Under SSP5-8.5 they agree on 57% of the land." The second sentence has no subject ("they" = the GCMs?), and "agree" is undefined (agree on what: sign of the change in GCR_max, four of five models?). The same −1% sentence opens Section 4.4 word for word. The results of RQ3 are therefore effectively absent, apart from Fig. 6. Contribution (iv) ("reports model agreement for every result") is not delivered: one agreement number is given, and it is undefined.
- No nomenclature, data availability or declarations sections appear in the manuscript (drafts exist in `paper/submission/`; they should be included or referenced).

**M2. The headline is an upper bound that the authors consider inflated.** The text says the robust case is "the conservative headline", but the only national figure in the paper, the highlights and the graphical abstract is the calibrated-N 45.5 TWp. In the east-west layout 42% of the wheat area (and 75% of vertical wheat and 86% of vertical millet before the cap) still meets the threshold at the largest simulated GCR, so even this upper bound is censored at the simulation grid. I accept that the robust run is pending. However, the paper should not be submitted, and the graphical abstract should not headline 45.5 TWp, until it exists. If the robust case changes the national number substantially, Sections 3.3, 4.1, 4.5 and Fig. 7 will need rewriting, not only filling in.

**M3. The nitrogen-masking argument is asserted, not shown, at national scale.** The interpretation "the large wheat share is a sign of nitrogen masking ... rather than of true shade tolerance" (3.2, 4.2) rests on (a) a Rajasthan pilot with farmer N60 versus recommended N, and (b) one diagnostic run with N stress switched off. Neither appears in the Methods, a table or a figure. Nationally, the contrast that is shown (42% of east-west wheat at the GCR cap versus 0% of south-facing wheat) is a *layout* effect at identical nitrogen, so it does not by itself support the N argument. Please provide: (i) the share of wheat area at the cap, or GCR_max, by calibrated N level (30/60/90/180), which would directly test the hypothesis; (ii) the N-stress-off diagnostic as a figure in the SM; (iii) a mechanism check in DSSAT output, for example the N stress factor or leaf N concentration in open and shaded strips. The statement "Nitrogen supply changed the simulated shade response more than any other input" (4.2) needs a sensitivity analysis across inputs (soil, irrigation trigger, sowing date, cultivar) to be supported.

**M4. The Rajasthan pilot is used as evidence but never described.** Sections 4.2, 4.3, 4.4 and 4.6 quote at least ten numbers from it: 498 cells; RY 1.13/0.90 at GCR 0.3 and 0.86/0.51 at GCR 0.5; RY 0.68 at 70% light with N stress off; chickpea 0.1 to 0.2, groundnut 0.2 to 0.4; feasible wheat GCR raised from 0.3 to 0.5 by east-west/vertical; RY change ±0.03 under SSP2-4.5; legume yields +37% under SSP2-4.5 "most of it from CO₂"; Jodhpur texture test 886/583 kg ha⁻¹ and RY 1.02/0.87. The Methods do not say how the pilot differs from the national run (management, GCR steps, cultivar, soil, calibration), and no table or figure in the SM reports these values. Either add an SM section with the pilot design and a table or figure (the repository has `results/fig_pilot_ry_vs_gcr.pdf` and `results/fig_rajasthan_ry_gcr03.pdf`), or replace the pilot evidence with national-run evidence.

**M5. The PV energy model is not validated, and specific yields look high.** Specific yield at GCR_max is 1,934 kWh kWp⁻¹ (south-facing), 1,785 (east-west) and 1,221 (vertical) at the median cell. From `cell_crop_historical_current.csv.gz` the south-facing value is about 2,090 kWh kWp⁻¹ in Punjab and 1,970 in Rajasthan. Punjab should not exceed Rajasthan, which has the highest irradiance in India. These values are well above what is commonly reported for fixed-tilt PV in India [verify against Global Solar Atlas PVOUT or PVGIS for a few cells]. Possible causes the authors should examine: (a) NEX-GDDP rsds bias. Bias correction targets GMFD/reanalysis radiation, which may be biased high under Indo-Gangetic aerosol and fog in winter. (b) The hourly disaggregation (Section 2.2) scales clear-sky irradiance to the daily total, so every hour of a day has the same clearness index. This removes intra-day cloud variability and can overstate the beam fraction and plane-of-array gain. (c) The bifacial rear gain at 3 m height with albedo 0.2. (d) Losses: 14% plus a 0.96 inverter gives a performance ratio of about 0.8 before temperature. Please validate the energy chain against measured plant data or PVGIS/Global Solar Atlas at several sites, and report the bias. The same disaggregation drives the crop light factor (Eq. 1), so its effect on f_k,d (beam/diffuse split) should also be quantified. The vertical-to-south ratio of 0.63 is also lower than usually reported for east-west vertical bifacial systems at low latitudes [verify]. Please explain it (mutual shading at GCR 0.6, no rear-side albedo gain from crops?).

**M6. The uncertainty is understated.** The only range reported is the five-GCM spread. For the reference period this is close to zero by construction, because all GCMs are bias-corrected to the same observations (45.5 TWp, range 45.5 to 45.9). It says nothing about the uncertainty of the estimate. Sources that dominate are not propagated: crop-model structure and parameters (one cultivar per crop, Yecora Rojo for all of India), the N calibration (pearl millet r = 0.28, MAPE 24%; groundnut over-estimated 2.6 times, r = −0.19), the light model (below-array light over-estimated by +0.147 relative units at CAZRI, Fig. S3), soil (the authors' own texture test changed millet RY at GCR 0.3 from 1.02 to 0.87), and the 0.22 module efficiency. At minimum, add a one-at-a-time sensitivity table (efficiency, soil texture, light-model bias correction, N level, threshold, slope) for the national number. Please also say explicitly in the captions that the GCM range is not a total uncertainty.

**M7. The land base and the "area" in RQ1 and RQ3.** Every eligible hectare is counted however small its GCR_max (5th percentile 0.20, legumes down to 0.05). Land is therefore identical (39.7 Mha) across thresholds, layouts and climates (Table 4 note), and RQ1 ("How much cropland ... can host APV") and RQ3 ("How do the feasible area and density change") cannot be answered as posed: by construction the area never changes. Consider a minimum practical density (for example GCR ≥ 0.2 or a minimum MWp ha⁻¹ from structural cost), report feasible area against it, and rephrase RQ1/RQ3 accordingly. Related points: (a) MapSPAM 2010 harvested area is applied unchanged to 2041 to 2060; (b) rabi area followed by rice or cotton (not simulated) is counted with only the rabi crop tested (acknowledged in 4.6, but the share of such land should be quantified); (c) "eligible" land includes small, fragmented holdings for which a 3 m elevated array is unrealistic. A sentence on holding size [citation needed] would help.

**M8. The demand framing limits the energy relevance.** A technical potential of 48 times national demand is not informative for an energy journal by itself. The 300/500 GWp land-share calculation (0.7%/1.1%) is the more useful framing, but it uses the national mean density. Please consider a supply-curve view: capacity ranked by GCR_max or specific yield, or the best X% of land, showing how much of India's 2030/2047 solar targets could be met on the most yield-tolerant land, and with which crops and layouts. This would answer the policy question in 4.5 directly.

**M9. The yield rule is applied to the 20-year mean RY.** Regulations apply the threshold to observed yields in individual seasons (DIN SPEC 91434 and the French decree compare with a reference plot; the Japanese rule is checked annually). A 20-year mean of 0.80 can include many seasons below 0.66, especially for rainfed millet and groundnut. Please report the probability of RY falling below τ in a given year at GCR_max, or test a rule based on a percentile (for example, RY ≥ τ in 80% of years).

**M10. The calibration is weak where it matters, and its interpretation conflicts with the cited data.** The calibrated wheat N is highest in Punjab and *Gujarat* (180 kg N ha⁻¹), and Haryana is at 90 (Table S6). The cited survey [46] reports the highest wheat rates in Haryana and Punjab. The text says the calibration "nonetheless follows survey data", which Table S6 does not support for Gujarat and Haryana, and the Spearman rank correlation with state N use (0.33 for wheat, 0.26 for millet, from the project's own check) is not reported. Please report it and soften the sentence. In addition, the "recommended-practice case with higher nitrogen" (2.4) uses 120 kg N ha⁻¹ for irrigated wheat (Table S4), which is *lower* than the calibrated 180 in Punjab and Gujarat. The robust case (minimum GCR_max of the two) will therefore mix higher and lower N depending on the state. That must be stated and its effect discussed once the run exists.

**M11. Light-only shading and the choice of crops.** The model changes only daily radiation. Beyond microclimate (acknowledged), two radiation effects matter for the shade response and should at least be discussed. First, the larger diffuse fraction under arrays raises canopy radiation use efficiency, which DSSAT's radiation-use routines do not represent. This probably makes RY conservative. Second, the alternation of sunflecks and shade within a day is lost by using daily strip means. Separately, the meta-analysis cited for the crop ranking [10] reports strong yield losses at low shade for *maize* (C₄) and grain legumes, and tolerance for *C₃* cereals. The model finds pearl millet (C₄) as tolerant as wheat (GCR_max 0.58 east-west). Section 4.3 says this "agrees with" [10]. That is true for the legumes but not for a C₄ cereal, and the discrepancy should be discussed (CERES-Millet RUE response, low N masking at 10 to 30 kg N ha⁻¹).

---

## 3. Minor comments

1. **Japan rule wording is inconsistent.** Introduction: a permit "is in doubt" when yields fall by about 20%. Section 2.5: a 20% drop "voids the permit". The MAFF notice requires that the harvest not fall by more than about 20% of the local average; the consequence is review or non-renewal of the temporary conversion permit. Use one accurate formulation and give the original notice title and number with a URL.
2. **DIN SPEC 91434 land loss.** The 15% limit is for Category II (crops between rows); Category I (elevated) has a 10% limit for the area lost to supports. State that the elevated layouts meet the 10% limit, or check it.
3. **Vertical GCR definition.** For vertical modules, "module area per ground area" is not a coverage ratio, so GCR values are not comparable across layouts (vertical GCR 0.6 means a pitch of 3.3 m for a 2.0 m module). Say this explicitly in 2.2 and in the Fig. 3 caption.
4. **Fig. 2 caption versus Table S1.** Fig. 2 says each pitch is divided into five strips S1 to S5. Table S1 says three mirrored strips for east-west and a pitch mean for vertical. Align them.
5. **Eq. (2).** Give c explicitly for the vertical layout (c = 1 − 0.5/pitch) and say whether RY > 1 values are kept or truncated before interpolation.
6. **Eq. (3)** finds the *first* crossing. Report how often RY is non-monotonic in GCR (RY > 1 at low GCR under low N), since the first crossing then differs from the last.
7. **Eq. (4).** Since A_ov = min(A_r, A_k), one of the two residual terms is always zero. Write the equation in that simpler form or say so. Also define ḡ_r when a cell has both wheat and chickpea (area-weighted across crops of the same season?).
8. **Modules treated as opaque.** Glass-glass bifacial modules transmit some light through cell gaps (typically 5 to 10%) [verify]. Note the assumption's direction of bias.
9. **CO₂ attribution.** "most of it from CO₂" (4.4) needs a fixed-CO₂ run; otherwise write "partly".
10. **ISIMIP3b.** "These are the GCMs of the ISIMIP3b impact-model protocol" needs a citation of the ISIMIP3b protocol or the ISIMIP3BASD bias-adjustment paper [citation needed]. [37] (Meehl et al.) supports only the ECS range.
11. **Specific-yield statistic.** 3.3 gives "area-weighted median over cells" (vertical 1,221), whereas Table 4 implies a capacity-weighted mean of 1,255 (52.7 PWh / 42.0 TWp). State which is used where.
12. **Two averaging methods for GCR_max.** Section 3.2 and Fig. 3 use the area-weighted mean of the GCM-median map (south chickpea 0.19, vertical groundnut 0.32). `headline_numbers.md` pools all GCMs (0.20 and 0.31). Use one definition throughout, including the highlights and the graphical abstract.
13. **Table 3 ratio.** "Simulated / observed" is the area-weighted mean of state ratios. The ratio of area-weighted means differs materially: wheat uncalibrated 0.83 versus 0.92 in the table, groundnut 2.36 versus 2.63. State the definition in the note. Also, for pearl millet calibration *increases* the bias (1.01 → 1.09), because uncalibrated north and south errors cancelled. Say so, so that the 1.01 is not read as a good fit.
14. **Fig. 3.** The caption should say what white cells mean (no simulated crop, area < 1000 ha, or slope-excluded). The colour bar runs to 0.7, but vertical is capped at 0.6, so the top class is empty in panels C, F, I and L. Consider marking the cap.
15. **Fig. 4.** The error bars (GCM range) are almost invisible. Say in the caption that this reflects bias correction (M6). The marker legend "No slope limit / Slope ≤ 10%" is clear.
16. **Fig. 6.** The caption should define the grey class (no change within ±x) and state that it differs from no data. The figure shows widespread decreases in central-Indian wheat and north-western millet that the text does not mention. Section 3.4 should describe the map.
17. **Fig. 7.** The y axis is in TWp, but the densities are in MW ha⁻¹. If TERI's densities are AC (MW) rather than DC (MWp), the comparison mixes units [verify TERI basis]. The dotted line from the last 0.42 diamond to the yield bar carries no label; add "+173%".
18. **Section 4.1, "90% of their simulated area"** conflicts with Fig. 7 and the same section ("the two land rules thus remove 21% of the crop area", 39.7 of 50.0 Mha = 79%). Define the denominator of 90% (unique land area before the slope rule?) or drop it.
19. **Section 4.3, last sentence** ("a layout that keeps more land in use does not necessarily give more energy per hectare") is hard to follow. The point seems to be that vertical rows give more capacity but less energy than south-facing at τ = 0.80 (52.7 versus 66.5 PWh). Say that directly.
20. **Introduction, paragraph 2, grammar.** "Evidence from India ... covers grape farms [11] and the experimental system at Jodhpur ..., and to wheat, for which ..." Make it "and wheat, for which ...".
21. **Introduction, Table 1, "This study" row.** "Irrigated and rainfed; calibrated and recommended N" and "SSP2-4.5" are listed although both are pending. Fine for a draft, but check the row against what is finally reported.
22. **Introduction.** "Studies that design systems under these rules show ..." cites one study [18]. Either add more or write "A study ...".
23. **Section 2.4.** "chickpea was sown 14 days before the local wheat date because the GGCMI pulse calendar describes kharif pulses": give a source for the offset (for example, the ICAR crop calendar) [citation needed].
24. **Section 2.6.** "probably makes RY conservative for rainfed crops in hot regions": Jia et al. [25] also report larger losses in humid regions. State that the bias can go either way outside arid zones.
25. **Units and style.** "MWp per hectare" and "MWp ha⁻¹" both appear; use one. "kWh kWp⁻¹" with "yr⁻¹" is missing in 3.3 and 4.3 (it is given in S6).
26. **Highlights.** Highlight 3 does not state the layout (east-west) and quotes means that include area censored at the GCR limit. Highlight 2 "Cropland on slopes up to 5% could host 45.5 TWp" should say "of four crops". The highlights are within 85 characters (longest 84).
27. **Graphical abstract.** (a) The headline shows the upper bound, see M2. (b) "≈48× India's yearly electricity use": the text uses the electricity *requirement* (CEA LGBR), which is not consumption; use "requirement" or "demand". (c) Panel cover is in % here ("~61% cereals", colour bar 0 to 70%) but GCR is a fraction elsewhere; "61%" and "29%" for cereals and legumes appear nowhere in the text or numbers.json. (d) "2050" labels a 2041 to 2060 mean; write "2041–2060" or "mid-century". (e) The caption is long for a graphical abstract (Elsevier uploads it without a caption); the build comment already notes it must be removed before submission.
28. **Supplementary S3.** Initial mineral N of 0.5 mg NH₄ and 1.0 mg NO₃ per kg soil is very low for Indian irrigated soils, and the low-N masking depends on it. Justify it or test it.
29. **Supplementary S6.** "Using the ratio of seasonal means rather than the mean of seasonal ratios keeps seasons with crop failure from dominating": this weights high-yield years more. Mention this trade-off.
30. **Supplementary Table S6.** The hill states (Himachal Pradesh simulated 3952 versus observed 1413; Uttarakhand 3650 versus 1959) are still over-estimated 2 to 3 times at the lowest level. Report how much eligible area these states contribute after the slope rule.
31. **Supplementary Table S2/Fig. S2.** The main text says the sunlit-fraction MAE is "0.0015"; Table S2 gives 0.0009 to 0.0015. Write "at most 0.0015".

---

## 4. Claims that lack support or a citation

| Location | Claim | Problem |
|---|---|---|
| Intro ¶1 | "more than 160 GW installed by mid-2026 [2]" | [2] is a dynamic MNRE web page; the figure was taken from trade press. Give the dated MNRE report or the figure from the page with its date [verify]. |
| Intro ¶4 | "their authors list crop response as a main limitation" | No specific citation or page; cite [19–21] at this sentence. |
| Intro ¶4 | "The tenfold spread of the Indian estimates thus comes from assumptions about which crops tolerate shade and what power density is acceptable" | Interpretation; only partly shown later (Fig. 7). Point to Section 4.1. |
| Intro ¶5 | "The approach has not been scaled to a national map, mainly because it needs weather, soil, crop calendar and management data ..." | Unsupported reason; soften ("probably because"). |
| 2.2 | "the legumes, whose RY falls fastest" | Based on the undescribed pilot (M4). |
| 2.3 | "These are the GCMs of the ISIMIP3b impact-model protocol" | No citation (minor 10). |
| 2.4 | "Nitrogen input ... controls much of the yield gap of Indian wheat and pearl millet" | Citation needed (yield-gap literature for India). |
| 2.4 | "groundnut was over-estimated by a factor of 2.6, in line with its large yield gap in India" | Citation needed for the groundnut yield gap. |
| 2.4 | Calibrated N "nonetheless follows survey data on fertiliser use" | Contradicted for Gujarat and Haryana by Table S6 (M10); FAO values (106/56, 62/18 kg N ha⁻¹) [verify against [46]; FAO site not reachable from this review]. |
| 2.6 | "which probably makes RY conservative for rainfed crops in hot regions" | Speculative; give [7,25] here. |
| 3.2 | "The large wheat share is a sign of nitrogen masking ... rather than of true shade tolerance" | Not shown at national scale (M3). |
| 4.1 | "What will limit deployment is siting near substations, grid capacity, finance and the choice of crop" | No citation. |
| 4.2 | "Nitrogen supply changed the simulated shade response more than any other input" | No cross-input sensitivity shown (M3). |
| 4.2 | All Rajasthan pilot numbers (498 cells, RY 1.13/0.90, 0.86/0.51, RY 0.68 at 70% light) | Not in any table, figure or method (M4). |
| 4.2 | "A farmer who receives APV lease income may apply more fertiliser" | Speculative; cite or mark as hypothesis. |
| 4.3 | Pilot chickpea 0.1–0.2, groundnut 0.2–0.4; wheat GCR "raised ... from 0.3 to 0.5" | Not in any table or figure (M4). |
| 4.3 | "the legume usually sets the density" | Not quantified; report the share of overlap area where the legume limits. |
| 4.4 | Pilot legume yields +37% under SSP2-4.5 "most of it from CO₂" | No fixed-CO₂ run (minor 9). |
| 4.4 | SSP5-8.5 open-field yield +37% chickpea, +24% groundnut; RY at GCR 0.3 changed < 0.01 | Not in numbers.json or any table; add an SM table. |
| 4.5 | "The scheme sets no rule for the crop below" | Needs the guideline clause or a citation ([33] has no URL). |
| 4.5 | "A paired open plot is the norm in Europe" | Cite [15,17] here. |
| 4.6 | Jodhpur texture test 886/583 kg ha⁻¹, RY 1.02/0.87 | Not in any table or figure (M4). |
| 4.6 | "[57] ... little change in mean crop temperature under panels in a temperate climate" | Marrou et al. worked at Montpellier, a Mediterranean climate; "temperate" is loose. |

---

## 5. Numbers in the text that do not match the tables, figures or numbers.json

Everything else that was checked matches, within rounding: Table 4 against `headline_numbers.md`; the 22–38× (TERI) and 3.3× (Fraunhofer) multiples; 17–30 TW; 1.5–2.7×; GCR 0.19–0.34; 48×; 0.26/0.44 Mha and 0.7/1.1%; waterfall 37.5/21.0/−10%/−12%/29.8/+53%/+173%; state values 14.3/7.7/6.6; 42/1/6/5% and 75/86% at the cap; 62% of vertical area above 0.6; legumes 25% of area and 13% of capacity; cereal median 0.65; P5–P95 0.20–0.70; Table 3 against `validation_before_after.csv` (r, MAPE, mean of ratios); Table S7 factors.

| # | Location | Text | Source | Issue |
|---|---|---|---|---|
| N1 | 3.3 | "Without the cap, vertical rows would give 47 TWp (11% more)" | 42.02 capped, 47.19 uncapped (`headline_numbers.md`) | 47.19/42.02 = +12.3%. The 11% is the reduction from the uncapped value (as 4.3 correctly says). Write "12% more" or "the cap removes 11%". |
| N2 | 4.1 | "39.7 Mha of eligible cropland, 90% of their simulated area" | `recon.*`: 50.0 Mha crop area → 39.7 Mha (−21%); `hist.land_share` = 90 | The 90% and "remove 21%" in the same section use different denominators; undefined. |
| N3 | 3.2 / Fig. 3 vs `headline_numbers.md` | South chickpea 0.19; vertical groundnut 0.32 | Pooled-GCM table: 0.20 and 0.31 | Two averaging methods (minor 12). |
| N4 | 3.3 | Specific yield vertical "1,221" | Table 4: 52.7 PWh / 42.0 TWp = 1,255; `vertical.t80.sy` = 1,255 | Different statistic, not stated (minor 11). |
| N5 | 3.4, 4.4 | "−1% (GCM range −6% to 0%)" | SSP5-8.5 east-west capacity 44.9 (43.0–46.0) vs 45.5 | Against the historical median the range is −5.5% to +1.1%. The quoted range must be per-GCM paired changes; say so. "0%" hides a positive change for one GCM. |
| N6 | 3.4 | "they agree on 57% of the land" | `ssp585.agree4_share` = 57 | The key suggests 4 of 5 GCMs agree on sign; the text defines neither who agrees nor on what. |
| N7 | Table 3 | Wheat uncalibrated sim/obs 0.92; groundnut 2.63 | Ratio of area-weighted means: 0.83 and 2.36 | Definition not stated (minor 13). 2.4 quotes "factor of 2.6", 4.6 "2.6". |
| N8 | Graphical abstract | "~61% cereals", "~29% legumes" | Not in numbers.json (`ga.*` has only per-crop values) or the text | Cannot be checked against the manuscript. |
| N9 | Graphical abstract / highlights | "45.5 TWp" as headline | Text: the robust case is the headline | Consistency (M2). |
| N10 | Intro ¶7 | "about 51 Mha ... wheat (28), pearl millet (9), chickpea (8), groundnut (5)" | These sum to 50; Table 2 implies 28.5 + 9.1 + 8.3 + 5.4 = 51.3 | Rounding. Give one decimal (28.5, 9.1, 8.3, 5.4), or the parts will not add up. |
| N11 | Fig. S2 caption vs 2.2 | MAE 0.0009–0.0015 vs "0.0015" | Table S2 | Minor 31. |

Note for the authors: `india_combined_*.csv` stores values to five significant figures (for example 4.5500e+07 MWp), so the east-west median of exactly 45,500 GWp is a rounding artefact of the file, not a placeholder. Write the tables with full precision.

---

## 6. Reference problems

**Crossref check.** All 44 Crossref DOIs in the manuscript and SM resolve, and the first author, year, journal, volume and pages match the reference list. This includes the recent ones: Ademollo 2026 (Appl Energy 405:127225), Arendarczyk 2026 (Appl Energy 426:128628), Jia 2026 (PNAS 123:e2514380123), Mehta & Betz 2026 (ESD 91:101915), Campana 2025 (Nat Rev Clean Technol 1:801–21) and Santra 2021 (Biosyst Eng 209:74–93, which settles the earlier [verify]). The two OSTI DOIs (10.2172/1158421 Dobos 2014; 10.2172/1219777 Lopez 2012) resolve with matching titles.

**Problems:**
1. **Missing DOI or URL** (required by the authors' own rules and by good practice): [1] India NDC 2022 (UNFCCC NDC registry URL); [3] PLFS Annual Report 2023–24 (MoSPI URL); [15] DIN SPEC 91434 (Beuth/DIN Media URL; the DIN SPEC has a free download); [16] MAFF notice of 31 March 2013 (give the notice number and the MAFF URL; the title is a translation and should be marked as such); [17] Décret n° 2024-318 (Légifrance URL, NOR code); [33] PM-KUSUM guidelines (amended) 2024 (MNRE URL and the exact amendment date); SM [11] IEC 61724-1:2021 (IEC webstore URL).
2. **[45] / SM [9] ICRISAT DLD.** No year or version is given. The DOI 10.21421/D2/XFB1BZ is a DataCite DOI; doi.org resolves it (HTTP 302), but its metadata could not be checked from this session (DataCite blocked). Add the year and version accessed. The SM text says "District Level Database" while the reference title says "District Level Data (DLD) and Dashboard"; use one name.
3. **[48] / SM [10] Copernicus DEM.** The reference gives 2021; Crossref lists the DOI as issued 2022, with ESA and Airbus as creators. Align the year and creators with the DOI record.
4. **[52] CEA LGBR 2026-27.** The URL ends in `lang=hi` (the Hindi page); use the English page or the PDF. The value 1,707,493 MU was supplied by the author and could not be checked from this session [verify against the PDF].
5. **[2] MNRE physical progress** and **[56] PM-KUSUM FAQ** are live web pages; "accessed October 2026" needs a day. The 160 GW figure should be checked on the page itself [verify].
6. **[19] Fraunhofer ISE/EY/CSTEP 2024** and **[20] TERI 2026.** The URLs could not be reached from this session (proxy 403) and must be checked by the authors [verify]. The TERI authors (Yadav, Tiwari, Malik, Dortch) and the year should be confirmed on the brief.
7. **[46] FAO 2005 "Fertilizer use by crop in India"** and **[41] FAO-56**: URLs not reachable from this session [verify]. The specific numbers quoted from [46] (106/56, 62/18 kg N ha⁻¹) should be checked against the table they come from.
8. **[40] DSSAT 4.8.** The software citation is acceptable. Applied Energy prefers a version and date of release, so give "Version 4.8.0.027" or similar.
9. **[10] Laub et al. 2022.** The meta-analysis is restricted to temperate and subtropical studies, and it finds maize (C₄) sensitive and C₃ cereals tolerant. Section 4.3 cites it in support of pearl millet (C₄) tolerance (M11).
10. **[58] Weselek et al. 2021** is cited for "yield gains in hot, dry seasons". The paper is from a temperate site in Germany; the gains were in the dry 2018 season. Say so, so that readers do not take it as evidence from a hot climate.
11. **[57] Marrou et al. 2013**: "temperate climate" should be "Mediterranean" (Montpellier).
12. **Missing references:** ISIMIP3b protocol or bias adjustment (minor 10); a source for the chickpea sowing offset (minor 23); Indian yield-gap literature for wheat/millet N and groundnut (Section 4 table); a source on Indian landholding size (M7).

---

## 7. Em dashes

None. No em dash (U+2014) or other long dash (U+2015, U+2012) was found in the built manuscript, the Supplementary, `highlights.txt` or the graphical-abstract caption. En dashes are used correctly for ranges.

---

## 8. Recommendation

**Major revision**, and in its current state I would recommend that the editor return it before review, because it is incomplete (M1).

The core idea, a yield-constrained national APV potential from coupled light and crop models with an explicit link between nitrogen management and the shade response, is novel and suited to Applied Energy. For the paper to be publishable, the authors need to:
1. complete the manuscript (abstract, keywords, conclusions, Section 3.4);
2. make the robust case the headline everywhere once it is available, and show the nitrogen-masking mechanism with national data rather than the undescribed pilot;
3. validate the PV energy chain and explain the high specific yields;
4. widen the uncertainty analysis beyond the GCM spread;
5. reframe RQ1/RQ3 so that "feasible area" can change, and test a per-year yield rule;
6. fix the number inconsistencies in Section 5 and the reference gaps in Section 6.
