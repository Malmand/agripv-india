// Supplementary Material for the Methodology
const L = require("./lib.js");
const { cite, P, PF, H1, H2, R, sub, frac, sum, EQ, TABLE, FIG, FIGAUTO, refsList, save, Paragraph, TextRun, FONT, fill } = L;
L.resetCounters();
L.setPrefix("S", "S", "S");
const body = [];
const add = (...x) => x.flat().forEach(e => body.push(e));

add(new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: "Supporting Information for Yield-Constrained Agrivoltaic Potential of India Under Current and Mid-Century Climate", bold: true, size: 32, font: FONT })] }));
add(P("Yield-constrained agrivoltaic potential of India under current and mid-century climate. Texts S1 to S7 give the detail behind Section 2 of the main text, Text S8 shows the validation of the crop and light models, and Text S9 describes the Rajasthan pilot and the Jodhpur soil test that the Discussion cites."));

// S1
add(H1("Text S1. Layout geometry and light model"));
add(TABLE("Geometry of the agrivoltaic layouts.",
  ["Layout", "Row axis", "Module tilt / azimuth", "Module width per row", "Lower edge height", "Uncultivated strip", "Ground strips simulated"],
  [["South-facing, elevated", "East-west", "25° / 180°", "2.0 m", "3.0 m", "None", "5"],
   ["East-west ridge, elevated", "North-south", "10° / 90° and 270°", "2 × 2.0 m", "3.0 m", "None", "3, mirrored to 5"],
   ["Vertical bifacial", "North-south", "90° / 90° (bifacial)", "2.0 m", "0.8 m", "0.5 m", "Pitch mean"]],
  [1750, 1100, 1500, 1300, 1150, 1150, 1076],
  "Pitch = module width per row / GCR. Simulated GCR: 0.1–0.5 in steps of 0.1 for all crops, plus 0.6 and 0.7 for wheat and pearl millet and 0.05 for chickpea and groundnut."));
add(P(`For a ground point, beam transmission is the fraction of rays at the projected solar zenith angle that pass between the modules of 81 rows centred on the point, and the sky view factor is the visible fraction of an isotropic sky. Both were evaluated at 200 points across the cultivated part of the pitch and averaged over five strips. The east-west ridge is symmetric about the row axis, so three strips were simulated and mirrored. For vertical rows the strip factors were averaged over the pitch, because the morning and afternoon shade sweeps the whole inter-row space. Hourly irradiance used local solar days in Indian Standard Time and the pvlib Linke turbidity climatology.`));
add(TABLE("Light model against the analytical two-dimensional functions in pvlib for single-segment rows (26.4°N, 73.1°E; hourly sun positions of 2010 with solar zenith below 85°).",
  ["Layout", "GCR", "Mean sky view factor, this model", "Mean sky view factor, pvlib", "Largest pointwise difference", "Hourly sunlit fraction, MAE"],
  [["South-facing", "0.1", "0.9008", "0.9009", "0.009", "0.0013"], ["South-facing", "0.2", "0.8040", "0.8037", "0.009", "0.0014"],
   ["South-facing", "0.3", "0.7089", "0.7086", "0.012", "0.0015"], ["South-facing", "0.4", "0.6163", "0.6162", "0.017", "0.0014"],
   ["South-facing", "0.5", "0.5274", "0.5273", "0.016", "0.0011"], ["Vertical", "0.1", "0.9047", "0.9050", "0.005", "0.0014"],
   ["Vertical", "0.2", "0.8202", "0.8198", "0.007", "0.0012"], ["Vertical", "0.3", "0.7435", "0.7440", "0.009", "0.0011"],
   ["Vertical", "0.4", "0.6768", "0.6770", "0.008", "0.0011"], ["Vertical", "0.5", "0.6182", "0.6180", "0.011", "0.0009"]],
  [1500, 700, 1700, 1600, 1700, 1826],
  "The east-west ridge has two segments per row and no direct pvlib counterpart; it uses the same ray-tracing code."));

