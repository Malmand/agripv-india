// Sensitivity table (one assumption changed at a time), shared by the main text and the Supporting Information.
const L = require("./lib.js");
const { cite, fill, TABLE } = L;
function addSensTable(add) {
  const ROB = fill.has("head.is_robust") && fill("{head.is_robust}") === "yes";
    const R = (lab, k, basis) => fill.has(`sens.${k}.cap`) ? [[lab, basis, fill(`{sens.${k}.cap}`), k === "base" ? "–" : fill(`{sens.${k}.chg}`), fill.has(`sens.${k}.en`) ? fill(`{sens.${k}.en}`) : "–"]] : [];
  const rows = [
    ...R(`Base: ${ROB ? "robust nitrogen" : "calibrated nitrogen"}, east-west, τ = 0.80, slope ≤ 5%`, "base",
      `Japanese threshold ${cite("maff")}; 5% PV slope limit for India ${cite("deshmukh")}`),
    ...R("Threshold τ = 0.66", "thr66", `DIN SPEC 91434 minimum ${cite("din")}`),
    ...R("Threshold τ = 0.90", "thr90", `French decree ${cite("decret")}`),
    ...R("No slope limit", "slope_none", "No terrain screening"),
    ...R("Slope ≤ 10%", "slope_le10", "Relaxed terrain limit"),
    ...(ROB ? R("Calibrated nitrogen alone (less conservative)", "n_calib", "State-calibrated nitrogen, Section 2.4") : []),
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
module.exports = { addSensTable };
