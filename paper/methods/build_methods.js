// Main-text Methodology (concise). Detail lives in build_supp.js (Supplementary Material).
const L = require("./lib.js");
const { cite, P, H1, H2, R, sub, frac, sum, EQ, TABLE, FIG, refsList, save } = L;
L.resetCounters();
const body = [];
const add = (...x) => x.flat().forEach(e => body.push(e));
const { Paragraph, TextRun, FONT } = L;
add(new Paragraph({ spacing: { after: 300 }, children: [new TextRun({ text: "Yield-constrained agrivoltaic potential of India under current and mid-century climate", bold: true, size: 32, font: FONT })] }));
require("./intro.js").addIntro(add);

add(H1("2. Methodology"));
add(P(`The APV potential was estimated by coupling a two-dimensional light model of the ground below the PV rows with a process-based crop model, applied to every 0.25° cell where the four crops are grown, under the current climate and two mid-century scenarios. Fig. 1 shows the workflow. Further detail on each step is given in the Supplementary Material (SM).`));
add(FIG("fig1_flow.png", 560, 540, "Methodology flowchart. (A) A light model gives the daily light factor of five ground strips below each layout and GCR. (B) DSSAT simulates open-field and shaded yields, with nitrogen calibrated by state against observed yields. (C) Relative yield (RY) is tested against each threshold τ to find the largest feasible GCR (GCR~max~). (D) GCR~max~ and eligible land give PV capacity and energy, reported as the five-GCM median and range. Numbers in brackets refer to sections of the text."));

// 2.1
add(H2("2.1. Study domain and crop systems"));
add(P(`Four crops were chosen to cover both cropping seasons and the main contrasts in shade response: wheat (rabi, C~3~ cereal), chickpea (rabi, C~3~ legume), pearl millet (kharif, C~4~ cereal) and groundnut (mainly kharif, C~3~ legume). Harvested area and irrigated share were taken from MapSPAM 2010 ${cite("yu")}. A crop was simulated in a cell where its harvested area was at least 1000 ha; this gives 2977 cells and keeps 93–99% of each crop's national area (Table 2). Irrigated and rainfed systems were simulated separately where each covered at least 10% of the crop's area in the cell.`));
add(TABLE("Crop systems and main crop-model settings.",
  ["Crop", "DSSAT model, cultivar", "Cells", "Area simulated, Mha (share of national)", "Irrigated share", "Sowing date"],
  [["Wheat", "CERES-Wheat, Yecora Rojo", "2095", "28.2 (99%)", "0.79", "GGCMI spring wheat"],
   ["Chickpea", "CROPGRO-Chickpea, JG 74", "1462", "8.0 (96%)", "0.12", "Wheat date − 14 d"],
   ["Pearl millet", "CERES-Millet, ICMH 451", "1024", "8.8 (97%)", "0.05", "GGCMI millet; rainfed automatic"],
   ["Groundnut", "CROPGRO-Peanut, TMV 2", "897", "5.0 (93%)", "0.19", "GGCMI groundnut; rainfed kharif automatic"]],
  [1250, 2150, 750, 1800, 1000, 2076],
  "Cultivars from the DSSAT 4.8 genotype files; Yecora Rojo is a short-season spring wheat; the default files contain no Indian wheat cultivar, so the state calibration (Section 2.4) also absorbs cultivar differences. Automatic sowing: within ±15 d of the calendar date, triggered by soil moisture (SM Section S3)."));

// 2.2
add(H2("2.2. Agrivoltaic layouts and light model"));
add(P(`Three layouts were simulated (Fig. 2): an elevated south-facing array (tilt 25°), an elevated east-west ridge (tilt 10°), both with a 3 m clearance, and vertical bifacial rows facing east and west. GCR, the module area per ground area, was varied from 0.1 to 0.5, with 0.6 and 0.7 added for wheat and pearl millet and 0.05 for the legumes, whose RY falls fastest. Modules were treated as opaque, and tilt and height were kept the same across India so that differences between cells reflect climate, crop and soil rather than design (geometry in Table S1).`));
add(FIG("fig2_layouts.png", 600, 197, "Cross-sections of the three layouts at GCR 0.3 (two rows shown). Blue lines are modules and grey lines supports. The cultivated part of each row pitch is divided into five strips (S1–S5). The vertical layout leaves a 0.5 m uncultivated strip under each row."));
add(P(`Daily radiation from the climate models was disaggregated to hourly values by scaling the Ineichen-Perez clear-sky irradiance ${cite("ineichen")} to the daily total and splitting it into beam and diffuse parts with the Erbs model ${cite("erbs")}, using pvlib ${cite("pvlib")}. For each ground strip, beam transmission between the rows and the sky view factor were computed with a two-dimensional infinite-row view-factor model, following the ray and view-factor approaches used for ground irradiance below PV rows ${cite("dupraz", "nassar")}. The daily light factor of strip _k_ on day _d_ is`));
add(EQ([sub("f", "k,d"), R(" = "), frac([sum("h∈d", [R("("), sub("T", "k"), R("("), sub("θ", "h"), R(") "), sub("B", "h"), R(" + "), sub("F", "k"), R(" "), sub("D", "h"), R(")")])], [sum("h∈d", [sub("G", "h")])])]));
add(P(`where _T_~k~(θ~h~) is the beam transmission of the strip at the projected solar zenith angle θ~h~ of hour _h_, _B_~h~ the beam irradiance on a horizontal plane, _F_~k~ the sky view factor of the strip, _D_~h~ the diffuse horizontal irradiance and _G_~h~ the global horizontal irradiance (W m^−2^). The crop model of each strip was driven by the open-field daily radiation multiplied by _f_~k,d~; all other weather variables were left unchanged. Against the analytical functions in pvlib, the model reproduced the mean sky view factor within 0.0005 and the hourly sunlit ground fraction with a mean absolute difference of 0.0015 (Table S2).`));