// S2
add(H1("Text S2. Climate data processing"));
add(P(`NEX-GDDP-CMIP6 ${cite("thrasher")} variables were converted as follows: shortwave radiation from W m^−2^ to MJ m^−2^ d^−1^; precipitation from kg m^−2^ s^−1^ to mm d^−1^; dew point from mean daily temperature and relative humidity with the Magnus formula, capped at the daily minimum temperature; and wind speed from 10 m to 2 m with the FAO-56 logarithmic profile ${cite("allen")}. Model calendars of 360 or 365 days were mapped onto the real calendar by nearest-day resampling. The climate grid coincides with the simulation grid, so no spatial interpolation was needed.`));
add(TABLE("Climate periods and CO~2~ concentration.",
  ["Period", "Years", "Scenario", "CO~2~ (ppm)", "Climate models"],
  [["Reference", "1995–2014", "Historical", "378", "GFDL-ESM4, IPSL-CM6A-LR, MPI-ESM1-2-HR, MRI-ESM2-0, UKESM1-0-LL"],
   ["Mid-century", "2041–2060", "SSP2-4.5", "507", "Same five"], ["Mid-century", "2041–2060", "SSP5-8.5", "563", "Same five"]],
  [1300, 1100, 1200, 1100, 4326], `Period-mean CO~2~ ${cite("meinshausen")}, constant within each simulation.`));

// S3
add(H1("Text S3. Crop model set-up"));
add(P(`DSSAT 4.8 ${cite("jones", "hoogenboom")} was run through the DSSATTools Python interface. Initial soil water was 50% of plant-available water and initial mineral nitrogen was low (0.5 mg NH~4~ and 1.0 mg NO~3~ per kg soil), and crops were harvested at maturity. Nitrogen was applied as urea incorporated at 5 cm; irrigated wheat received two equal doses at sowing and 30 days after sowing. Rainfed pearl millet and rainfed kharif groundnut were sown automatically in a ±15-day window around the calendar date when soil water in the top 30 cm was 40–100% of plant-available water and soil temperature was 10–40 °C. Soil profiles used the six SoilGrids 2.0 depths ${cite("poggio")}, sampled at the cell centre; lower limit, drained upper limit, saturation and saturated conductivity came from the Saxton and Rawls functions ${cite("saxton")}. The 108 cells (3.6%) without SoilGrids data at the centre took the profile of the nearest valid cell.`));
add(TABLE("Management scenarios.",
  ["Scenario", "Wheat N (kg ha^−1^)", "Pearl millet N", "Chickpea, groundnut N", "Irrigation trigger (share of plant-available water)", "Use"],
  [["Calibrated (main)", "30–180 by state", "10–30 by state", "0", "50% (wheat, millet); 20% (legumes)", "All periods"],
   ["Recommended", "120 irrigated (60 + 60), 60 rainfed", "40", "20", "50%", "Reference period, sensitivity"]],
  [1500, 1800, 1150, 1300, 2050, 1226], "Triggers apply to irrigated systems, in the top 30 cm of soil."));
add(TABLE("Planting settings.",
  ["Crop", "Plants m^−2^", "Row spacing (cm)", "Sowing depth (cm)", "Sowing rule"],
  [["Wheat", "225", "22.5", "5", "GGCMI spring wheat date"], ["Chickpea", "33", "30", "5", "Wheat date − 14 d"],
   ["Pearl millet", "11", "45", "5", "GGCMI millet date; rainfed automatic"], ["Groundnut", "33", "30", "5", "GGCMI groundnut date; rainfed kharif automatic"]],
  [1600, 1300, 1600, 1600, 2926], `Sowing dates from the GGCMI Phase 3 crop calendar ${cite("jagermeyr")}, irrigated and rainfed calendars separately.`));

