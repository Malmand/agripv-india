// Main-text Methodology (concise). Detail lives in build_supp.js (Supplementary Material).
const L = require("./lib.js");
const { cite, P, PF, H1, H2, R, sub, frac, sum, EQ, TABLE, FIG, refsList, save, fill } = L;
L.resetCounters();
const body = [];
const add = (...x) => x.flat().forEach(e => body.push(e));
const { Paragraph, TextRun, FONT } = L;

add(new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: "Yield-Constrained Agrivoltaic Potential of India Under Current and Mid-Century Climate", bold: true, size: 32, font: FONT })] }));
add(P("M. Al-Mandhari^1^ and A. Ghosh^1*^"));
add(P("^1^[Affiliation of each author: department, institution, city, country.]"));
add(P("*Corresponding author: Aritra Ghosh ([email address])"));
require("./abstract.js").addAbstract(add);
require("./intro.js").addIntro(add);

add(H1("2 Materials and Methods"));
add(P(`The potential was estimated by coupling a two-dimensional light model of the ground below the PV rows with process-based crop models, for every 0.25° cell where the four crops are grown, under the current climate and two mid-century scenarios. Fig. 1 shows the workflow: the light model (A), the crop model (B), the threshold test (C) and the conversion to capacity and energy (D). Further detail is given in the Supporting Information (Text S1–S14).`));
add(FIG("fig1_flow.png", 560, 540, "Methodology flowchart. (A) A light model gives the daily light factor of five ground strips below each layout and ground coverage ratio. (B) A crop model simulates open-field and shaded yields, with nitrogen calibrated by state against observed yields. (C) Relative yield is tested against each threshold τ to find the largest feasible ground coverage ratio. (D) That ratio and the eligible land give photovoltaic capacity and energy, reported as the median and range of five global climate models. Numbers in brackets refer to sections of the text."));

add(H2("2.1 Study domain and crop systems"));
add(P(`Four crops cover both cropping seasons and the main contrasts in shade response: wheat (rabi, a C~3~ cereal), chickpea (rabi, C~3~ legume), pearl millet (kharif, C~4~ cereal) and groundnut (mainly kharif, C~3~ legume). Harvested area and irrigated share came from the Spatial Production Allocation Model (MapSPAM) for 2010 ${cite("yu")}. A crop was simulated in a cell where its harvested area was at least 1000 ha, which gives 2977 cells and keeps 93–99% of each crop's national area (Table 2). Irrigated and rainfed systems were simulated separately where each covered at least 10% of the crop's area in the cell.`));
add(TABLE("Crop systems and main crop-model settings.",
  ["Crop", "DSSAT model, cultivar", "Cells", "Area simulated, Mha (share of national)", "Irrigated share", "Sowing date"],
  [["Wheat", "CERES-Wheat, Yecora Rojo", "2095", "28.2 (99%)", "0.79", "Spring wheat calendar"],
   ["Chickpea", "CROPGRO-Chickpea, JG 74", "1462", "8.0 (96%)", "0.12", "Wheat date − 14 d"],
   ["Pearl millet", "CERES-Millet, ICMH 451", "1024", "8.8 (97%)", "0.05", "Millet calendar; rainfed automatic"],
   ["Groundnut", "CROPGRO-Peanut, TMV 2", "897", "5.0 (93%)", "0.19", "Groundnut calendar; rainfed kharif automatic"]],
  [1250, 2150, 750, 1800, 1000, 2076],
  "DSSAT is the Decision Support System for Agrotechnology Transfer. Yecora Rojo is a short-season spring wheat; the default files contain no Indian wheat cultivar, so the state calibration (Section 2.4) also absorbs cultivar differences. Automatic sowing is triggered by soil moisture within ±15 d of the calendar date (Text S3)."));

