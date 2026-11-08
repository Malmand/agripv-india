// Abstract (<= 250 words; background, methods, results, implications), keywords and highlights (front matter).
// Numbers are {key} placeholders from results/potential/numbers.json (src/make_numbers.py). The headline uses the
// head.* keys, which switch to the robust case when it exists; head.is_robust picks the matching wording.
const fs = require("fs");
const L = require("./lib.js");
const { PF, H3, fill, P } = L;

function abstractText() {
  const robust = fill.has("head.is_robust") && fill("{head.is_robust}") === "yes";
  const head = robust
    ? "In the robust case (lower of calibrated and recommended nitrogen), cropland with slopes up to 5% could host {head.cap_twp_m} terawatts peak (TWp) of east-west elevated arrays at 80% relative yield on {head.land_mha} million hectares ({robust.ew.t80.energy_pwh} petawatt-hours per year). The crop models were more shade-tolerant than field observations; rescaled to them, capacity is {field.ew.t80.cap_twp} TWp, so we report {field.ew.t80.cap_twp}–{head.cap_twp_m} TWp as a technical potential, not a forecast."
    : "With calibrated nitrogen, cropland with slopes up to 5% could host {head.cap_twp_m} TWp of east-west elevated arrays at 80% relative yield on {head.land_mha} Mha, before grid, economic and land-tenure limits. This is an upper bound: low nitrogen rates hide part of the shade loss.";
  return [
    "National agrivoltaic potential estimates, including those for India, assume fixed power densities and do not test whether crops keep their yield.",
    "To our knowledge, this is the first yield-constrained national potential for India. We coupled a strip-resolved light model for three array layouts with crop models of wheat, chickpea, pearl millet and groundnut on 2977 cells of a 0.25° grid, driven by five downscaled climate models for 1995–2014 and 2041–2060, with nitrogen calibrated to observed state yields.",
    "For each cell we found the largest ground coverage ratio (GCR) that keeps relative yield at or above 0.66, 0.80 or 0.90, the thresholds of German, Japanese and French rules.",
    head,
    "The feasible GCR averaged {head.gcr_cereals} for cereals but {head.gcr_legumes} for legumes.",
    robust
      ? "Calibrated nitrogen alone gives {main.cap_twp_m} TWp, an upper bound, because low nitrogen hides shade loss."
      : "Wheat that met the threshold even at the densest array lay mostly in states calibrated at 60 kg N ha^−1^ or less.",
    "Under the high-emission pathway SSP5-8.5 (calibrated nitrogen), capacity changed by {ssp585.change_pct}% but energy by {ssp585.energy_change_pct}%, through lower irradiance.",
    "Screening costs show elevated frames need a tariff adder of Indian rupees (Rs) {econ.adder_25}–{econ.adder_38} per kWh; tying it to a relative-yield threshold with crop-specific density caps could suit India's farm-based solar schemes.",
  ].join(" ");
}

const KEYWORDS = ["Agrivoltaics", "Land use", "Crop model", "Ground coverage ratio", "Climate change", "India"];

function addAbstract(add) {
  const text = fill(abstractText());
  const words = text.replace(/\^[^^]*\^|~[^~]*~/g, "").split(/\s+/).filter(Boolean).length;
  if (words > 250) console.log(`WARNING abstract has ${words} words (> 250)`);
  else console.log(`abstract: ${words} words`);
  add(H3("Abstract"));
  add(P(text));
  add(H3("Keywords"));
  add(P(KEYWORDS.join("; ")));
}
module.exports = { addAbstract, abstractText, KEYWORDS };