// S4
add(H1("Text S4. Nitrogen calibration"));
add(P(`Simulated open-field cell yields (mean of GFDL-ESM4 and MPI-ESM1-2-HR) were combined into state means weighted by irrigated and rainfed share and by harvested area, and compared with the 1995–2014 mean state yield from the ICRISAT District Level Database ${cite("icrisat")}. States without enough observed area used the area-weighted median of the calibrated levels. The hill states remained over-estimated at the lowest level; most of their cropland is removed by the slope rule.`));
add(TABLE("Calibrated nitrogen level and open-field state yield, reference period.",
  ["State", "Crop", "N (kg ha^−1^)", "Observed (kg ha^−1^)", "Simulated (kg ha^−1^)"],
  [["Punjab", "Wheat", "180", "4411", "4656"], ["Gujarat", "Wheat", "180", "2553", "2854"], ["Haryana", "Wheat", "90", "4172", "3739"],
   ["Rajasthan", "Wheat", "90", "2898", "3362"], ["Karnataka", "Wheat", "90", "852", "876"], ["Uttar Pradesh", "Wheat", "60", "2761", "2652"],
   ["Madhya Pradesh", "Wheat", "60", "1935", "1623"], ["Bihar", "Wheat", "30", "2126", "2026"], ["Maharashtra", "Wheat", "30", "1415", "1351"],
   ["West Bengal", "Wheat", "30", "2430", "2989"], ["Himachal Pradesh", "Wheat", "30", "1413", "3952"], ["Uttarakhand", "Wheat", "30", "1959", "3650"],
   ["Chhattisgarh", "Wheat", "30", "1067", "1433"], ["Assam", "Wheat", "30", "1182", "1774"], ["Jharkhand", "Wheat", "30", "1421", "2281"],
   ["Other states", "Wheat", "60", "–", "–"], ["Gujarat", "Pearl millet", "30", "1355", "1129"], ["Haryana", "Pearl millet", "30", "1443", "1328"],
   ["Madhya Pradesh", "Pearl millet", "30", "1406", "1173"], ["Uttar Pradesh", "Pearl millet", "30", "1513", "1336"],
   ["Rajasthan", "Pearl millet", "10", "689", "637"], ["Maharashtra", "Pearl millet", "10", "758", "1183"],
   ["Karnataka", "Pearl millet", "10", "723", "2023"], ["Tamil Nadu", "Pearl millet", "10", "1492", "2589"],
   ["Andhra Pradesh", "Pearl millet", "10", "1277", "2059"], ["Other states", "Pearl millet", "10", "–", "–"]],
  [2400, 1600, 1400, 1800, 1826], "Level 10 kg N ha^−1^ was tested for pearl millet only."));

// S5
add(H1("Text S5. Legume yield-gap factors"));
add(TABLE("Observed and simulated open-field legume yields and yield-gap factors (applied to absolute production only).",
  ["State", "Crop", "Observed (kg ha^−1^)", "Simulated (kg ha^−1^)", "Factor (obs/sim)"],
  [["Madhya Pradesh", "Chickpea", "925", "854", "1.08"], ["Rajasthan", "Chickpea", "725", "522", "1.39"], ["Maharashtra", "Chickpea", "677", "436", "1.55"],
   ["Uttar Pradesh", "Chickpea", "858", "1235", "0.70"], ["Karnataka", "Chickpea", "550", "1053", "0.52"], ["Andhra Pradesh", "Chickpea", "1096", "1292", "0.85"],
   ["Chhattisgarh", "Chickpea", "746", "1089", "0.68"], ["Haryana", "Chickpea", "810", "1169", "0.69"], ["Gujarat", "Chickpea", "855", "1191", "0.72"],
   ["Telangana", "Chickpea", "1052", "733", "1.44"], ["Bihar", "Chickpea", "1014", "820", "1.24"], ["Gujarat", "Groundnut", "1313", "2640", "0.50"],
   ["Andhra Pradesh", "Groundnut", "754", "2352", "0.32"], ["Karnataka", "Groundnut", "721", "2988", "0.24"], ["Tamil Nadu", "Groundnut", "1979", "2654", "0.74"],
   ["Maharashtra", "Groundnut", "1122", "3806", "0.30"], ["Rajasthan", "Groundnut", "1387", "2084", "0.67"], ["Odisha", "Groundnut", "1488", "3444", "0.43"],
   ["Telangana", "Groundnut", "1284", "1246", "1.03"], ["Madhya Pradesh", "Groundnut", "1176", "3665", "0.32"], ["Uttar Pradesh", "Groundnut", "813", "3676", "0.22"]],
  [2400, 1500, 1700, 1700, 1726], "States with at least 50 kha, ordered by area. Area-weighted mean factor: chickpea 1.09, groundnut 0.44."));

