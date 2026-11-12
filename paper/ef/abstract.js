// Earth's Future version: abstract (< 250 words), Key Points (<= 140 characters, no acronyms), Plain Language Summary.
const L = require("./lib.js");
const { PF, H3, fill, P } = L;

function abstractText() {
  return [
    "Growing crops under solar panels could ease the competition between food and energy for land, but national estimates of agrivoltaic potential assume fixed power densities and do not test whether crops keep their yield.",
    "To our knowledge, this is the first yield-constrained national potential for India. A strip-resolved light model for three array layouts drives crop models of wheat, chickpea, pearl millet and groundnut on 2977 grid cells, under five downscaled climate models for 1995–2014 and 2041–2060 and with nitrogen calibrated to observed state yields.",
    "For each cell we found the largest ground coverage ratio (GCR) that keeps relative yield at or above 0.66, 0.80 or 0.90, the thresholds of German, Japanese and French rules.",
    "With the lower of calibrated and recommended nitrogen, cropland with slopes up to 5% could host {head.cap_twp_m} terawatts peak (TWp) of east-west elevated arrays at 80% relative yield on {head.land_mha} million hectares ({robust.ew.t80.energy_pwh} petawatt-hours per year). The crop models were more shade-tolerant than field observations; rescaled to them, capacity is {field.ew.t80.cap_twp} TWp, so we report {field.ew.t80.cap_twp}–{head.cap_twp_m} TWp as a technical potential, not a forecast.",
    "Feasible GCR averaged {head.gcr_cereals} for cereals but {head.gcr_legumes} for legumes, and low nitrogen hid part of the shade loss.",
    "Under the high-emission pathway SSP5-8.5, capacity changed by {fut.change_pct}% and energy by {fut.energy_change_pct}%, " + (fill.has("fut.size") && fill("{fut.size}") !== "small" ? "from lower capacity and irradiance." : "through lower irradiance."),
    "Screening costs show that elevated frames need a tariff adder of Indian rupees (Rs) {econ.adder_25}–{econ.adder_38} per kWh, far above the crop value protected, so support should be tied to a yield threshold.",
  ].join(" ");
}
function keyPoints() {
  return [
    "If crops must keep 80% of their yield, Indian farmland could host {field.ew.t80.cap_twp} to {head.cap_twp_m} terawatts peak of elevated solar",
    "Allowed panel density is about twice as high for cereals as for legumes, and low fertiliser use makes crops look more shade tolerant",
    "Mid-century climate {fut.kp_phrase}, but raised frames need a tariff top-up that crop income cannot cover",
  ];
}
function plainSummary() {
  return `Solar farms compete with food crops for land. Panels can be raised above a field so that both share the sunlight, but a crop only does well if enough light gets through. We built a computer model of the light under three panel layouts and linked it to crop models for wheat, chickpea, pearl millet and groundnut across India. For each place we asked how many panels fit if the crop must still give at least 80% of its normal harvest. Under that rule, Indian cropland could host between {field.ew.t80.cap_twp} and {head.cap_twp_m} terawatts of solar capacity, a technical figure that ignores grid, finance and land ownership. Wheat and pearl millet tolerate about twice as many panels as chickpea and groundnut, and crops grown with little fertiliser seem to cope with shade better than they really would. ${fill.has("fut.size") && fill("{fut.size}") !== "small" ? "Climate change by mid-century changes how many panels fit by {fut.change_pct}% and the electricity they produce by {fut.energy_change_pct}%." : "Climate change by mid-century barely changes how many panels fit, but it slightly reduces the electricity they produce."} Raised frames cost more than ground-mounted panels, so farmers would need a higher electricity price, a gap that the value of the crop cannot cover. Linking any support to a yield rule would keep the land in food production.`;
}
const KEYWORDS = ["Agrivoltaics", "Land use", "Crop model", "Food-energy trade-off", "Climate change", "India"];
function addAbstract(add) {
  const wc = t => t.replace(/\^[^^]*\^|~[^~]*~/g, "").split(/\s+/).filter(Boolean).length;
  const text = fill(abstractText());
  console.log(wc(text) > 249 ? `WARNING abstract ${wc(text)} words` : `abstract: ${wc(text)} words`);
  keyPoints().forEach((k, i) => { const t = fill(k); console.log(`key point ${i + 1}: ${t.length} characters${t.length > 140 ? "  TOO LONG" : ""}`); });
  console.log(`plain language summary: ${wc(fill(plainSummary()))} words`);
  add(H3("Key Points:"));
  keyPoints().forEach(k => add(P("• " + fill(k))));
  add(H3("Abstract"));
  add(P(text));
  add(H3("Plain Language Summary"));
  add(P(fill(plainSummary())));
}
module.exports = { addAbstract, abstractText, KEYWORDS };