add(H2("2.2 Agrivoltaic layouts and light model"));
add(P(`Three layouts were simulated (Fig. 2): an elevated south-facing array (tilt 25°), an elevated east-west ridge (tilt 10°), both with a 3 m clearance, and vertical bifacial rows facing east and west. The ground coverage ratio (GCR), module area per ground area, was varied from 0.1 to 0.5, with 0.6 and 0.7 added for wheat and pearl millet and 0.05 for the legumes, whose relative yield (RY) falls fastest. Modules were treated as opaque, and tilt and height were kept the same across India so that differences between cells reflect climate, crop and soil, not design (Table S1).`));
add(FIG("fig2_layouts.png", 600, 197, "Cross-sections of the three layouts at a ground coverage ratio of 0.3 (two rows shown). Blue lines are modules and grey lines supports. The cultivated row pitch is divided into five strips (S1–S5); vertical rows leave a 0.5 m uncultivated strip."));
add(P(`Daily radiation from the climate models was disaggregated to hourly values by scaling the Ineichen-Perez clear-sky irradiance ${cite("ineichen")} to the daily total and splitting it into beam and diffuse parts with the Erbs model ${cite("erbs")}, using pvlib ${cite("pvlib")}. For each ground strip, beam transmission between the rows and the sky view factor were computed with a two-dimensional infinite-row view-factor model ${cite("dupraz", "nassar")} (Text S1). The daily light factor of strip _k_ on day _d_ is`));
add(EQ([sub("f", "k,d"), R(" = "), frac([sum("h∈d", [R("("), sub("T", "k"), R("("), sub("θ", "h"), R(") "), sub("B", "h"), R(" + "), sub("F", "k"), R(" "), sub("D", "h"), R(")")])], [sum("h∈d", [sub("G", "h")])])]));
add(P(`where _T_~k~(θ~h~) is the beam transmission of the strip at the projected solar zenith angle θ~h~ of hour _h_, _B_~h~ the beam irradiance on a horizontal plane, _F_~k~ the sky view factor of the strip, _D_~h~ the diffuse horizontal irradiance and _G_~h~ the global horizontal irradiance (W m^−2^). The crop model of each strip was driven by the open-field daily radiation multiplied by _f_~k,d~; all other weather variables were unchanged. Against the analytical functions in pvlib, the model reproduced the mean sky view factor within 0.0005 and the hourly sunlit ground fraction within 0.0015 (Table S2).`));

add(H2("2.3 Climate data"));
add(P(`Daily climate came from the bias-corrected NASA Earth Exchange Global Daily Downscaled Projections (NEX-GDDP-CMIP6) at 0.25° ${cite("thrasher")}, for five global climate models (GCMs): GFDL-ESM4, IPSL-CM6A-LR, MPI-ESM1-2-HR, MRI-ESM2-0 and UKESM1-0-LL. These are the models of the Inter-Sectoral Impact Model Intercomparison Project phase 3b (ISIMIP3b) and span equilibrium climate sensitivities of about 2.6 to 5.3 K ${cite("meehl")}. Three 20-year periods were simulated: 1995–2014 (reference) and 2041–2060 under SSP2-4.5, an intermediate pathway, and SSP5-8.5, a high-emission pathway ${cite("meinshausen")}. The low-emission SSP1-2.6 was not simulated because of the run time. Atmospheric CO~2~ was held at the period mean of 378, 507 and 563 ppm ${cite("meinshausen")}. Variable conversion is described in Text S2.`));

