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
  add(H1("3. Results"));

  // 3.1
  add(H2("3.1. Model evaluation"));
  add(PF(`Calibrating nitrogen by state improved the simulated open-field yields of the two cereals (Fig. S1). For wheat, the correlation between simulated and observed state yields rose from r = {calib.wheat.before.r} to {calib.wheat.after.r} and the area-weighted mean absolute percentage error fell from {calib.wheat.before.mape}% to {calib.wheat.after.mape}% ({calib.wheat.after.n} states). Pearl millet improved less, from r = {calib.pearl_millet.before.r} to {calib.pearl_millet.after.r} and from {calib.pearl_millet.before.mape}% to {calib.pearl_millet.after.mape}% ({calib.pearl_millet.after.n} states), because yields in the south remained over-predicted even at the lowest nitrogen level. The light model reproduced the pvlib view factors closely and the light measured over the whole Jodhpur system, but over-estimated the light directly below the modules under low winter sun (Figs. S2 and S3).`));

  // 3.2 to 3.4: the robust case (minimum GCR_max of calibrated and recommended nitrogen) is the main case;
  // calibrated nitrogen alone is the upper bound, compared in 3.4 (its maps and state chart: Figs. S4, S5).
  const ROB = fill.has("robust.change_pct");
  const C = ROB ? "robust" : "hist";
  const CASE = ROB ? "robust nitrogen case (smaller GCR~max~ of calibrated and recommended nitrogen in each cell)" : "calibrated nitrogen (upper bound)";
  const STG = ROB ? "historical_current_robust" : "historical_current";

  // 3.2
  add(H2("3.2. Feasible ground coverage ratio by crop and layout"));
  add(PF(`Cereals tolerate about twice the panel density of legumes (Fig. 3). In the east-west layout, the area-weighted mean GCR~max~ at RY ≥ 0.80 was {${C}.ew.t80.gcr_wheat} for wheat and {${C}.ew.t80.gcr_pearl_millet} for pearl millet, but {${C}.ew.t80.gcr_chickpea} for chickpea and {${C}.ew.t80.gcr_groundnut} for groundnut. The south-facing array allowed the lowest densities for every crop, most clearly for the rabi crops wheat ({${C}.south.t80.gcr_wheat}) and chickpea ({${C}.south.t80.gcr_chickpea}), whose grain fills under low winter sun. Vertical rows allowed densities close to the east-west layout and reached the DIN SPEC 91434 cap of 0.6 on at least {${C}.vertical.t80.atcap_pearl_millet}% of the pearl millet area. Within each crop, GCR~max~ varied strongly across the country, and few cells met the threshold at the densest GCR simulated (east-west: {${C}.ew.t80.atcap_wheat}% of the wheat and {${C}.ew.t80.atcap_chickpea}% of the chickpea area).${ROB ? "" : " These wheat cells lie mostly in states with low calibrated nitrogen, which points to nitrogen masking rather than true shade tolerance (Section 4.2)."}`));
  add(FIGAUTO(FIGS + `fig_india_gcrmax_${STG}_thr80.png`, 600,
    `Largest ground coverage ratio (GCR~max~) that keeps relative yield at or above 0.80, by crop (columns) and layout (rows), 1995–2014, ${CASE}; vertical GCR~max~ capped at 0.6 (DIN SPEC 91434 land-loss limit). Cell values are the median over five GCMs, interpolated for display; the number in each panel is the eligible-area-weighted mean with the GCM range, the mean GCR~max~ used throughout the text. Eligible area is the MapSPAM harvested area times the share of the cell with slope ≤ 5%. Cells that still meet the threshold at the densest GCR simulated (0.7 for cereals, 0.5 for legumes) enter at that limit. State and union-territory boundaries: DataMeet India community, States/Admin2 (https://github.com/datameet/maps, CC BY 4.0).`));

  // 3.3
  add(H2("3.3. National potential"));
  add(PF(`Under the yield rule, Indian cropland could host {${C}.ew.t80.cap_twp_m} TWp of APV (Fig. 4, Table 4). This is the east-west layout at τ = 0.80 on {${C}.ew.t80.land_mha} Mha of cropland with slopes up to 5% (GCM range {${C}.ew.t80.cap_twp_lo}–{${C}.ew.t80.cap_twp_hi} TWp), or {${C}.ew.t80.density} MWp ha^−1^. It would generate {${C}.ew.t80.energy_pwh} PWh per year, about {frame.head_multiple} times India's 2025–26 electricity requirement of {frame.cea_twh} TWh ${cite("cea")}. Seen the other way, 500 GWp at this mean density would occupy only {frame.gw500.land_mha} Mha, {frame.gw500.share}% of the eligible cropland{?, and {supply.gw500_mha} Mha if the densest cells are used first (Fig. S6)?}. Capacity density is highest across the Indo-Gangetic plain and north-western Rajasthan and lowest in the legume-growing Deccan and the south, which follows the crop pattern of Fig. 3.`));
  add(FIGAUTO(FIGS + `fig_india_capmap_${STG}_thr80.png`, 600,
    `Yield-constrained capacity density (MWp per ha of cropland, crops combined) for east-west elevated arrays at RY ≥ 0.80, 1995–2014, ${CASE}, slope ≤ 5%. Cell values are the median over five GCMs; cells with less than 1000 ha of eligible cropland are blank, and the 0.25° values are interpolated for display. The three leading states are labelled with their capacity, and the national total is given in the map.`));
  add(PF(`The layouts rank differently by capacity and by energy (Fig. 5). Vertical rows reached the most capacity, {${C}.vertical.t80.cap_twp_m} TWp with the 0.6 cap, against {${C}.south.t80.cap_twp_m} TWp for the south-facing array. Their specific yield, however, was only {${C}.vertical.t80.sy} kWh kWp^−1^ yr^−1^, against {${C}.ew.t80.sy} for east-west and {${C}.south.t80.sy} for south-facing arrays, so they produced the least energy ({${C}.vertical.t80.energy_pwh} PWh yr^−1^). East-west arrays gave the most energy at every threshold and are used for the headline. The threshold mattered more than the slope rule: capacity was {${C}.ew.t66.cap_twp} TWp at τ = 0.66 and {${C}.ew.t90.cap_twp} TWp at τ = 0.90, while dropping the slope limit raised it only to {${C}.ew.t80.none.cap_twp} TWp.`));
  add(PF(`The potential is concentrated in three states, which hold {${C}.top3_share}% of it: {${C}.top1_state} ({${C}.top1_twp} TWp), {${C}.top2_state} ({${C}.top2_twp} TWp) and {${C}.top3_state} ({${C}.top3_twp} TWp) (Fig. 6).`));
  const cell = (c, lk, tk) => fill(`{${c}.${lk}.${tk}.cap_twp_m} ({${c}.${lk}.${tk}.cap_twp_lo}–{${c}.${lk}.${tk}.cap_twp_hi})`);
  if (ROB) {
    add(TABLE("Yield-constrained APV potential of India for four crops, 1995–2014: robust nitrogen case and calibrated nitrogen alone (upper bound). Slope ≤ 5%; crops combined with double-cropped land counted once; vertical GCR~max~ capped at 0.6.",
      ["Layout", "τ", "Capacity, TWp (robust)", "Capacity, TWp (calibrated)", "Energy, PWh yr^−1^ (robust)", "Energy, PWh yr^−1^ (calibrated)", "MWp ha^−1^ (robust)"],
      LAY.flatMap(([lk, name]) => THR.map(([tk, tv], i) => [i === 0 ? name : "", tv, cell("robust", lk, tk), cell("hist", lk, tk),
        fill(`{robust.${lk}.${tk}.energy_pwh}`), fill(`{hist.${lk}.${tk}.energy_pwh}`), fill(`{robust.${lk}.${tk}.density}`)])),
      [1700, 500, 1550, 1550, 1200, 1200, 1326],
      fill("Median over five GCMs, GCM range in brackets. Land is the eligible crop area, {robust.ew.t80.land_mha} Mha in every case; the threshold and nitrogen act through the density. Vertical rows without the 0.6 cap (robust): {robust.vertical.t66.nodin.cap_twp}, {robust.vertical.t80.nodin.cap_twp} and {robust.vertical.t90.nodin.cap_twp} TWp at τ = 0.66, 0.80 and 0.90.")));
    add(FIGAUTO(FIGS + "fig_india_cases_historical_current_robust.png", 600,
      "National APV capacity (A) and annual energy (B) by layout and relative-yield threshold, 1995–2014, slope ≤ 5%, vertical GCR~max~ capped at 0.6. Filled bars: robust nitrogen case, five-GCM median, error bars the GCM range. Outline bars: calibrated nitrogen alone (upper bound)."));
  } else {
    add(TABLE("Yield-constrained APV potential of India for four crops, 1995–2014 (calibrated nitrogen, an upper bound; slope ≤ 5%; crops combined with double-cropped land counted once; vertical GCR~max~ capped at 0.6).",
      ["Layout", "τ", "Capacity, TWp", "Energy, PWh yr^−1^", "Land, Mha", "MWp ha^−1^"],
      LAY.flatMap(([lk, name]) => THR.map(([tk, tv], i) => [i === 0 ? name : "", tv, cell("hist", lk, tk),
        fill(`{hist.${lk}.${tk}.energy_pwh}`), fill(`{hist.${lk}.${tk}.land_mha}`), fill(`{hist.${lk}.${tk}.density}`)])),
      [2100, 700, 2000, 1600, 1300, 1326],
      fill("Median over five GCMs, GCM range in brackets. Land is the eligible crop area and does not depend on τ; the threshold acts through the density.")));
    add(FIGAUTO(FIGS + "fig_india_capacity_historical_current.png", 450,
      "National APV capacity by layout and relative-yield threshold, 1995–2014, calibrated nitrogen (upper bound), slope ≤ 5%, vertical GCR~max~ capped at 0.6. Bars are the five-GCM median and error bars the GCM range; markers show the cases without a slope limit and with a 10% limit."));
  }
  add(FIGAUTO(FIGS + `fig_india_states_${STG}_thr80.png`, 450,
    `Capacity of the leading states at RY ≥ 0.80 by layout, 1995–2014, ${CASE}, slope ≤ 5%, vertical GCR~max~ capped at 0.6. Bars are the five-GCM median and error bars the GCM range.`));

  // 3.4
  if (ROB) {
    add(H2("3.4. Effect of nitrogen management"));
    add(PF(`With calibrated nitrogen alone, the east-west potential at τ = 0.80 is {main.cap_twp_m} TWp (GCM range {main.cap_twp_lo}–{main.cap_twp_hi}) and {main.energy_pwh} PWh yr^−1^, so the robust case is {robust.reduction_pct}% lower (Table 4, Fig. 5). The change is {robust.south.t80.change_pct}% for the south-facing array and {robust.vertical.t80.change_pct}% for vertical rows, and the largest absolute losses are in {robust.top_states}. The difference comes almost entirely from the cereals: mean GCR~max~ falls from {main.gcr_wheat} to {robust.ew.t80.gcr_wheat} for wheat and from {main.gcr_pearl_millet} to {robust.ew.t80.gcr_pearl_millet} for pearl millet, while the legumes barely change. With calibrated nitrogen, {main.atcap_wheat}% of the east-west wheat area still met the threshold at GCR 0.7; in the robust case {robust.ew.t80.atcap_wheat}% does. These wheat cells lie mostly in states with low calibrated nitrogen, which points to nitrogen masking rather than true shade tolerance (Section 4.2). With calibrated nitrogen the {hist.best_layout} layout also gave the most capacity, {main.cap_twp_m} against {hist.vertical.t80.cap_twp_m} TWp for capped vertical rows. Figs. S4 and S5 show the calibrated-nitrogen maps and state results.`));
  }

  // 3.5
  if (fill.has("ssp245.change_pct") || fill.has("ssp585.change_pct")) {
    add(H2(`3.${fill.has("robust.change_pct") ? 5 : 4}. Mid-century change`));
    add(PF(`The climate runs use calibrated nitrogen, so the changes below are relative to the calibrated 1995–2014 potential of {main.cap_twp_m} TWp.`));
    add(PF(`{?By 2041–2060 under SSP2-4.5, the potential in the east-west layout at τ = 0.80 changes by {ssp245.change_pct}% to {ssp245.ew.t80.cap_twp} TWp (GCM range {ssp245.change_lo}% to {ssp245.change_hi}%), and at least four of five GCMs agree on the sign of the change in GCR~max~ on {ssp245.agree4_share}% of the eligible land.?} {?Under SSP5-8.5 the potential changes by {ssp585.change_pct}% to {ssp585.ew.t80.cap_twp_m} TWp. The GCM range of this change, {ssp585.change_lo}% to {ssp585.change_hi}%, is the range of the five per-GCM paired changes, each GCM's mid-century total against its own 1995–2014 total.?} {?At least four of five GCMs agree on the sign of the change in GCR~max~ (crops combined, which on fixed land is the sign of the change in cell capacity) on {ssp585.agree4_share}% of the eligible land.?} {?Mean GCR~max~ in the east-west layout changes by {ssp585.gcr_wheat_delta} for wheat, {ssp585.gcr_pearl_millet_delta} for pearl millet, {ssp585.gcr_chickpea_delta} for chickpea and {ssp585.gcr_groundnut_delta} for groundnut (Fig. 7); pearl millet in the north-west loses most.?} {?Climate barely changes capacity but lowers energy: annual energy changes by {ssp585.energy_change_pct}% to {ssp585.ew.t80.energy_pwh} PWh, and specific yield by {ssp585.sy_change_pct}%, from {hist.ew.t80.sy} to {ssp585.ew.t80.sy} kWh kWp^−1^ yr^−1^. Most of the loss in specific yield comes from lower irradiance in the climate models (plane-of-array irradiance, front and rear, {ssp585.irr_change_pct}%); the remainder ({ssp585.pr_change_pct}%) reflects lower module efficiency at higher temperature.?} These changes include the effect of higher CO~2~ on the crops (Section 4.4).`));
    const fut = fill.has("ssp245.change_pct") ? "ssp245_current" : "ssp585_current";
    add(FIGAUTO(FIGS + `fig_india_delta_${fut}_thr80.png`, 600,
      `Change in GCR~max~ at RY ≥ 0.80, 2041–2060 under ${fut.startsWith("ssp245") ? "SSP2-4.5" : "SSP5-8.5"} minus 1995–2014, by crop and layout (five-GCM median, interpolated for display).`));
  }

  // sensitivity (review comment M6): one assumption changed at a time, from src/make_numbers.py sens_numbers
  if (fill.has("sens.base.cap")) {
    const nsec = 4 + (ROB ? 1 : 0) + ((fill.has("ssp245.change_pct") || fill.has("ssp585.change_pct")) ? 1 : 0);
    add(H2(`3.${nsec}. Sensitivity`));
    add(PF(`Apart from the array layout, the yield threshold is the strongest lever on the potential (Table 5): moving τ from 0.80 to 0.66 or 0.90 changes capacity by {sens.thr66.chg}% and {sens.thr90.chg}%. Calibrated nitrogen alone changes it by {sens.n_calib.chg}% and dropping the slope limit by {sens.slope_none.chg}%, while module efficiency of 20% or 24% instead of 22%, the span from older modules to 2025 back-contact modules ${cite("itrpv")}, changes capacity and energy by about ±9%.{? Applying the threshold season by season, in at least 16 of 20 seasons, changes capacity by {sens.season.chg}%.?} The spread of the five GCMs, {sens.base.range} TWp, is small against all of these, so the choice of rule and management matters far more than the climate model.`));
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
      ...R("Radiation not corrected (energy only)", "rad_off", "NEX-GDDP radiation as supplied, SM Section S12"),
    ];
    if (fill.has("sens.base.range")) rows.push(["Range of five GCMs (base case)", "CMIP6 ensemble, Section 2.3", fill("{sens.base.range}"), "–", "–"]);
    add(TABLE("Sensitivity of the national APV potential, 1995–2014: one assumption changed at a time from the base case, with the basis of each tested value.",
      ["Case", "Basis of the tested value", "Capacity, TWp", "Change, %", "Energy, PWh yr^−1^"], rows, [2900, 2900, 1100, 1000, 1426],
      "Five-GCM median. Module efficiency scales capacity and energy in proportion, because GCR~max~ depends on shade, not on the module rating."));
  }
}
module.exports = { addResults };