// 2.3
add(H2("2.3. Climate data"));
add(P(`Daily climate came from NEX-GDDP-CMIP6, a bias-corrected and downscaled CMIP6 product at 0.25° ${cite("thrasher")}, for five GCMs: GFDL-ESM4, IPSL-CM6A-LR, MPI-ESM1-2-HR, MRI-ESM2-0 and UKESM1-0-LL. These are the GCMs of the ISIMIP3b impact-model protocol and span equilibrium climate sensitivities of about 2.6 to 5.3 K ${cite("meehl")}. Three 20-year periods were simulated: 1995–2014 (reference) and 2041–2060 under SSP2-4.5 and SSP5-8.5. Atmospheric CO~2~ was held at the period mean, 378, 507 and 563 ppm ${cite("meinshausen")}. Variable conversion is described in SM Section S2.`));

// 2.4
add(H2("2.4. Crop model and calibration"));
add(P(`Crops were simulated with DSSAT 4.8 ${cite("jones", "hoogenboom")} (CERES-Wheat, CERES-Millet, CROPGRO-Chickpea and CROPGRO-Peanut), with FAO-56 Penman-Monteith evapotranspiration ${cite("allen")}, nitrogen fixation for the legumes and the CO~2~ response of each model. Each season was simulated independently. Sowing dates came from the GGCMI Phase 3 crop calendar ${cite("jagermeyr")}; chickpea was sown 14 days before the local wheat date because the GGCMI pulse calendar describes kharif pulses. Soil profiles to 2 m were built from SoilGrids 2.0 ${cite("poggio")} with the Saxton and Rawls pedotransfer functions ${cite("saxton")}. Irrigated systems were irrigated automatically when soil water in the top 30 cm fell below a set fraction of plant-available water.`));
add(P(`Nitrogen input, which controls much of the yield gap of Indian wheat and pearl millet, differs strongly between states, and a single national rule reproduced the mean wheat yield but not its spatial pattern (Table 3). Nitrogen was therefore calibrated by state for these two crops. Open-field yields were simulated at 10 (pearl millet only), 30, 60, 90, 120 and 180 kg N ha^−1^ with two GCMs for the reference period, and in each state the level whose area-weighted mean yield was closest to the observed 1995–2014 state yield ${cite("icrisat")} was selected (Table S6). The calibrated level is interpreted as an effective management intensity, since it also absorbs other yield-limiting factors. It nonetheless follows survey data on fertiliser use by crop, which report about 106 and 56 kg N ha^−1^ for irrigated and rainfed wheat, 62 and 18 kg N ha^−1^ for pearl millet, and the highest wheat rates in Haryana and Punjab ${cite("fao2005")}; the calibrated levels are 30–180 kg N ha^−1^ for wheat, highest in Punjab and Gujarat, and 10–30 kg N ha^−1^ for pearl millet.`));
add(P(`Calibration raised the between-state correlation for wheat from 0.01 to 0.74 and reduced the error from 29% to 12% (Table 3). For pearl millet the gain was smaller, because yields in the southern states stayed too high even at the lowest level. The legumes were not calibrated: chickpea was unbiased on average, while groundnut was over-estimated by a factor of 2.6, in line with its large yield gap in India. Since RY is a ratio of two yields from the same model, a bias that scales both yields does not change it; legume yields were scaled by state yield-gap factors only when absolute production is reported (Table S7). Calibrated nitrogen is the main management case; a recommended-practice case with higher nitrogen and irrigation was run for the reference period as a sensitivity test (Table S4).`));
add(TABLE("Simulated against observed open-field state yields, 1995–2014 (states with at least 50 kha of the crop).",
  ["Crop", "States", "Case", "Pearson r", "MAPE (%)", "Simulated / observed"],
  [["Wheat", "15", "Uncalibrated", "0.01", "29", "0.92"], ["Wheat", "15", "Calibrated", "0.74", "12", "1.01"],
   ["Pearl millet", "9", "Uncalibrated", "0.04", "31", "1.01"], ["Pearl millet", "9", "Calibrated", "0.28", "24", "1.09"],
   ["Chickpea", "11", "Not calibrated", "0.21", "29", "1.02"], ["Groundnut", "10", "Not calibrated", "−0.19", "163", "2.63"]],
  [1500, 900, 1700, 1300, 1300, 2326],
  "Mean of GFDL-ESM4 and MPI-ESM1-2-HR. MAPE and the ratio are weighted by observed harvested area."));