add(H2("2.4 Crop model and calibration"));
add(P(`Crops were simulated with DSSAT 4.8 ${cite("jones", "hoogenboom")}, with Penman-Monteith evapotranspiration ${cite("allen")}, nitrogen fixation for the legumes and the CO~2~ response of each model. Sowing dates came from the Global Gridded Crop Model Intercomparison (GGCMI) Phase 3 crop calendar ${cite("jagermeyr")}, and soil profiles to 2 m from SoilGrids 2.0 ${cite("poggio")} with the Saxton and Rawls pedotransfer functions ${cite("saxton")}. Irrigated systems were irrigated automatically when soil water in the top 30 cm fell below a set fraction of plant-available water (Text S3).`));
add(PF(`Nitrogen input, which controls much of the yield gap of Indian wheat and pearl millet, differs strongly between states, and a single national rule reproduced the mean wheat yield but not its spatial pattern (Table 3). Nitrogen was therefore calibrated by state for these two crops, as is common in large-scale crop modelling ${cite("folberth12", "muller17")}: open-field yields were simulated at 10 (pearl millet only), 30, 60, 90, 120 and 180 kg N ha^−1^ with two GCMs, and in each state the level whose area-weighted mean yield was closest to the observed 1995–2014 state yield ${cite("icrisat")} was selected (Table S6). The calibrated level is an effective management intensity that also absorbs other yield-limiting factors. Across states, its Spearman rank correlation with the fertiliser nitrogen used per hectare of cropped area is {calib.wheat.spearman_nuse} for wheat ({calib.wheat.after.n} states) and {calib.pearl_millet.spearman_nuse} for pearl millet ({calib.pearl_millet.after.n} states; Text S4). The legumes were not calibrated: chickpea was unbiased on average, while groundnut was over-estimated by a factor of {calib.groundnut.before.ratio}. Because RY is a ratio of two yields from the same model, a bias that scales both does not change it (Text S5).`));
add(PF(`Calibrated nitrogen is the base management case, and the only one used for the mid-century runs. A recommended-practice case was also run for the reference period (120 kg N ha^−1^ for irrigated wheat; Table S4). The robust case, which we use for the headline, takes in each cell the smaller GCR~max~ of the calibrated and recommended cases, so it mixes nitrogen levels by state and does not simply raise nitrogen everywhere.`));
add(TABLE("Simulated against observed open-field state yields, 1995–2014 (states with at least 50 kha of the crop).",
  ["Crop", "States", "Case", "Pearson r", "Mean absolute percentage error (%)", "Simulated / observed"],
  [["Wheat", "wheat", "before", "Uncalibrated"], ["Wheat", "wheat", "after", "Calibrated"],
   ["Pearl millet", "pearl_millet", "before", "Uncalibrated"], ["Pearl millet", "pearl_millet", "after", "Calibrated"],
   ["Chickpea", "chickpea", "before", "Not calibrated"], ["Groundnut", "groundnut", "before", "Not calibrated"]]
    .map(([name, c, k, lab]) => [name, fill(`{calib.${c}.${k}.n}`), lab, fill(`{calib.${c}.${k}.r}`), fill(`{calib.${c}.${k}.mape}`),
      fill(`{calib.${c}.${k}.ratio} ({calib.${c}.${k}.ratio_pool})`)]),
  [1500, 900, 1700, 1300, 1300, 2326],
  "Mean of GFDL-ESM4 and MPI-ESM1-2-HR. The mean absolute percentage error is weighted by observed harvested area. Simulated / observed is the area-weighted mean of the state ratios; in brackets, the ratio of the area-weighted mean yields."));

add(H2("2.5 Yield-constrained potential"));
add(P(`For each cell, crop system, layout, GCR and GCM, the relative yield was computed on a land-area basis, as in land equivalent ratio studies and the reference-yield rule of DIN SPEC 91434 ${cite("dupraz", "weselek", "din")}:`));
add(EQ([R("RY = c "), frac([sub("Ȳ", "APV")], [sub("Ȳ", "0")])]));
add(P(`where Ȳ~APV~ is the yield under the array averaged over strips and seasons, Ȳ~0~ the open-field yield over the same seasons (kg ha^−1^), and _c_ the cultivated share of the pitch (1 for the elevated layouts). Irrigated and rainfed systems were combined by production. The largest GCR that meets a threshold τ, GCR~max~, was found by linear interpolation at the first crossing of the RY-GCR curve, which starts at RY = 1 for GCR = 0 ${cite("dupraz24", "willockx")}; where RY stayed above τ at the largest simulated GCR, that value was used and reported as a lower bound. Three thresholds from existing rules were used: τ = 0.66 (DIN SPEC 91434 ${cite("din")}), 0.80 (Japan ${cite("maff")}; main case) and 0.90 (France ${cite("decret")}). DIN SPEC 91434 also limits the land lost to the structure to 15%, which the 0.5 m strip of the vertical layout exceeds above GCR 0.6; vertical GCR~max~ is therefore capped at 0.6.`));
add(P(`Eligible land was the MapSPAM harvested area of each crop multiplied by the share of the cell with terrain slope of at most 5%, the limit used to screen land for utility PV in India ${cite("deshmukh")}, from the Copernicus 90 m elevation model ${cite("copdem")}. Because a PV array stands all year, the rabi area _A_~r~ (wheat, chickpea) and kharif area _A_~k~ (pearl millet, groundnut) of a cell were assumed to overlap as far as possible, and the overlap had to satisfy both seasons. Every eligible hectare enters at its own GCR~max~, so thresholds, layouts, management and climate change the potential through density, not land area. For a cell, capacity is`));
add(EQ([R("P = η "), sub("I", "STC"), R(" [ "), sub("A", "ov"), R(" min("), sub("ḡ", "r"), R(", "), sub("ḡ", "k"), R(") + ("), sub("A", "r"), R(" − "), sub("A", "ov"), R(") "), sub("ḡ", "r"), R(" + ("), sub("A", "k"), R(" − "), sub("A", "ov"), R(") "), sub("ḡ", "k"), R(" ]")]));
add(P(`where η = 0.22 is the module efficiency, _I_~STC~ = 1000 W m^−2^, _A_~ov~ = min(_A_~r~, _A_~k~) the double-cropped area, and ḡ~r~ and ḡ~k~ the area-weighted GCR~max~ of the rabi and kharif crops. Annual energy was obtained by multiplying capacity by the specific yield of each cell, layout and GCR, computed with pvlib for a bifacial glass-glass module using the infinite-sheds model, the Faiman cell temperature model ${cite("faiman")} and PVWatts ${cite("dobos")} (Table S8).`));

