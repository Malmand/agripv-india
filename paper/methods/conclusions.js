// Section 5 Conclusions (~300 words). Numbers are {key} placeholders from results/potential/numbers.json;
// {? ... ?} sentences need the robust or SSP2-4.5 stage and are dropped until it exists.
const L = require("./lib.js");
const { PF, H1, fill } = L;

function addConclusions(add) {
  add(H1("5. Conclusions"));
  const robust = fill.has("head.is_robust") && fill("{head.is_robust}") === "yes";
  add(PF(`This study mapped the agrivoltaic potential of India under a crop-yield rule, by coupling a strip-resolved light model with calibrated DSSAT crop models for four field crops, three layouts and five climate models. Four conclusions follow.`));
  add(PF(`First, a yield rule sets the density of APV, not the land it can use. On cropland with slopes up to 5%, east-west elevated arrays that keep 80% of the open-field yield reach {head.cap_twp_m} TWp on {head.land_mha} Mha (${robust ? "robust case" : "calibrated nitrogen, an upper bound"}), about {head.density} MWp ha^−1^. This is far above the published Indian estimates, mainly because those exclude field crops or fix a low density. Land is therefore not the constraint on Indian APV; grid access, finance and farmer acceptance are.`));
  add(PF(`Second, the feasible density depends on the crop. The area-weighted GCR~max~ is {head.gcr_cereals} for cereals and {head.gcr_legumes} for legumes, so one national density rule would be too high for pulses and too low for much of the wheat belt. Crop-specific density caps follow directly from the GCR~max~ maps.`));
  add(PF(`Third, nitrogen management changes the answer. Wheat that meets the threshold at the densest array simulated lies mostly in states with low calibrated nitrogen, where the open-field crop is nitrogen-limited and shade costs little extra yield. The calibrated potential is therefore an upper bound. {?Taking the lower GCR~max~ of the calibrated and recommended cases lowers it by {robust.reduction_pct}%, and the share of wheat area that meets the threshold at the densest array falls from {main.atcap_wheat}% to {robust.ew.t80.atcap_wheat}%.?}${robust ? "" : " A robust case with recommended nitrogen [pending: recommended-nitrogen stage] gives the conservative estimate."}`));
  add(PF(`Fourth, mid-century climate barely changes the yield-constrained capacity ({ssp585.change_pct}% under SSP5-8.5) but changes annual energy by {ssp585.energy_change_pct}%, mostly through lower irradiance in the climate models. {?Under SSP2-4.5 the change in capacity is {ssp245.change_pct}%.?} These results include CO~2~ fertilisation, which raises absolute legume yields far more than relative yield.`));
  add(PF(`For policy, India could add to PM-KUSUM a relative-yield threshold of about 0.80, a limit on land lost to the structure and a reference yield that can be checked. Future work should add the microclimate under the panels, correct the radiation of the climate data, test yield rules season by season and add grid and economic limits.`));
}
module.exports = { addConclusions };
