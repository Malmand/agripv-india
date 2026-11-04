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

  // 3.2
  add(H2("3.2. Feasible ground coverage ratio by crop and layout"));
  add(PF(`Fig. 3 maps the largest GCR that keeps RY ≥ 0.80. Here and throughout, a mean GCR~max~ is the eligible-area-weighted mean of the five-GCM median map shown in Fig. 3. In the east-west layout, the mean GCR~max~ was {main.gcr_wheat} for wheat and {main.gcr_pearl_millet} for pearl millet, against {main.gcr_chickpea} for chickpea and {main.gcr_groundnut} for groundnut; pooled by group, it was {hist.ew.t80.gcr_cereals} for the cereals and {hist.ew.t80.gcr_legumes} for the legumes (the values in the graphical abstract). Under the south-facing array the values were {hist.south.t80.gcr_wheat}, {hist.south.t80.gcr_pearl_millet}, {hist.south.t80.gcr_chickpea} and {hist.south.t80.gcr_groundnut}, and under vertical rows {hist.vertical.t80.gcr_wheat}, {hist.vertical.t80.gcr_pearl_millet}, {hist.vertical.t80.gcr_chickpea} and {hist.vertical.t80.gcr_groundnut}, in the same order. Vertical GCR~max~ is capped at 0.6, the density above which the uncultivated strip under the rows exceeds the 15% land-loss limit of DIN SPEC 91434 (Section 4.3). Some cells met the threshold at the densest GCR simulated (0.7 for the cereals, 0.5 for the legumes). In the east-west layout this applied to {main.atcap_wheat}% of the wheat area, but to only {main.atcap_pearl_millet}% of the pearl millet, {main.atcap_chickpea}% of the chickpea and {main.atcap_groundnut}% of the groundnut area. Under vertical rows it applied to {hist.vertical.t80.atcap_wheat}% of the wheat and {hist.vertical.t80.atcap_pearl_millet}% of the pearl millet area before the cap. These wheat cells lie mostly in states with low calibrated nitrogen, which points to nitrogen masking rather than true shade tolerance (Section 4.2).`));
  add(FIGAUTO(FIGS + "fig_india_gcrmax_historical_current_thr80.png", 600,
    "Largest ground coverage ratio (GCR~max~) that keeps relative yield at or above 0.80, by crop (columns) and layout (rows), 1995–2014, calibrated nitrogen; vertical GCR~max~ capped at 0.6 (DIN SPEC 91434 land-loss limit). Cell values are the median over five GCMs; the number in each panel is the area-weighted mean with the GCM range. Eligible area is the MapSPAM harvested area times the share of the cell with slope ≤ 5%. Cells that still meet the threshold at the densest GCR simulated (0.7 for cereals, 0.5 for legumes) enter at that limit. State and union-territory boundaries: DataMeet India community, States/Admin2 (https://github.com/datameet/maps, CC BY 4.0)."));

  // 3.3
  add(H2("3.3. National potential"));
  add(PF(`With calibrated nitrogen, cropland with slopes up to 5% could host {main.cap_twp_m} TWp of the four crops (GCM range {main.cap_twp_lo}–{main.cap_twp_hi}) in the east-west layout at τ = 0.80, on {main.land_mha} Mha of land, with an annual yield of {main.energy_pwh} PWh (Table 4, Fig. 4). This value is an upper bound, because low nitrogen rates hide part of the shade loss in wheat (Section 4.2). ${fill.has("robust.change_pct") ? "The robust estimate in Section 3.4 is the conservative headline." : "The robust estimate, the conservative headline, is pending the recommended-nitrogen stage [pending]."} The upper bound corresponds to {main.density} MWp per hectare of eligible land and to about {frame.main_multiple} times India's 2025–26 electricity requirement of {frame.cea_twh} TWh ${cite("cea")}. At the headline density, 300 GWp would need {frame.gw300.land_mha} Mha ({frame.gw300.share}% of the eligible land) and 500 GWp {frame.gw500.land_mha} Mha ({frame.gw500.share}%). The south-facing array gave {hist.south.t80.cap_twp} TWp and vertical rows {hist.vertical.t80.cap_twp} TWp with GCR~max~ capped at 0.6, so the {hist.best_layout} layout gave the most capacity. Without the cap, vertical rows would give {hist.vertical.t80.nodin.cap_twp} TWp ({hist.din_gain_pct}% more) and the most capacity of the three layouts. National specific yield at GCR~max~, annual energy divided by capacity (Table 4), was {hist.ew.t80.sy} kWh kWp^−1^ yr^−1^ for the east-west layout, {hist.south.t80.sy} for the south-facing array and {hist.vertical.t80.sy} for vertical rows; at the area-weighted median cell the values were {hist.ew.sy_med}, {hist.south.sy_med} and {hist.vertical.sy_med}.`));
  add(PF(`In the east-west layout, capacity was {hist.ew.t66.cap_twp} TWp at τ = 0.66 and {hist.ew.t90.cap_twp} TWp at τ = 0.90. Without a slope limit it was {hist.ew.t80.none.cap_twp} TWp, and with a 10% limit {hist.ew.t80.le10.cap_twp} TWp. The leading states at τ = 0.80 are {hist.top1_state} ({hist.top1_twp} TWp), {hist.top2_state} ({hist.top2_twp} TWp) and {hist.top3_state} ({hist.top3_twp} TWp) (Fig. 5).`));
  const cell = (lk, tk) => fill(`{hist.${lk}.${tk}.cap_twp_m} ({hist.${lk}.${tk}.cap_twp_lo}–{hist.${lk}.${tk}.cap_twp_hi})`);
  add(TABLE("Yield-constrained APV potential of India for four crops, 1995–2014 (calibrated nitrogen, an upper bound; slope ≤ 5%; crops combined with double-cropped land counted once; vertical GCR~max~ capped at 0.6).",
    ["Layout", "τ", "Capacity, TWp", "Energy, PWh yr^−1^", "Land, Mha", "MWp ha^−1^"],
    LAY.flatMap(([lk, name]) => THR.map(([tk, tv], i) => [i === 0 ? name : "", tv, cell(lk, tk),
      fill(`{hist.${lk}.${tk}.energy_pwh}`), fill(`{hist.${lk}.${tk}.land_mha}`), fill(`{hist.${lk}.${tk}.density}`)])),
    [2100, 700, 2000, 1600, 1300, 1326],
    fill("Median over five GCMs, GCM range in brackets. Land is the eligible crop area and does not depend on τ; the threshold acts through the density. Vertical rows without the 0.6 cap: {hist.vertical.t66.nodin.cap_twp}, {hist.vertical.t80.nodin.cap_twp} and {hist.vertical.t90.nodin.cap_twp} TWp at τ = 0.66, 0.80 and 0.90.")));
  add(FIGAUTO(FIGS + "fig_india_capacity_historical_current.png", 450,
    "National APV capacity by layout and relative-yield threshold, 1995–2014, calibrated nitrogen (upper bound), slope ≤ 5%, vertical GCR~max~ capped at 0.6. Bars are the five-GCM median and error bars the GCM range; markers show the cases without a slope limit and with a 10% limit."));
  add(FIGAUTO(FIGS + "fig_india_states_historical_current_thr80.png", 450,
    "Capacity of the leading states at RY ≥ 0.80 by layout, 1995–2014, calibrated nitrogen (upper bound), slope ≤ 5%, vertical GCR~max~ capped at 0.6. Bars are the five-GCM median and error bars the GCM range."));

  // 3.4
  if (fill.has("robust.change_pct")) {
    add(H2("3.4. Effect of nitrogen management"));
    add(PF(`{?When each cell takes the smaller GCR~max~ of the calibrated and recommended nitrogen cases, the potential in the east-west layout at τ = 0.80 falls by {robust.reduction_pct}% to {robust.ew.t80.cap_twp_m} TWp (GCM range {robust.ew.t80.cap_twp_lo}–{robust.ew.t80.cap_twp_hi}).?} {?The change is {robust.south.t80.change_pct}% for the south-facing array and {robust.vertical.t80.change_pct}% for vertical rows.?} {?The largest absolute losses are in {robust.top_states}.?}`));
  }

  // 3.5
  if (fill.has("ssp245.change_pct") || fill.has("ssp585.change_pct")) {
    add(H2(`3.${fill.has("robust.change_pct") ? 5 : 4}. Mid-century change`));
    add(PF(`{?By 2041–2060 under SSP2-4.5, the potential in the east-west layout at τ = 0.80 changes by {ssp245.change_pct}% to {ssp245.ew.t80.cap_twp} TWp (GCM range {ssp245.change_lo}% to {ssp245.change_hi}%), and at least four of five GCMs agree on the sign of the change in GCR~max~ on {ssp245.agree4_share}% of the eligible land.?} {?Under SSP5-8.5 the potential changes by {ssp585.change_pct}% to {ssp585.ew.t80.cap_twp_m} TWp. The GCM range of this change, {ssp585.change_lo}% to {ssp585.change_hi}%, is the range of the five per-GCM paired changes, each GCM's mid-century total against its own 1995–2014 total.?} {?At least four of five GCMs agree on the sign of the change in GCR~max~ (crops combined, which on fixed land is the sign of the change in cell capacity) on {ssp585.agree4_share}% of the eligible land.?} {?Mean GCR~max~ in the east-west layout changes by {ssp585.gcr_wheat_delta} for wheat, {ssp585.gcr_pearl_millet_delta} for pearl millet, {ssp585.gcr_chickpea_delta} for chickpea and {ssp585.gcr_groundnut_delta} for groundnut (Fig. 6); pearl millet in the north-west loses most.?} {?Climate barely changes capacity but lowers energy: annual energy changes by {ssp585.energy_change_pct}% to {ssp585.ew.t80.energy_pwh} PWh, and specific yield by {ssp585.sy_change_pct}%, from {hist.ew.t80.sy} to {ssp585.ew.t80.sy} kWh kWp^−1^ yr^−1^. Most of the loss in specific yield comes from lower irradiance in the climate models (plane-of-array irradiance, front and rear, {ssp585.irr_change_pct}%); the remainder ({ssp585.pr_change_pct}%) reflects lower module efficiency at higher temperature.?} These changes include the effect of higher CO~2~ on the crops (Section 4.4).`));
    const fut = fill.has("ssp245.change_pct") ? "ssp245_current" : "ssp585_current";
    add(FIGAUTO(FIGS + `fig_india_delta_${fut}_thr80.png`, 600,
      `Change in GCR~max~ at RY ≥ 0.80, 2041–2060 under ${fut.startsWith("ssp245") ? "SSP2-4.5" : "SSP5-8.5"} minus 1995–2014, by crop and layout (five-GCM median).`));
  }
}
module.exports = { addResults };
