// Section 3 Results. Every number is a {key} placeholder filled from results/potential/numbers.json
// (src/make_numbers.py) by fill()/PF() in lib.js. Sentences in {? ... ?} need a stage that may be missing
// (robust case, SSP2-4.5, SSP5-8.5) and are dropped until it exists; other missing keys show [pending].
// Figures are the PNGs written by src/fig_india.py; a missing PNG gives a [pending] caption.
const L = require("./lib.js");
const { PF, H1, H2, TABLE, FIGAUTO, fill, cite } = L;
const FIGS = "../../results/figures/";
const LAY = [["south", "South-facing, elevated"], ["ew", "East-west, elevated"], ["vertical", "Vertical bifacial"]];
const THR = [["t66", "0.66"], ["t80", "0.80"], ["t90", "0.90"]];

function addResults(add) {
  add(H1("3 Results"));

  // 3.1
  add(H2("3.1 Model evaluation"));
  add(PF(`Calibrating nitrogen by state improved the simulated open-field yields of the two cereals (Fig. S1). For wheat, the correlation between simulated and observed state yields rose from r = {calib.wheat.before.r} to {calib.wheat.after.r} and the area-weighted mean absolute percentage error fell from {calib.wheat.before.mape}% to {calib.wheat.after.mape}% ({calib.wheat.after.n} states). Pearl millet improved less, from r = {calib.pearl_millet.before.r} to {calib.pearl_millet.after.r} and from {calib.pearl_millet.before.mape}% to {calib.pearl_millet.after.mape}%, because yields in the south stayed over-predicted even at the lowest nitrogen level. The light model reproduced the pvlib view factors closely and the light measured over the whole Jodhpur system, but over-estimated the light directly below the modules under low winter sun (Figs. S2 and S3).`));

  // 3.2 to 3.4: the robust case (minimum GCR_max of calibrated and recommended nitrogen) is the main case;
  // calibrated nitrogen alone is the upper bound, compared in 3.4 (its maps and state chart: Figs. S4, S5).
  const ROB = fill.has("robust.change_pct");
  const C = ROB ? "robust" : "hist";
  const CASE = ROB ? "robust nitrogen case (smaller of the calibrated and recommended nitrogen results in each cell)" : "calibrated nitrogen (upper bound)";
  const STG = ROB ? "historical_current_robust" : "historical_current";

  // 3.2
  add(H2("3.2 Feasible ground coverage ratio by crop and layout"));
  add(PF(`Cereals tolerate about twice the panel density of legumes (Fig. 3A–D). In the east-west layout, the area-weighted mean GCR~max~ at RY ≥ 0.80 was {${C}.ew.t80.gcr_wheat} for wheat and {${C}.ew.t80.gcr_pearl_millet} for pearl millet{? ({field.gcr_pearl_millet} in the field-response scenario, which rests on maize as a proxy, so the pearl millet value is the least certain)?}, but {${C}.ew.t80.gcr_chickpea} for chickpea and {${C}.ew.t80.gcr_groundnut} for groundnut. The south-facing array allowed the lowest densities for every crop, most clearly for the rabi crops wheat ({${C}.south.t80.gcr_wheat}) and chickpea ({${C}.south.t80.gcr_chickpea}), whose grain fills under low winter sun (Fig. 3E). Vertical rows allowed densities close to the east-west layout and reached the cap of 0.6 on at least {${C}.vertical.t80.atcap_pearl_millet}% of the pearl millet area. Within each crop, GCR~max~ varied strongly across the country. Maps for all crops and layouts, and their change by mid-century, are in Figs. S7–S9.`));
  add(FIGAUTO(FIGS + `fig_india_gcrmain_${STG}_thr80.png`, 600,
    `Largest ground coverage ratio that keeps relative yield at or above 0.80, 1995–2014, ${CASE}. (A–D) East-west layout by crop: median of five climate models, interpolated for display; the number in each map is the area-weighted mean. (E) Mean by crop and layout, with error bars for the range of the five models. Boundaries: DataMeet India community, States/Admin2 (https://github.com/datameet/maps, Creative Commons Attribution 4.0 licence).`));

  // 3.3
  add(H2("3.3 National potential"));
  add(PF(`Under the yield rule, Indian cropland could host {${C}.ew.t80.cap_twp_m} terawatts peak (TWp) of APV (Fig. 4, Table 4). This is the east-west layout at τ = 0.80 on {${C}.ew.t80.land_mha} Mha of cropland with slopes up to 5% (GCM range {${C}.ew.t80.cap_twp_lo}–{${C}.ew.t80.cap_twp_hi} TWp), or {${C}.ew.t80.density} megawatts peak (MWp) per hectare. It would generate {${C}.ew.t80.energy_pwh} petawatt-hours (PWh) per year, about {frame.head_multiple} times India's 2025–26 electricity requirement of {frame.cea_twh} terawatt-hours ${cite("cea")}. Seen the other way, 500 gigawatts peak at this mean density would occupy only {frame.gw500.land_mha} Mha, {frame.gw500.share}% of the eligible cropland. Capacity density is highest across the Indo-Gangetic plain and north-western Rajasthan and lowest in the legume-growing Deccan and the south, which follows the crop pattern of Fig. 3.`));
  add(FIGAUTO(FIGS + `fig_india_capmap_${STG}_thr80.png`, 600,
    `Yield-constrained capacity density (megawatts peak per hectare of cropland, crops combined) for east-west elevated arrays at relative yield ≥ 0.80, 1995–2014, ${CASE}, slope ≤ 5%. Median of five climate models, interpolated for display; cells with less than 1000 ha of eligible cropland are blank. Labels give the capacity of the three leading states.`));
  add(PF(`The layouts rank differently by capacity (Fig. 5A) and by energy (Fig. 5B). Vertical rows reached the most capacity, {${C}.vertical.t80.cap_twp_m} TWp with the 0.6 cap, against {${C}.south.t80.cap_twp_m} TWp for the south-facing array, but their specific yield was only {${C}.vertical.t80.sy} kWh kWp^−1^ yr^−1^ against {${C}.ew.t80.sy} for east-west arrays, so they produced the least energy ({${C}.vertical.t80.energy_pwh} PWh yr^−1^). East-west arrays gave the most energy at every threshold and are used for the headline. The threshold mattered more than the slope rule: capacity was {${C}.ew.t66.cap_twp} TWp at τ = 0.66 and {${C}.ew.t90.cap_twp} TWp at τ = 0.90, while dropping the slope limit raised it only to {${C}.ew.t80.none.cap_twp} TWp. Three states hold {${C}.top3_share}% of the potential: {${C}.top1_state} ({${C}.top1_twp} TWp), {${C}.top2_state} ({${C}.top2_twp} TWp) and {${C}.top3_state} ({${C}.top3_twp} TWp) (Fig. 6).`));
  const cell = (c, lk, tk) => fill(`{${c}.${lk}.${tk}.cap_twp_m} ({${c}.${lk}.${tk}.cap_twp_lo}–{${c}.${lk}.${tk}.cap_twp_hi})`);
  if (ROB) {
    add(TABLE("Yield-constrained APV potential of India for four crops, 1995–2014: robust nitrogen case and calibrated nitrogen alone (upper bound). Slope ≤ 5%; crops combined with double-cropped land counted once; vertical GCR~max~ capped at 0.6.",
      ["Layout", "τ", "Capacity, TWp (robust)", "Capacity, TWp (calibrated)", "Energy, PWh yr^−1^ (robust)", "Energy, PWh yr^−1^ (calibrated)", "MWp ha^−1^ (robust)"],
      LAY.flatMap(([lk, name]) => THR.map(([tk, tv], i) => [i === 0 ? name : "", tv, cell("robust", lk, tk), cell("hist", lk, tk),
        fill(`{robust.${lk}.${tk}.energy_pwh}`), fill(`{hist.${lk}.${tk}.energy_pwh}`), fill(`{robust.${lk}.${tk}.density}`)])),
      [1700, 500, 1550, 1550, 1200, 1200, 1326],
      fill("Median over five GCMs, GCM range in brackets. Land is the eligible crop area, {robust.ew.t80.land_mha} Mha in every case; the threshold and nitrogen act through the density. Vertical rows without the 0.6 cap (robust): {robust.vertical.t66.nodin.cap_twp}, {robust.vertical.t80.nodin.cap_twp} and {robust.vertical.t90.nodin.cap_twp} TWp at τ = 0.66, 0.80 and 0.90.")));
    add(FIGAUTO(FIGS + "fig_india_cases_historical_current_robust.png", 600,
      "National agrivoltaic capacity (A) and annual energy (B) by layout and relative-yield threshold, 1995–2014, slope ≤ 5%. Filled bars: robust nitrogen case; outline bars: calibrated nitrogen alone (upper bound). Median of five climate models, with error bars for their range."));
  } else {
    add(TABLE("Yield-constrained APV potential of India for four crops, 1995–2014 (calibrated nitrogen, an upper bound; slope ≤ 5%; crops combined with double-cropped land counted once; vertical GCR~max~ capped at 0.6).",
      ["Layout", "τ", "Capacity, TWp", "Energy, PWh yr^−1^", "Land, Mha", "MWp ha^−1^"],
      LAY.flatMap(([lk, name]) => THR.map(([tk, tv], i) => [i === 0 ? name : "", tv, cell("hist", lk, tk),
        fill(`{hist.${lk}.${tk}.energy_pwh}`), fill(`{hist.${lk}.${tk}.land_mha}`), fill(`{hist.${lk}.${tk}.density}`)])),
      [2100, 700, 2000, 1600, 1300, 1326],
      fill("Median over five GCMs, GCM range in brackets. Land is the eligible crop area and does not depend on τ; the threshold acts through the density.")));
    add(FIGAUTO(FIGS + "fig_india_capacity_historical_current.png", 450,
      "National agrivoltaic capacity by layout and relative-yield threshold, 1995–2014, calibrated nitrogen (upper bound), slope ≤ 5%. Median of five climate models, with error bars for their range; markers show the cases without a slope limit and with a 10% limit."));
  }
  add(FIGAUTO(FIGS + `fig_india_states_${STG}_thr80.png`, 450,
    `Capacity of the leading states at relative yield ≥ 0.80 by layout, 1995–2014, ${CASE}, slope ≤ 5%. Median of five climate models, with error bars for their range.`));

  // 3.4
  if (ROB) {
    add(H2("3.4 Nitrogen management and the field-response scenario"));
    add(PF(`With calibrated nitrogen alone, the east-west potential at τ = 0.80 is {main.cap_twp_m} TWp (GCM range {main.cap_twp_lo}–{main.cap_twp_hi}) and {main.energy_pwh} PWh yr^−1^, so the robust case is {robust.reduction_pct}% lower (Table 4, Fig. 5). The difference comes almost entirely from the cereals: mean GCR~max~ falls from {main.gcr_wheat} to {robust.ew.t80.gcr_wheat} for wheat and from {main.gcr_pearl_millet} to {robust.ew.t80.gcr_pearl_millet} for pearl millet, while the legumes barely change. With calibrated nitrogen, {main.atcap_wheat}% of the east-west wheat area still met the threshold at GCR 0.7; in the robust case {robust.ew.t80.atcap_wheat}% does. These wheat cells lie mostly in states with low calibrated nitrogen, which points to nitrogen masking rather than true shade tolerance (Section 4.2). Figs. S4 and S5 show the calibrated-nitrogen maps and state results.`));
    add(PF(`The crop models are also more tolerant of shade than field observations (Text S14). In the field-response scenario, simulated RY is rescaled so that its dependence on the reduction in ground light follows the observations compiled by Jha et al. ${cite("jha")}, with maize standing in for pearl millet. The east-west potential at τ = 0.80 then falls by {field.reduction_pct}% to {field.ew.t80.cap_twp} TWp and {field.ew.t80.energy_pwh} PWh yr^−1^, with GCR~max~ of {field.gcr_wheat} for wheat, {field.gcr_pearl_millet} for pearl millet, {field.gcr_groundnut} for groundnut and {field.gcr_chickpea} for chickpea, and the ranking of layouts by energy is unchanged. We therefore treat the robust case as the upper bound and the field-response scenario as the lower bound of the technical potential.`));
  }

  // 3.5
  if (fill.has("ssp245.change_pct") || fill.has("ssp585.change_pct")) {
    add(H2(`3.${fill.has("robust.change_pct") ? 5 : 4} Mid-century change`));
    add(PF(`${fill.has("ssp585r.change_pct") ? "Both pathways were run with calibrated nitrogen, and SSP5-8.5 also with recommended nitrogen, so the robust case can be compared with its own 1995–2014 potential of {robust.ew.t80.cap_twp_m} TWp. With calibrated nitrogen the changes below are relative to the calibrated 1995–2014 potential of {main.cap_twp_m} TWp." : "The climate runs use calibrated nitrogen, so the changes below are relative to the calibrated 1995–2014 potential of {main.cap_twp_m} TWp."} {?By 2041–2060 under SSP2-4.5, the east-west potential at τ = 0.80 changes by {ssp245.change_pct}% to {ssp245.ew.t80.cap_twp} TWp (GCM range {ssp245.change_lo}% to {ssp245.change_hi}%).?} {?Under SSP5-8.5 it changes by {ssp585.change_pct}% to {ssp585.ew.t80.cap_twp_m} TWp (range {ssp585.change_lo}% to {ssp585.change_hi}%, the paired change of each GCM against its own 1995–2014 total; Fig. 5A).?} {?With robust nitrogen, the SSP5-8.5 potential changes by {ssp585r.change_pct}% to {ssp585r.ew.t80.cap_twp_m} TWp (range {ssp585r.change_lo}% to {ssp585r.change_hi}%), {fut.n_compare}, and mean GCR~max~ changes by {ssp585r.gcr_wheat_delta} for wheat, {ssp585r.gcr_pearl_millet_delta} for pearl millet, {ssp585r.gcr_chickpea_delta} for chickpea and {ssp585r.gcr_groundnut_delta} for groundnut (Fig. 7A,B,D).?} {?At least four of five GCMs agree on the sign of the change in GCR~max~ on {ssp245.agree4_share}% of the eligible land under SSP2-4.5 and {ssp585.agree4_share}% under SSP5-8.5.?} {?Mean GCR~max~ in the east-west layout changes by {ssp585.gcr_wheat_delta} for wheat, {ssp585.gcr_pearl_millet_delta} for pearl millet, {ssp585.gcr_chickpea_delta} for chickpea and {ssp585.gcr_groundnut_delta} for groundnut (Fig. 7B), and pearl millet in the north-west loses most (Fig. 7C,D).?}`));
    add(PF(`{?${fill.has("ssp585r.change_pct") ? "With calibrated nitrogen, climate" : "Climate"} barely changes capacity but lowers energy: annual energy changes by {ssp585.energy_change_pct}% to {ssp585.ew.t80.energy_pwh} PWh, and specific yield by {ssp585.sy_change_pct}%. Most of this loss comes from lower irradiance in the climate models ({ssp585.irr_change_pct}%); the remainder ({ssp585.pr_change_pct}%) reflects lower module efficiency at higher temperature.?} {?With robust nitrogen, energy changes by {ssp585r.energy_change_pct}% to {ssp585r.ew.t80.energy_pwh} PWh.?} These changes include the effect of higher CO~2~ on the crops (Section 4.3). Change maps by crop and layout are in Figs. S8 and S9.`));
    add(FIGAUTO(FIGS + "fig_india_deltamain_thr80.png", 600, fill.has("ssp585r.change_pct")
      ? "Change by 2041–2060 against 1995–2014 at relative yield ≥ 0.80. (A) National capacity by layout and (B) mean largest ground coverage ratio by crop, east-west layout; white, SSP2-4.5 (intermediate emissions) with calibrated nitrogen; grey, SSP5-8.5 (high emissions) with calibrated nitrogen; black, SSP5-8.5 with robust nitrogen (the lower ratio of the calibrated and recommended nitrogen runs), each against its own 1995–2014 case; bars and symbols are the median, whiskers the range of the five paired changes of the climate models. (C, D) Change in capacity density under SSP5-8.5, east-west layout, median of five climate models, interpolated for display, with calibrated (C) and robust (D) nitrogen."
      : "Change by 2041–2060 against 1995–2014 at relative yield ≥ 0.80 with calibrated nitrogen. (A) National capacity by layout and (B) mean largest ground coverage ratio by crop, east-west layout; open symbols, SSP2-4.5 (intermediate emissions), filled symbols, SSP5-8.5 (high emissions), with the range of the five paired changes of the climate models. (C, D) Change in capacity density, east-west layout, median of five climate models, interpolated for display, for SSP2-4.5 (C) and SSP5-8.5 (D)."));
  }

  // screening economics (src/economics.py): cost-supply curve and the cost of keeping the crop
  const ECON = fill.has("econ.crop_value_bn");
  const nclim = 4 + (ROB ? 1 : 0) + ((fill.has("ssp245.change_pct") || fill.has("ssp585.change_pct")) ? 1 : 0);
  if (ECON) {
    add(H2(`3.${nclim} Screening economics`));
    add(PF(`At the ceiling tariff of Rs {econ.tariff_ceiling} per kWh, an eligible hectare under the robust east-west case would earn about Rs {econ.rev_per_ha_lakh} lakh a year from electricity (1 lakh = 100,000), against a gross crop value of Rs {econ.crop_value_per_ha_lakh} lakh on the same land, so electricity would be worth about {econ.ratio_rev_crop} times the crop. The yield rule is what prevents full conversion: at τ = 0.80 the crop loss is at most Rs {econ.crop_loss_max_bn} billion a year, one fifth of the Rs {econ.crop_value_bn} billion of gross crop value on the eligible land.`));
    add(PF(`Whether the electricity can be sold at that tariff depends on the premium of the elevated frame (Fig. ${L.nextFig()}). With no premium, the energy-weighted LCOE is Rs {econ.lcoe_0} per kWh and {econ.share_ceil_0}% of the capacity ({econ.twp_ceil_0} TWp) costs less than the ceiling tariff. At the ministry's 25% premium the LCOE is Rs {econ.lcoe_25} per kWh and no capacity clears the ceiling; at 38% it is Rs {econ.lcoe_38}. The auction price leaves only {econ.be_ceil_pct}% headroom below the ceiling, so a larger premium needs a tariff adder: Rs {econ.adder_25} per kWh at 25%, Rs {econ.adder_30} at 30% and Rs {econ.adder_38} at 38%.`));
    add(FIGAUTO("../../results/figures/fig_economics.png", 450,
      "Cost-supply curve of the yield-constrained agrivoltaic potential, east-west layout, relative yield ≥ 0.80, 1995–2014, robust nitrogen case, slope ≤ 5%. Cells are ordered by levelised cost of electricity. Lines are medians of five climate models and bands their range; colours show the cost premium of the elevated structure over ground-mounted photovoltaics. Horizontal lines mark the ceiling tariff and the discovered auction price of the Gujarat farmer solar scheme."));
    add(PF(`Per hectare, even the adder at a 25% premium is about Rs {econ.adder25_per_ha_lakh} lakh a year, many times the Rs {econ.crop_value_per_ha_lakh} lakh of crop value that the yield rule protects. Crop revenue alone therefore cannot pay for elevated frames; the case for them rests on keeping land in food production (Section 4.4).`));
  }

  // sensitivity (review comment M6): one assumption changed at a time, from src/make_numbers.py sens_numbers
  if (fill.has("sens.base.cap")) {
    const nsec = nclim + (ECON ? 1 : 0);
    add(H2(`3.${nsec} Sensitivity`));
    add(PF(`Apart from the array layout, the yield threshold is the strongest lever on the potential (Table 5): moving τ from 0.80 to 0.66 or 0.90 changes capacity by {sens.thr66.chg}% and {sens.thr90.chg}%. Calibrated nitrogen alone changes it by {sens.n_calib.chg}% and dropping the slope limit by {sens.slope_none.chg}%, while module efficiency of 20% or 24% instead of 22% changes capacity and energy by about ±9%.{? Applying the threshold season by season, in at least 16 of 20 seasons, changes capacity by {sens.season.chg}%.?} The spread of the five GCMs, {sens.base.range} TWp, is small against all of these, so the choice of rule and management matters far more than the climate model.`));
    const R = (lab, k, basis) => fill.has(`sens.${k}.cap`) ? [[lab, basis, fill(`{sens.${k}.cap}`), k === "base" ? "–" : fill(`{sens.${k}.chg}`), fill.has(`sens.${k}.en`) ? fill(`{sens.${k}.en}`) : "–"]] : [];
    const rows = [
      ...R(`Base: ${ROB ? "robust nitrogen" : "calibrated nitrogen"}, east-west, τ = 0.80, slope ≤ 5%`, "base",
        `Japanese threshold ${cite("maff")}; 5% PV slope limit for India ${cite("deshmukh")}`),
      ...R("Threshold τ = 0.66", "thr66", `DIN SPEC 91434 minimum ${cite("din")}`),
      ...R("Threshold τ = 0.90", "thr90", `French decree ${cite("decret")}`),
      ...R("No slope limit", "slope_none", "No terrain screening"),
      ...R("Slope ≤ 10%", "slope_le10", "Relaxed terrain limit"),
      ...(ROB ? R("Calibrated nitrogen alone (upper bound)", "n_calib", "State-calibrated nitrogen, Section 2.4") : []),
      ...R("Module efficiency 20%", "eta20", `Older modules; 2025 mass production 21.7% (PERC) ${cite("itrpv")}`),
      ...R("Module efficiency 24%", "eta24", `Back-contact modules, 24.1% in 2025 ${cite("itrpv")}`),
      ...R("South-facing layout", "south", "Alternative design, Section 2.2"),
      ...R("Vertical layout, GCR ≤ 0.6", "vertical", "Alternative design, Section 2.2"),
      ...R("Vertical layout, no DIN cap", "vertical_nodin", `15% land-loss limit removed ${cite("din")}`),
      ...R("Threshold met in ≥ 16 of 20 seasons", "season", `Rules judge single seasons ${cite("din", "decret")}; one failure in five tolerated`),
      ...R("Radiation not corrected (energy only)", "rad_off", "NEX-GDDP radiation as supplied, Supplementary Section S12"),
    ];
    if (fill.has("sens.base.range")) rows.push(["Range of five GCMs (base case)", "CMIP6 ensemble, Section 2.3", fill("{sens.base.range}"), "–", "–"]);
    add(TABLE("Sensitivity of the national APV potential, 1995–2014: one assumption changed at a time from the base case, with the basis of each tested value.",
      ["Case", "Basis of the tested value", "Capacity, TWp", "Change, %", "Energy, PWh yr^−1^"], rows, [2900, 2900, 1100, 1000, 1426],
      "Five-GCM median. Module efficiency scales capacity and energy in proportion, because GCR~max~ depends on shade, not on the module rating."));
  }
}
module.exports = { addResults };