// 2.5
add(H2("2.5. Yield-constrained potential"));
add(P(`For each cell, crop system, layout, GCR and GCM, the relative yield was computed on a land-area basis, as in land equivalent ratio studies and the reference-yield rule of DIN SPEC 91434 ${cite("dupraz", "weselek", "din")}:`));
add(EQ([R("RY = c "), frac([sub("Ȳ", "APV")], [sub("Ȳ", "0")])]));
add(P(`where Ȳ~APV~ is the yield under the array averaged over strips and seasons, Ȳ~0~ the open-field yield over the same seasons (kg ha^−1^), and _c_ the cultivated share of the pitch (1 for the elevated layouts). Irrigated and rainfed systems were combined by production (Eq. (S1)). The largest GCR that meets a threshold τ was found on the RY-GCR curve, which starts at RY = 1 for GCR = 0, by linear interpolation at the first crossing. This extends the use of GCR as the design variable that links light sharing to crop yield ${cite("dupraz24", "willockx")}:`));
add(EQ([sub("GCR", "max"), R(" = "), sub("g", "j−1"), R(" + "), frac([R("("), sub("RY", "j−1"), R(" − τ)("), sub("g", "j"), R(" − "), sub("g", "j−1"), R(")")], [sub("RY", "j−1"), R(" − "), sub("RY", "j")])]));
add(P(`where _g_~j~ is the first simulated GCR with RY below τ and _g_~j−1~ the one before it, so that every smaller GCR also meets τ. Where RY stayed above τ at the largest simulated GCR, GCR~max~ was set to that value and reported as a lower bound. Three thresholds from existing rules were used: τ = 0.66 (DIN SPEC 91434 ${cite("din")}), 0.80 (Japan, where a yield drop of about 20% against the local average voids the permit ${cite("maff")}; main case) and 0.90 (France ${cite("decret")}). DIN SPEC 91434 also limits the land lost to the structure to 15% for systems with crops between the rows; the 0.5 m strip of the vertical layout exceeds this above GCR 0.6.`));
add(P(`Eligible land was the MapSPAM harvested area of each crop multiplied by the share of the cell with terrain slope of at most 5%, computed from the Copernicus GLO-90 elevation model ${cite("copdem")}. Because a PV array stands all year, the rabi area _A_~r~ (wheat, chickpea) and kharif area _A_~k~ (pearl millet, groundnut) of a cell were assumed to overlap as far as possible, and the overlap had to satisfy both seasons. Capacity follows from module area and rated efficiency, as in earlier national APV estimates ${cite("dinesh", "adeh")}; for a cell it is`));
add(EQ([R("P = η "), sub("I", "STC"), R(" [ "), sub("A", "ov"), R(" min("), sub("ḡ", "r"), R(", "), sub("ḡ", "k"), R(") + ("), sub("A", "r"), R(" − "), sub("A", "ov"), R(") "), sub("ḡ", "r"), R(" + ("), sub("A", "k"), R(" − "), sub("A", "ov"), R(") "), sub("ḡ", "k"), R(" ]")]));
add(P(`where η = 0.22 is the module efficiency, _I_~STC~ = 1000 W m^−2^, _A_~ov~ = min(_A_~r~, _A_~k~) the double-cropped area, and ḡ~r~ and ḡ~k~ the area-weighted GCR~max~ of the rabi and kharif crops. Annual energy was obtained by multiplying capacity by the specific yield of each cell, layout and GCR, computed with pvlib for a bifacial glass-glass module from the same hourly irradiance, using the infinite-sheds model for front and rear irradiance, the Faiman cell temperature model ${cite("faiman")} and PVWatts ${cite("dobos")} (Table S8).`));

// 2.6
add(H2("2.6. Uncertainty and assumptions"));
add(P(`All steps were run separately for each GCM; national and state totals are reported as the five-GCM median with the minimum and maximum as the range. Sensitivity cases cover the threshold (0.66, 0.90), the slope limit (none, 10%), management (recommended practice) and climate (both scenarios). Three assumptions shape the results. Panels change only the radiation reaching the crop; lower leaf temperature and evaporative demand under shade are not represented, which probably makes RY conservative for rainfed crops in hot regions. Mid-century yields include CO~2~ fertilisation, which is strongest for the C~3~ legumes. Finally, the potential is technical, bounded by crop yield and terrain only; grid capacity, land tenure and economics are not considered.`));

require("./results.js").addResults(add);

require("./discussion.js").addDiscussion(add);

add(H1("References"));
add(refsList());
save(body, "Manuscript_AgriPV_India.docx");
require("./highlights.js").writeHighlights();