// S6
add(H1("Text S6. Aggregation, eligible land and energy"));
add(P(`Irrigated and rainfed systems of a crop were combined by production, in the same way as gridded crop-model outputs are aggregated across management systems ${cite("jagermeyr")}:`));
add(EQ([sub("RY", "crop"), R(" = "), frac([sum("w", [sub("a", "w"), R(" "), sub("Ȳ", "0,w"), R(" "), sub("RY", "w")])], [sum("w", [sub("a", "w"), R(" "), sub("Ȳ", "0,w")])])]));
add(P(`where _a_~w~ is the share of the crop's area under water regime _w_ and Ȳ~0,w~ and RY~w~ are the open-field yield and RY of that regime. Using the ratio of seasonal means rather than the mean of seasonal ratios in RY keeps seasons with crop failure from dominating. The eligible area of a crop is`));
add(EQ([sub("A", "e"), R(" = "), sub("A", "c"), R(" "), sub("φ", "S")]));
add(P(`where _A_~c~ is its harvested area (ha) and φ~S~ the share of the cell with slope ≤ _S_ % (S = 5 in the main case), computed from GLO-90 ${cite("copdem")} by finite differences. The rule assumes that cropland is spread evenly over the slope classes of a cell. For single-crop results, capacity is η _I_~STC~ _A_~e~ GCR~max~. Annual energy is`));
add(EQ([R("E = P "), sub("Y", "sp"), R("("), sub("GCR", "max"), R(")")]));
add(P(`where _Y_~sp~ is the specific yield, the final yield of IEC 61724-1 ${cite("iec61724")} (kWh kW~p~^−1^ yr^−1^), of the cell and layout, interpolated at GCR~max~. It was computed with pvlib ${cite("pvlib")} from the same hourly irradiance as the crop simulations, for every fifth year of each GCM (twenty model-years per period). Hourly air temperature followed a cosine between the daily minimum at 06:00 and maximum at 15:00.`));
add(TABLE("Parameters of the PV energy model.",
  ["Parameter", "Value"],
  [["Module", "Bifacial glass-glass, n-type"], ["Efficiency at STC", "22%"], ["Bifaciality", "0.80"],
   ["Temperature coefficient of power", "−0.30% K^−1^"], ["Cell temperature", `Faiman model ${cite("faiman")}, pvlib default coefficients, 2 m wind`],
   ["Irradiance on modules", "pvlib infinite sheds, isotropic sky, front and rear"], ["Ground albedo", "0.20"],
   ["DC model", `PVWatts ${cite("dobos")}`], ["System losses", "14%"], ["Inverter efficiency", "96%"]],
  [3600, 5426], null));

// S7
add(H1("Text S7. Implementation and quality control"));
add(P(`The workflow was written in Python. Crop simulations, one task per cell, GCM, period and management case, ran on a 12-core cloud virtual machine. Each task wrote its results only on completion, so an interrupted run resumed without duplicates, and DSSAT runs that stopped with an error were retried up to three times. A report every 20 minutes checked three rules and stopped the run on a breach: failed tasks above 2%; median open-field yield of a crop outside a plausible range for India (wheat 800–7000, chickpea 200–3000, groundnut 200–5000 and pearl millet 150–4500 kg ha^−1^, applied after a full pass over all cells); and more than 5% of irrigated open-field seasons with zero yield.`));

