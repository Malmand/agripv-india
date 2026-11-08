// Abstract (<= 250 words; background, methods, results, implications), keywords and highlights (front matter).
// Numbers are {key} placeholders from results/potential/numbers.json (src/make_numbers.py). The headline uses the
// head.* keys, which switch to the robust case when it exists; head.is_robust picks the matching wording.
const fs = require("fs");
const L = require("./lib.js");
const { PF, H3, fill, P } = L;

function abstractText() {
  const robust = fill.has("head.is_robust") && fill("{head.is_robust}") === "yes";
  const head = robust
    ? "In the robust case, in which each cell takes the lower density of calibrated and recommended nitrogen, cropland with slopes up to 5% could host {head.cap_twp_m} TWp of east-west elevated arrays at 80% relative yield on {head.land_mha} Mha ({robust.ew.t80.energy_pwh} PWh yr^−1^). The crop models were more shade-tolerant than field observations; rescaling them to the observations gives {field.ew.t80.cap_twp} TWp, so we report {field.ew.t80.cap_twp}–{head.cap_twp_m} TWp as a technical potential, not a deployment forecast. Vertical rows gave slightly more capacity but less energy."
    : "With calibrated nitrogen, cropland with slopes up to 5% could host {head.cap_twp_m} TWp of east-west elevated arrays at 80% relative yield on {head.land_mha} Mha, before grid, economic and land-tenure limits. This is an upper bound: low nitrogen rates hide part of the shade loss.";
  return [
    "National estimates of India's agrivoltaic potential assume fixed power densities and do not test whether crops under the panels keep their yield.",
    "We coupled a strip-resolved light model for three array layouts with the DSSAT models of wheat, chickpea, pearl millet and groundnut on 2977 cells of a 0.25° grid, driven by five CMIP6 climate models for 1995–2014 and 2041–2060, with nitrogen calibrated by state against observed yields.",
    "For each cell we found the largest ground coverage ratio (GCR) that keeps relative yield at or above 0.66, 0.80 or 0.90, the thresholds of German, Japanese and French rules.",
    head,
    "The feasible GCR averaged {head.gcr_cereals} for cereals but {head.gcr_legumes} for legumes.",
    robust
      ? "Calibrated nitrogen alone gives {main.cap_twp_m} TWp, an upper bound: there wheat met the threshold even at the densest array on {main.atcap_wheat}% of its area, against {robust.ew.t80.atcap_wheat}% in the robust case."
      : "Wheat that met the threshold even at the densest array lay mostly in states calibrated at 60 kg N ha^−1^ or less.",
    "Under SSP5-8.5 (calibrated nitrogen), capacity changed by {ssp585.change_pct}% but annual energy by {ssp585.energy_change_pct}%, mainly through lower irradiance.",
    "India could consider a relative-yield threshold with crop-specific density caps for farm-based solar schemes.",
  ].join(" ");
}

const KEYWORDS = ["Agrivoltaics", "Land use", "Crop model", "Ground coverage ratio", "Climate change", "India"];

function addAbstract(add) {
  const text = fill(abstractText());
  const words = text.replace(/\^[^^]*\^|~[^~]*~/g, "").split(/\s+/).filter(Boolean).length;
  if (words > 250) console.log(`WARNING abstract has ${words} words (> 250)`);
  else console.log(`abstract: ${words} words`);
  const hl = fs.existsSync("highlights.txt") ? fs.readFileSync("highlights.txt", "utf8").split("\n").filter(l => l.trim()) : [];
  if (hl.length) {
    add(H3("Highlights"));
    hl.forEach(h => add(P(`• ${h}`, { indent: { left: 400 } })));
  }
  add(H3("Abstract"));
  add(P(text));
  add(H3("Keywords"));
  add(P(KEYWORDS.join("; ")));
}
module.exports = { addAbstract, abstractText, KEYWORDS };