add(H2("2.6 Uncertainty and assumptions"));
add(P(`All steps were run separately for each GCM; national and state totals are the five-GCM median with the minimum and maximum as the range. This range is not a total uncertainty: all GCMs are bias-corrected to the same observations, and crop-model, calibration, soil and light-model errors are not propagated. Sensitivity cases change one assumption at a time (Table 4). ${fill.has("rad.k_north_pct") ? `For PV energy, daily radiation was rescaled cell by cell and month by month to the 2001–2020 NASA POWER climatology ${cite("nasapower")}, because aerosols dim surface radiation over India ${cite("padma")} and reduce PV output ${cite("bergin")}, as in linear-scaling bias correction ${cite("teutschbein")}. ` : ""}Three assumptions shape the results. Panels change only the radiation reaching the crop, so lower leaf temperature and evaporative demand under shade are not represented. Mid-century yields include CO~2~ fertilisation, which is strongest for the C~3~ legumes. And the potential is technical, bounded by crop yield and terrain only: grid capacity and land tenure are not considered, and economics enter only as a screening (Section 2.7).`));

if (fill.has("econ.crop_value_bn")) {
  add(H2("2.7 Screening economics"));
  add(P(`The economic layer asks what the yield rule costs the crop and whether elevated arrays could be paid for; it is a screening estimate, not a project appraisal. For each cell, the levelised cost of electricity (LCOE) was set to the price discovered in the Gujarat reverse auction for PM-KUSUM Component A, Indian rupees (Rs) 2.77–2.78 per kWh ${cite("gerc")}, scaled by the ratio of the median specific yield of all cells to that of the cell, and a structure premium for the elevated frame of 0%, 25%, 30% or 38% was added. The Union Minister for New and Renewable Energy has put the extra cost of agrivoltaic plants at 25–30% ${cite("mnre25")}, and 38% is the excess LCOE of an elevated plant in a German analysis ${cite("schindele")}. Electricity was valued at the regulator's ceiling tariff of Rs 2.95 per kWh ${cite("gerc")}. The gross crop value of each eligible hectare is the observed state mean yield of 1995–2014 ${cite("icrisat")} times the minimum support price of each crop (Rs 2,585, 5,875, 2,900 and 7,517 per quintal for wheat, chickpea, pearl millet and groundnut ${cite("pibrabi", "pibkharif")}). The yield rule limits the crop loss to a share (1 − τ) of this value. Land lease, grid connection, financing and crop input costs were not modelled, so results are given per kWh and per hectare, not as national revenue.`));
}

require("./results.js").addResults(add);
require("./discussion.js").addDiscussion(add);
require("./conclusions.js").addConclusions(add);

add(H1("Author Contributions"));
add(P("Mohamed Al-Mandhari: Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Data curation, Visualization, Writing – original draft. Aritra Ghosh: Conceptualization, Methodology, Supervision, Project administration, Funding acquisition, Writing – review & editing."));
add(H1("Conflict of Interest Statement"));
add(P("The authors declare there are no conflicts of interest for this manuscript."));
add(H1("Acknowledgments"));
add(P("[Funding information for both authors, and any thanks, to be added. If there is no funding, state that no specific funding supported this work.]"));
add(H1("Open Research"));
add(P("[The simulation outputs behind the figures and tables (cell-level capacity, relative yield and economics tables) will be deposited in a public repository, with its DOI cited here and in the reference list. Software availability statement to be added if the editor requires it.] Input data are public: NEX-GDDP-CMIP6 (Thrasher et al., 2022), MapSPAM (Yu et al., 2020), SoilGrids 2.0 (Poggio et al., 2021), the Copernicus digital elevation model (European Space Agency, 2022) and the ICRISAT district database (Swamikannu et al., 2021)."));
add(H1("References"));
add(refsList());
save(body, "Manuscript_AgriPV_India_EarthsFuture.docx");