// S8
add(H1("Text S8. Validation figures"));
add(P(`Figs. S1 to S3 compare the crop model with observed state yields and the light model with an analytical reference and with field measurements. Fig. S1 uses the states with at least 50 kha of the crop. Fig. S2 repeats Table S2 in graphical form. Fig. S3 uses the PPFD measured by Santra et al. ${cite("santra")} at the 105 kW~p~ agrivoltaic plant of ICAR-CAZRI, Jodhpur, on clear days of 20 to 24 December 2018, 10 cm above the ground. Rows run east-west, modules face south at 26° tilt with the lower edge at 0.5 m, and the three blocks differ in the number of module rows (one, one and a half, two and a half) and in the interspace (2.95, 5.55 and 8.90 m). Measured and modelled values are both relative to the unshaded interspace, which removes the conversion between irradiance and photon flux.`));
add(FIG("../../results/figures/figS1_yield_calibration.png", 460, 442, "State mean open-field yields, simulated against observed (ICRISAT District Level Database, 1995–2014), before and after nitrogen calibration. (A, B) Wheat. (C, D) Pearl millet. Before calibration all states used farmer nitrogen (wheat 60, pearl millet 10 kg N ha^−1^); after calibration each state used its calibrated level (Table S6). Simulated yields are the mean of GFDL-ESM4 and MPI-ESM1-2-HR. Marker area is proportional to observed harvested area; only states with at least 50 kha are shown. The dashed line is 1:1. r is the Pearson correlation and MAPE the mean absolute percentage error weighted by harvested area. Pearl millet in the southern states (Karnataka, Tamil Nadu, Andhra Pradesh) stays over-predicted even at 10 kg N ha^−1^."));
add(FIG("../../results/figures/figS2_light_vs_pvlib.png", 600, 289, "Light model against the analytical view-factor functions of pvlib for single-segment rows at 26.4°N, 73.1°E (hourly sun positions of 2010, solar zenith below 85°). (A) Sky view factor of the ground averaged across the pitch. (B) Sunlit fraction of the ground averaged over all daylight hours. Lines are this model and open markers pvlib, for the south-facing layout (tilt 25°) and the vertical bifacial layout. The largest pointwise difference in sky view factor is 0.017 and the mean absolute error of the hourly sunlit fraction is 0.0009 to 0.0015."));
add(FIG("../../results/figures/figS3_light_vs_cazri.png", 600, 328, `Modelled relative irradiance against measured relative photosynthetic photon flux density at the Central Arid Zone Research Institute, Jodhpur ${cite("santra")}, by block (colour) and time window (marker). (A) Whole system, averaged over the row pitch: bias −0.044, root-mean-square error 0.053. (B) Ground below the photovoltaic array: bias +0.147, root-mean-square error 0.199. The model used clear-sky beam and diffuse irradiance with a broadband diffuse fraction. The dashed line is 1:1. The model reproduces the pitch-mean light but over-estimates the light directly below the modules, most strongly under the single-row Block 1. In late December the noon solar elevation at Jodhpur is about 40°, so below-array light is over-estimated for low winter sun: modelled beam reaches the ground under the low modules more often than measured, and the model includes neither frames, supports nor reflection from the ground and the array. The crop model uses light averaged over strips that span the cultivated pitch, which corresponds to panel A.`));

// S9
add(H1("Text S9. Rajasthan pilot and Jodhpur soil test"));
add(PF(`Before the national run, the light and crop models were tested in a pilot over Rajasthan, the state with the largest pearl millet area and a large wheat and chickpea area. The pilot used {pilot.n_cells} cells of the same 0.25° grid, the same five NEX-GDDP-CMIP6 GCMs ${cite("thrasher")}, SoilGrids 2.0 profiles ${cite("poggio")}, cultivars and light model as the national run, for 1995–2014 (378 ppm CO~2~) and 2041–2060 under SSP2-4.5 (507 ppm). It differed from the national run in four ways: nitrogen was not calibrated, and two management cases were run instead (Table S9); sowing dates were fixed (wheat 15 November, chickpea 1 November, groundnut 25 June) except for rainfed pearl millet, which was sown automatically in July; GCR was simulated from 0.1 to 0.5 only, in steps of 0.1; and GCR~max~ was taken as the largest simulated GCR whose RY met the threshold, without interpolation. Chickpea and groundnut were run as rainfed and irrigated systems and, for chickpea, also as their area-weighted mix. The SSP2-4.5 runs used farmer management only. RY was computed per cell and GCM as in the main text (Eq. (2)) and is reported as the median over GCMs and then over cells.`));
add(TABLE("Management cases of the Rajasthan pilot.",
  ["Case", "Wheat", "Chickpea, groundnut", "Pearl millet"],
  [["Farmer", "60 kg N ha^−1^ (30 at sowing, 30 at 30 d); irrigated at 50% of plant-available water", "No N; rainfed, and irrigated at 20% of plant-available water", "10 kg N ha^−1^; rainfed, automatic sowing in July"],
   ["Recommended", "120 kg N ha^−1^ (60 + 60); irrigated at 50%", "20 kg N ha^−1^; irrigated at 50%", "40 kg N ha^−1^; rainfed, automatic sowing in July"]],
  [1500, 2700, 2600, 2226], "Irrigation triggers refer to the top 30 cm of soil."));
add(PF(`Table S10 gives the pilot values that the Discussion uses. The soil test was run for the single cell that contains the ICAR-CAZRI experimental site at Jodhpur (26.375°N, 73.125°E), with NASA POWER daily weather for 1995–2014 ${cite("nasapower")}, FAO-56 Penman-Monteith evapotranspiration ${cite("allen")} and the same light model. Rainfed pearl millet received 40 kg N ha^−1^ and was sown automatically in July. The SoilGrids 2.0 profile of the cell was compared with a generic loamy sand profile, to test how strongly soil texture changes open-field yield and RY.`));
const pv = (k) => fill(`{${k}}`);
add(TABLE("Rajasthan pilot and Jodhpur soil test: values cited in the main text.",
  ["Quantity", "Case", "Value"],
  [["Wheat RY, south-facing, GCR 0.3", "Farmer / recommended", `${pv("pilot.wheat.south.farmer.g3")} / ${pv("pilot.wheat.south.recommended.g3")}`],
   ["Wheat RY, south-facing, GCR 0.5", "Farmer / recommended", `${pv("pilot.wheat.south.farmer.g5")} / ${pv("pilot.wheat.south.recommended.g5")}`],
   ["Pearl millet RY, south-facing, GCR 0.5", "Farmer / recommended", `${pv("pilot.pearl_millet.south.farmer.g5")} / ${pv("pilot.pearl_millet.south.recommended.g5")}`],
   ["GCR~max~ at RY ≥ 0.80, chickpea systems", "Farmer, all layouts", `${pv("pilot.chickpea.gcr_lo")}–${pv("pilot.chickpea.gcr_hi")}`],
   ["GCR~max~ at RY ≥ 0.80, groundnut systems", "Farmer, all layouts", `${pv("pilot.groundnut.gcr_lo")}–${pv("pilot.groundnut.gcr_hi")}`],
   ["GCR~max~ at RY ≥ 0.80, wheat and pearl millet", "Farmer, all layouts", `${pv("pilot.wheat.gcr_lo")} (largest simulated)`],
   ["GCR~max~ at RY ≥ 0.80, wheat", "Recommended; south / east-west / vertical", `${pv("pilot.wheat.rec.south.gcr")} / ${pv("pilot.wheat.rec.ew.gcr")} / ${pv("pilot.wheat.rec.vertical.gcr")}`],
   ["Largest median change in RY, SSP2-4.5 vs 1995–2014", "Farmer, any system, layout, GCR", pv("pilot.ssp245_ry_change_max")],
   ["Jodhpur open-field pearl millet yield (kg ha^−1^)", "SoilGrids / loamy sand", `${pv("jodhpur.soilgrids.millet_open")} / ${pv("jodhpur.loamy_sand.millet_open")}`],
   ["Jodhpur pearl millet RY, south-facing, GCR 0.3", "SoilGrids / loamy sand", `${pv("jodhpur.soilgrids.millet_ry_s03")} / ${pv("jodhpur.loamy_sand.millet_ry_s03")}`]],
  [3800, 2900, 2326], "Pilot: median over five GCMs and then over cells. Jodhpur: mean over the simulated seasons."));
// Table S10 sources: runs/rajasthan_final, results/soilgrids_F, results/loamy_sand_F (src/make_numbers.py pilot_numbers)

if (fill.has("robust.change_pct")) {
  add(H1("Text S10. Results with calibrated nitrogen alone"));
  add(PF(`The main text reports the robust nitrogen case. Figs. S4 and S5 show the same results with calibrated nitrogen alone, the upper bound of Section 3.4 (east-west layout, τ = 0.80: {main.cap_twp_m} TWp against {robust.ew.t80.cap_twp_m} TWp in the robust case).`));
  add(FIGAUTO("../../results/figures/fig_india_gcrmax_historical_current_thr80.png", 600,
    "As Fig. 3, with calibrated nitrogen alone (upper bound): largest ground coverage ratio  that keeps relative yield at or above 0.80, by crop (columns) and layout (rows), 1995–2014; vertical rows capped at 0.6. Cell values are the median over five climate models, interpolated for display; the number in each panel is the area-weighted mean with the range of the models. Boundaries: DataMeet India community, States/Admin2 (CC BY 4.0)."));
  add(FIGAUTO("../../results/figures/fig_india_states_historical_current_thr80.png", 450,
    "As Fig. 6, with calibrated nitrogen alone (upper bound): capacity of the leading states at relative yield ≥ 0.80 by layout, 1995–2014, slope ≤ 5%, vertical rows capped at 0.6. Bars are the five-model median and error bars the range of the models."));
}
add(H1("Text S11. Land-supply curve"));
add(PF(`Fig. S6 shows how much cropland a given APV capacity needs if the cells with the highest yield-constrained power density are used first (east-west layout, RY ≥ 0.80, slope ≤ 5%${fill.has("robust.change_pct") ? ", robust nitrogen" : ""}). For each GCM the cells are sorted by capacity per hectare and capacity and land are accumulated; the curve is the five-GCM median.{? At this order, 300 GWp needs {supply.gw300_mha} Mha and 500 GWp {supply.gw500_mha} Mha, against {frame.gw300.land_mha} and {frame.gw500.land_mha} Mha at the national mean density.?}`));
add(FIGAUTO("../../results/figures/figS6_supply_curve.png", 600,
  "Cropland needed for a given agrivoltaic capacity when the densest cells are used first, east-west layout, relative yield ≥ 0.80, slope ≤ 5%, 1995–2014. (A) Full range; (B) first 1000 gigawatts peak. Solid line: five-model median; band: range of the models; dashed line: land at the national mean density."));
if (fill.has("rad.k_north_pct")) {
  add(H1("Text S12. Radiation correction for PV energy"));
  add(PF(`NEX-GDDP-CMIP6 shortwave radiation was compared, per 0.25° cell and calendar month, with the 2001–2020 NASA POWER all-sky surface shortwave climatology ${cite("nasapower")}, queried on a 0.5° lattice. The ratio of the two (bounded to 0.5–1.3) rescales the daily radiation before the hourly disaggregation in the PV energy model; mid-century periods use the same factors (linear scaling ${cite("teutschbein")}). The correction changes radiation by {rad.k_nat_pct}% on average over the eligible cropland, {rad.k_north_pct}% in the Indo-Gangetic plain (24–31°N, 74–88°E) and {rad.k_south_pct}% south of 16°N, and national specific yield at GCR 0.3 by {rad.sy_change_pct}%. The crop model runs keep the original radiation{?; a test on the {rad.crop_n_cells} most affected cells with corrected radiation changed GCR~max~ by {rad.gcr_change} on average?}.`));
}
add(H1("Text S13. Maps by crop and layout"));
add(PF(`Fig. S7 shows the largest ground coverage ratio for all four crops and all three layouts in the robust nitrogen case, the maps of which only the east-west layout is shown in the main text (Fig. 3). Figs. S8 and S9 show the change in GCR~max~ by 2041–2060 under SSP2-4.5 and SSP5-8.5, with calibrated nitrogen, for every crop and layout.`));
add(FIGAUTO("../../results/figures/fig_india_gcrmax_historical_current_robust_thr80.png", 600,
  "As Fig. 3, for all crops and layouts: largest ground coverage ratio  that keeps relative yield at or above 0.80, by crop (rows) and layout (columns), 1995–2014, robust nitrogen case; vertical rows capped at 0.6. Cell values are the median over five climate models, interpolated for display; the number in each panel is the eligible-area-weighted mean with the range of the models. Boundaries: DataMeet India community, States/Admin2 (CC BY 4.0)."));
add(FIGAUTO("../../results/figures/fig_india_delta_ssp245_current_thr80.png", 600,
  "Change in the largest ground coverage ratio at relative yield ≥ 0.80, 2041–2060 under SSP2-4.5 minus 1995–2014, by crop and layout (five-model median, interpolated for display; calibrated nitrogen)."));
add(FIGAUTO("../../results/figures/fig_india_delta_ssp585_current_thr80.png", 600,
  "As Fig. S8, for SSP5-8.5."));
add(H1("Text S14. Simulated relative yield against reduction in ground light"));
add(PF(`Fig. S${L.nextFig()} plots the simulated relative yield (RY) of each crop in the east-west layout against the mean reduction in ground light, with calibrated and with recommended nitrogen. The reduction is one minus the season-mean, strip-mean ground-light factor of the light model, computed for a representative central-Indian site (25° N, 78° E) with a rabi season for wheat and chickpea and a kharif season for pearl millet and groundnut. For the east-west layout the mean reduction is close to the GCR (a GCR of 0.2 gives a reduction of 0.20, 0.5 gives 0.49). Curves are medians over all cells, GCMs and water systems of the 1995–2014 runs; the proportional-loss line marks RY = 1 minus the reduction.`));
add(FIGAUTO("../../results/figures/fig_shade_response_check.png", 380,
  "Simulated median relative yield against mean reduction in ground light, east-west layout, 1995–2014. Solid lines with circles: calibrated nitrogen; dashed lines with squares: recommended nitrogen; dotted line: proportional loss; dashed horizontal line: relative yield = 0.80."));
add(PF(`Fig. S${L.nextFig()} compares these curves with the observations compiled by Jha et al. ${cite("jha")} (public data set of 547 observations from 66 studies; relative yield and reduction in solar radiation, mostly from artificial shading and intercropping trials). Wheat observations are wheat and durum wheat; grain legumes are all grain-legume observations up to a 50% reduction (soybean dominates, with chickpea, mungbean, peanut and bean), compared with the mean of the simulated chickpea and groundnut curves; maize is compared with the simulated pearl millet curve because the compilation contains no millet. Simulated RY was interpolated at each observed reduction. The mean bias (simulated minus observed) with recommended nitrogen was +{shade.val.wheat.recommended.bias} for wheat, +{shade.val.legumes.recommended.bias} for grain legumes and +{shade.val.maize.recommended.bias} for maize, and +{shade.val.wheat.current.bias}, +{shade.val.legumes.current.bias} and +{shade.val.maize.current.bias} with calibrated nitrogen. The simulated crops are therefore more tolerant of shade than the compiled field data, and the comparison is not an India-specific validation.`));
add(FIGAUTO("../../results/figures/fig_shade_validation_jha.png", 600,
  "Observed relative yield against reduction in solar radiation (grey points, Jha et al.) and simulated median relative yield against reduction in ground light (lines), east-west layout. A, wheat; B, grain legumes (simulated: mean of chickpea and groundnut); C, maize (simulated: pearl millet). Blue solid line: calibrated nitrogen; orange dashed line: recommended nitrogen; dotted line: proportional loss."));
add(PF(`*Field-response scenario.* For each crop we fitted a decreasing (isotonic) curve to the observed RY against the reduction in solar radiation, anchored at RY = 1 for no reduction and with gains above one not credited (wheat from wheat and durum wheat, chickpea and groundnut from all grain legumes, pearl millet from maize). The simulated RY of every cell, GCM, layout and GCR was multiplied by c = min(1, observed RY / national median simulated RY), evaluated at the mean ground-light reduction of that layout and GCR (light model at 25° N, 78° E and the season of the crop). Spatial differences between cells are kept and only the average response is aligned with the observations. The potential was then recomputed as in the main case, with the lower GCR~max~ of the calibrated and recommended nitrogen runs. With τ = 0.80 and slopes up to 5%, the east-west potential is {field.ew.t80.cap_twp} TWp ({field.ew.t80.energy_pwh} PWh yr^−1^), the south-facing {field.south.t80.cap_twp} TWp ({field.south.t80.energy_pwh} PWh yr^−1^) and the vertical {field.vertical.t80.cap_twp} TWp ({field.vertical.t80.energy_pwh} PWh yr^−1^); at τ = 0.66 and 0.90 the east-west potential is {field.ew.t66.cap_twp} and {field.ew.t90.cap_twp} TWp. The scenario treats light as the only driver, uses one representative site for the light reduction and relies on maize as the proxy for pearl millet, so it is a bound and not a best estimate. The choice of observation set matters little: leaving soybean out of the grain-legume set gives {field.proxy.nosoy.cap_twp} TWp, using all C3 cereals for wheat gives {field.proxy.c3.cap_twp} TWp, and using maize together with C3 cereals for pearl millet gives {field.proxy.millet_c3.cap_twp} TWp, against {field.ew.t80.cap_twp} TWp for the main set (east-west, 80% threshold, slope ≤5%).`));
add(H1("Text Supplementary references"));
add(refsList());
save(body, "Supporting_Information_AgriPV_India_EarthsFuture.docx");
