// Builds Methods_AgriPV_India.docx (Applied Energy style manuscript section)
const fs = require("fs");
const d = require("docx");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, BorderStyle, ShadingType, ImageRun, TabStopType, PageBreak, Math: OMath, MathRun,
  MathSubScript, MathFraction, MathSum, MathSuperScript, Footer, PageNumber, LineRuleType,
} = d;

const FONT = "Arial";
const path = require("path");
process.chdir(__dirname);   // builders work from any directory (figures and outputs are relative to here)
// ---------- citations, numbered by first use ----------
const REF = {
  dupraz: "Dupraz C, Marrou H, Talbot G, Dufour L, Nogier A, Ferard Y. Combining solar photovoltaic panels and food crops for optimising land use: Towards new agrivoltaic schemes. Renew Energy 2011;36:2725–32. https://doi.org/10.1016/j.renene.2011.03.005.",
  amaducci: "Amaducci S, Yin X, Colauzzi M. Agrivoltaic systems to optimise land use for electric energy production. Appl Energy 2018;220:545–61. https://doi.org/10.1016/j.apenergy.2018.03.081.",
  valle: "Valle B, Simonneau T, Sourd F, Pechier P, Hamard P, Frisson T, et al. Increasing the total productivity of a land by combining mobile photovoltaic panels and food crops. Appl Energy 2017;206:1495–507. https://doi.org/10.1016/j.apenergy.2017.09.113.",
  bellone: "Bellone Y, Croci M, Impollonia G, Nik Zad A, Colauzzi M, Campana PE, Amaducci S. Simulation-based decision support for agrivoltaic systems. Appl Energy 2024;369:123490. https://doi.org/10.1016/j.apenergy.2024.123490.",
  neesham: "Neesham-McTiernan TH, Randle-Boggis RJ, Buckley AR, Hartley SE. The spatial potential for agrivoltaics to address energy-agriculture land use conflicts in Great Britain. Appl Energy 2025;385:125527. https://doi.org/10.1016/j.apenergy.2025.125527.",
  zainali: "Zainali S, Ma Lu S, Fernández-Solas Á, Cruz-Escabias A, Fernández EF, Zidane TEK, et al. Modelling, simulation, and optimisation of agrivoltaic systems: a comprehensive review. Appl Energy 2025;386:125558. https://doi.org/10.1016/j.apenergy.2025.125558.",
  jones: "Jones JW, Hoogenboom G, Porter CH, Boote KJ, Batchelor WD, Hunt LA, et al. The DSSAT cropping system model. Eur J Agron 2003;18:235–65. https://doi.org/10.1016/S1161-0301(02)00107-7.",
  hoogenboom: "Hoogenboom G, Porter CH, Boote KJ, Shelia V, Wilkens PW, Singh U, et al. Decision Support System for Agrotechnology Transfer (DSSAT) Version 4.8. Gainesville, FL: DSSAT Foundation; 2021. https://dssat.net.",
  pvlib: "Anderson KS, Hansen CW, Holmgren WF, Jensen AR, Mikofski MA, Driesse A. pvlib python: 2023 project update. J Open Source Softw 2023;8:5994. https://doi.org/10.21105/joss.05994.",
  thrasher: "Thrasher B, Wang W, Michaelis A, Melton F, Lee T, Nemani R. NASA Global Daily Downscaled Projections, CMIP6. Sci Data 2022;9:262. https://doi.org/10.1038/s41597-022-01393-4.",
  meinshausen: "Meinshausen M, Nicholls ZRJ, Lewis J, Gidden MJ, Vogel E, Freund M, et al. The shared socio-economic pathway (SSP) greenhouse gas concentrations and their extensions to 2500. Geosci Model Dev 2020;13:3571–605. https://doi.org/10.5194/gmd-13-3571-2020.",
  yu: "Yu Q, You L, Wood-Sichra U, Ru Y, Joglekar AKB, Fritz S, et al. A cultivated planet in 2010 – Part 2: The global gridded agricultural-production maps. Earth Syst Sci Data 2020;12:3545–72. https://doi.org/10.5194/essd-12-3545-2020.",
  jagermeyr: "Jägermeyr J, Müller C, Ruane AC, Elliott J, Balkovic J, Castillo O, et al. Climate impacts on global agriculture emerge earlier in new generation of climate and crop models. Nat Food 2021;2:873–85. https://doi.org/10.1038/s43016-021-00400-y.",
  poggio: "Poggio L, de Sousa LM, Batjes NH, Heuvelink GBM, Kempen B, Ribeiro E, et al. SoilGrids 2.0: producing soil information for the globe with quantified spatial uncertainty. SOIL 2021;7:217–40. https://doi.org/10.5194/soil-7-217-2021.",
  saxton: "Saxton KE, Rawls WJ. Soil water characteristic estimates by texture and organic matter for hydrologic solutions. Soil Sci Soc Am J 2006;70:1569–78. https://doi.org/10.2136/sssaj2005.0117.",
  copdem: "European Space Agency, Airbus. Copernicus DEM, global 90 m (GLO-90). 2022. https://doi.org/10.5270/ESA-c5d3d65.",
  icrisat: "Nedumaran S, Pingali P, Padmanabhan JR, Ravula P, Gumma MK, Mohammed IA, et al. District Level Data (DLD) and Dashboard for Agriculture and Allied-sectors in India. ICRISAT Dataverse. https://doi.org/10.21421/D2/XFB1BZ.",
  ineichen: "Ineichen P, Perez R. A new airmass independent formulation for the Linke turbidity coefficient. Sol Energy 2002;73:151–7. https://doi.org/10.1016/S0038-092X(02)00045-2.",
  erbs: "Erbs DG, Klein SA, Duffie JA. Estimation of the diffuse radiation fraction for hourly, daily and monthly-average global radiation. Sol Energy 1982;28:293–302. https://doi.org/10.1016/0038-092X(82)90302-4.",
  allen: "Allen RG, Pereira LS, Raes D, Smith M. Crop evapotranspiration: Guidelines for computing crop water requirements. FAO Irrigation and Drainage Paper 56. Rome: FAO; 1998. https://www.fao.org/4/x0490e/x0490e00.htm.",
  din: "DIN SPEC 91434:2021-05. Agri-photovoltaic systems – Requirements for primary agricultural use. Berlin: Beuth Verlag; 2021. https://doi.org/10.31030/3257526.",
  maff: "Ministry of Agriculture, Forestry and Fisheries of Japan. Handling under the farmland conversion permit system of solar power generation facilities installed on supporting pillars while farming continues. Notice 24-Noshin-2657 of 31 March 2013 (in Japanese: 支柱を立てて営農を継続する太陽光発電設備等についての農地転用許可制度上の取扱いについて); superseded by a guideline in 2024. https://www.maff.go.jp/j/nousin/noukei/totiriyo/einogata.html.",
  decret: "Décret n° 2024-318 du 8 avril 2024 relatif au développement de l'agrivoltaïsme et aux conditions d'implantation des installations photovoltaïques sur des terrains agricoles, naturels ou forestiers (NOR ECOR2321918D). Journal officiel de la République française n° 0083, 9 April 2024. https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000049386027.",
  fao2005: "FAO. Fertilizer use by crop in India. Rome: Food and Agriculture Organization of the United Nations; 2005. https://www.fao.org/4/a0257e/a0257e00.htm.",
  faiman: "Faiman D. Assessing the outdoor operating temperature of photovoltaic modules. Prog Photovolt Res Appl 2008;16:307–15. https://doi.org/10.1002/pip.813.",
  meehl: "Meehl GA, Senior CA, Eyring V, Flato G, Lamarque JF, Stouffer RJ, et al. Context for interpreting equilibrium climate sensitivity and transient climate response from the CMIP6 Earth system models. Sci Adv 2020;6:eaba1981. https://doi.org/10.1126/sciadv.aba1981.",
  riaz: "Riaz MH, Imran H, Younas R, Butt NZ. The optimization of vertical bifacial photovoltaic farms for efficient agrivoltaic systems. Sol Energy 2021;230:1004–12. https://doi.org/10.1016/j.solener.2021.10.051.",
  nassar: "Nassar YF, El-Khozondar HJ, Belhaj SO, Alsadi SY, Abuhamoud NM. View factors in horizontal plane fixed-mode solar PV fields. Front Energy Res 2022;10:859075. https://doi.org/10.3389/fenrg.2022.859075.",
  weselek: "Weselek A, Ehmann A, Zikeli S, Lewandowski I, Schindele S, Högy P. Agrophotovoltaic systems: applications, challenges, and opportunities. A review. Agron Sustain Dev 2019;39:35. https://doi.org/10.1007/s13593-019-0581-3.",
  dupraz24: "Dupraz C. Assessment of the ground coverage ratio of agrivoltaic systems as a proxy for potential crop productivity. Agrofor Syst 2024;98:2679–96. https://doi.org/10.1007/s10457-023-00906-3.",
  willockx: "Willockx B, Lavaert C, Cappelle J. Geospatial assessment of elevated agrivoltaics on arable land in Europe to highlight the implications on design, land use and economic level. Energy Rep 2022;8:8736–51. https://doi.org/10.1016/j.egyr.2022.06.076.",
  dinesh: "Dinesh H, Pearce JM. The potential of agrivoltaic systems. Renew Sustain Energy Rev 2016;54:299–308. https://doi.org/10.1016/j.rser.2015.10.024.",
  adeh: "Adeh EH, Good SP, Calaf M, Higgins CW. Solar PV power potential is greatest over croplands. Sci Rep 2019;9:11442. https://doi.org/10.1038/s41598-019-47803-3.",
  iec61724: "IEC 61724-1:2021. Photovoltaic system performance – Part 1: Monitoring. Geneva: International Electrotechnical Commission; 2021. https://webstore.iec.ch/en/publication/65561.",
  santra: "Santra P, Meena HM, Yadav OP. Spatial and temporal variation of photosynthetic photon flux density within agrivoltaic system in hot arid region of India. Biosyst Eng 2021;209:74–93. https://doi.org/10.1016/j.biosystemseng.2021.06.017.",
  dobos: "Dobos AP. PVWatts Version 5 Manual. NREL/TP-6A20-62641. Golden, CO: National Renewable Energy Laboratory; 2014. https://doi.org/10.2172/1158421.",
  // Discussion (Section 4)
  justes: "Justes E, Mary B, Meynard JM, Machet JM, Thelier-Huché L. Determination of a critical nitrogen dilution curve for winter wheat crops. Ann Bot 1994;74:397–407. https://doi.org/10.1006/anbo.1994.1133.",
  ainsworth: "Ainsworth EA, Long SP. What have we learned from 15 years of free-air CO2 enrichment (FACE)? A meta-analytic review of the responses of photosynthesis, canopy properties and plant production to rising CO2. New Phytol 2005;165:351–72. https://doi.org/10.1111/j.1469-8137.2004.01224.x.",
  long06: "Long SP, Ainsworth EA, Leakey ADB, Nösberger J, Ort DR. Food for thought: lower-than-expected crop yield stimulation with rising CO2 concentrations. Science 2006;312:1918–21. https://doi.org/10.1126/science.1114722.",
  marrou: "Marrou H, Guilioni L, Dufour L, Dupraz C, Wéry J. Microclimate under agrivoltaic systems: Is crop growth rate affected in the partial shade of solar panels? Agric For Meteorol 2013;177:117–32. https://doi.org/10.1016/j.agrformet.2013.04.012.",
  weselek21: "Weselek A, Bauerle A, Hartung J, Zikeli S, Lewandowski I, Högy P. Agrivoltaic system impacts on microclimate and yield of different crops within an organic crop rotation in a temperate climate. Agron Sustain Dev 2021;41:59. https://doi.org/10.1007/s13593-021-00714-y.",
  folberth: "Folberth C, Skalský R, Moltchanova E, Balkovič J, Azevedo LB, Obersteiner M, et al. Uncertainty in soil data can outweigh climate impact signals in global crop yield simulations. Nat Commun 2016;7:11872. https://doi.org/10.1038/ncomms11872.",
  lopez: "Lopez A, Roberts B, Heimiller D, Blair N, Porro G. U.S. renewable energy technical potentials: a GIS-based analysis. NREL/TP-6A20-51946. Golden, CO: National Renewable Energy Laboratory; 2012. https://doi.org/10.2172/1219777.",
  cea: "Central Electricity Authority. Load Generation Balance Report 2026-27. New Delhi: Ministry of Power, Government of India; 2026. https://cea.nic.in/wp-content/uploads/l_g_b_r_reports/2025/LGBR_2026_27.pdf [accessed 2 November 2026].",
  nasapower: "NASA Langley Research Center. Prediction Of Worldwide Energy Resources (POWER) Project, daily and climatology data. Hampton, VA: NASA. https://power.larc.nasa.gov [accessed November 2026].",
  kusumfaq: "Ministry of New and Renewable Energy. PM-KUSUM: frequently asked questions. https://pmkusum.mnre.gov.in/landing-faq.html [accessed October 2026].",
};
let order = [];
function cite(...keys) {
  const n = keys.map(k => { if (!REF[k]) throw new Error(k); if (!order.includes(k)) order.push(k); return order.indexOf(k) + 1; });
  n.sort((a, b) => a - b);
  // compress ranges
  const parts = []; let i = 0;
  while (i < n.length) { let j = i; while (j + 1 < n.length && n[j + 1] === n[j] + 1) j++;
    parts.push(j - i >= 2 ? `${n[i]}–${n[j]}` : n.slice(i, j + 1).join(",")); i = j + 1; }
  return `[${parts.join(",")}]`;
}

// ---------- inline markup: *bold*  _italic_  ~sub~  ^sup^ ----------
function runs(text, base = {}) {
  const out = [];
  const re = /(\*[^*]+\*|_[^_]+_|~[^~]+~|\^[^^]+\^)/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), font: FONT, ...base }));
    const t = m[0], inner = t.slice(1, -1);
    const o = { text: inner, font: FONT, ...base };
    if (t[0] === "*") o.bold = true;
    if (t[0] === "_") o.italics = true;
    if (t[0] === "~") o.subScript = true;
    if (t[0] === "^") o.superScript = true;
    out.push(new TextRun(o));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), font: FONT, ...base }));
  return out;
}
const SP = { line: 360, lineRule: LineRuleType.AUTO };   // 1.5 line spacing
const P = (t, o = {}) => new Paragraph({ children: runs(t), spacing: { after: 140, ...SP }, alignment: AlignmentType.JUSTIFIED, ...o });
const H1 = t => new Paragraph({ heading: HeadingLevel.HEADING_1, children: runs(t), spacing: { before: 240, after: 160 } });
const H2 = t => new Paragraph({ heading: HeadingLevel.HEADING_2, children: runs(t), spacing: { before: 220, after: 120 } });
const H3 = t => new Paragraph({ heading: HeadingLevel.HEADING_3, children: runs(t), spacing: { before: 160, after: 100 } });

// ---------- equations ----------
const R = t => new MathRun(t);
const sub = (b, s) => new MathSubScript({ children: [R(b)], subScript: [R(s)] });
const frac = (n, dd) => new MathFraction({ numerator: n, denominator: dd });
const sum = (s, ch) => new MathSum({ children: ch, subScript: [R(s)] });
let eqn = 0;
function EQ(children) {
  eqn++;
  return new Paragraph({
    tabStops: [{ type: TabStopType.CENTER, position: 4513 }, { type: TabStopType.RIGHT, position: 9026 }],
    spacing: { before: 120, after: 120 },
    children: [new TextRun({ text: "\t", font: FONT }), new OMath({ children }), new TextRun({ text: `\t(${EP}${eqn})`, font: FONT })],
  });
}

// ---------- tables ----------
const BORDER = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
const NONE = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
let tabn = 0; let TP = "", FP = "", EP = "";
function caption(prefix, text) {
  return new Paragraph({ keepNext: true, spacing: { before: 200, after: 80 },
    children: [new TextRun({ text: prefix + " ", bold: true, font: FONT, size: 20 }), ...runs(text, { size: 20 })] });
}
function TABLE(title, header, rows, widths, notes, label) {
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (t, i, isHead, isLast) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    margins: { top: 50, bottom: 50, left: 80, right: 80 },
    borders: { top: isHead ? BORDER : NONE, bottom: (isHead || isLast) ? BORDER : NONE, left: NONE, right: NONE },
    children: [new Paragraph({ children: runs(String(t), { size: 17, bold: isHead }), alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.LEFT })],
  });
  const out = [caption(label || `Table ${TP}${++tabn}.`, title)];
  out.push(new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: header.map((h, i) => cell(h, i, true, false)) }),
      ...rows.map((r, k) => new TableRow({ cantSplit: true, children: r.map((t, i) => cell(t, i, false, k === rows.length - 1)) }))],
  }));
  if (notes) out.push(new Paragraph({ spacing: { before: 60, after: 200 }, children: runs(notes, { size: 16 }) }));
  return out;
}
// ---------- result numbers: {key} placeholders filled from results/potential/numbers.json ----------
// fill(text): {key} -> numbers.json values[key], or [pending] when the key is missing.
// {? ... ?} marks an optional sentence: it is dropped when any key inside it is missing
// (use it for 2050 and robust-case sentences). Keys always contain a dot, e.g. {main.cap_twp}.
// NUMBERS=<file> overrides the default path. fill.has(...keys) tests for keys; fill.missing lists
// the keys that were shown as [pending] (printed by save()).
const NUM_FILE = process.env.NUMBERS || path.join(__dirname, "..", "..", "results", "potential", "numbers.json");
const KEY = /\{([a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+)\}/g;
let NUM = null;
function numbers() {
  if (NUM === null) NUM = fs.existsSync(NUM_FILE) ? JSON.parse(fs.readFileSync(NUM_FILE, "utf8")).values : {};
  return NUM;
}
function fill(text) {
  const v = numbers();
  let t = text.replace(/\{\?([\s\S]*?)\?\}/g, (_, seg) =>
    [...seg.matchAll(KEY)].every(m => m[1] in v) ? seg : "");
  t = t.replace(KEY, (_, k) => { if (k in v) return v[k]; fill.missing.add(k); return "[pending]"; });
  return t.replace(/ {2,}/g, " ").replace(/ +([.,;:)])/g, "$1").trim();
}
fill.missing = new Set();
fill.has = (...keys) => keys.every(k => k in numbers());
fill.file = NUM_FILE;
// paragraph with numbers; returns [] when nothing is left (all sentences optional and missing)
const PF = (t, o = {}) => { const f = fill(t); return f ? P(f, o) : []; };

// figure from a PNG of any size, scaled to width w (px); placeholder caption if the file is missing
function pngSize(file) { const b = fs.readFileSync(file); return [b.readUInt32BE(16), b.readUInt32BE(20)]; }
function FIGAUTO(file, w, cap) {
  if (fs.existsSync(file)) { const [pw, ph] = pngSize(file); return FIG(file, w, Math.round(w * ph / pw), cap); }
  fign++;
  return [new Paragraph({ spacing: { before: 200, after: 240 }, children: [
    new TextRun({ text: `Fig. ${FP}${fign}. `, bold: true, font: FONT, size: 20 }),
    new TextRun({ text: `[pending: ${path.basename(file)}] `, font: FONT, size: 20 }), ...runs(cap, { size: 20 })] })];
}

let fign = 0;
function FIG(path, w, h, cap) {
  fign++;
  return [new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 200 },
      children: [new ImageRun({ type: "png", data: fs.readFileSync(path), transformation: { width: w, height: h } })] }),
    new Paragraph({ spacing: { before: 80, after: 240 }, children: [new TextRun({ text: `Fig. ${FP}${fign}. `, bold: true, font: FONT, size: 20 }), ...runs(cap, { size: 20 })] })];
}


const nextFig = () => fign + 1;   // number the next FIG/FIGAUTO will get (for "Fig. N shows ...")
function resetCounters(){ order = []; eqn = 0; tabn = 0; fign = 0; }
function refsList(){ return order.map((k, i) => new Paragraph({ spacing: { after: 80 }, indent: { left: 440, hanging: 440 },
  tabStops: [{ type: TabStopType.LEFT, position: 440 }],
  children: [new TextRun({ text: `[${i + 1}]\t`, font: FONT, size: 20 }), new TextRun({ text: REF[k], font: FONT, size: 20 })] })); }
function setPrefix(t, f, e){ TP = t; FP = f; EP = e; }
function save(body, file){
  const doc = new Document({
    styles: { default: { document: { run: { font: FONT, size: 22 } } },
      paragraphStyles: [
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 28, bold: true, font: FONT } },
        { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 24, bold: true, font: FONT } },
        { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 22, bold: true, italics: true, font: FONT } }] },
    sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18 })] })] }) },
      children: body }] });
  return Packer.toBuffer(doc).then(b => { fs.writeFileSync(file, b); console.log("wrote", file, order.length, "refs", eqn, "eqs");
    const nf = fs.existsSync(NUM_FILE) ? "numbers from " + path.relative(process.cwd(), NUM_FILE) : "no numbers.json";
    if (fill.missing.size) console.log(`${nf}; [pending] keys (${fill.missing.size}): ${[...fill.missing].sort().join(", ")}`);
    else console.log(`${nf}; no [pending] keys`); });
}
module.exports = { nextFig, fill, PF, FIGAUTO, d, REF, cite, runs, P, H1, H2, H3, R, sub, frac, sum, EQ, TABLE, FIG, resetCounters, refsList, setPrefix, save, Paragraph, TextRun, PageBreak, FONT };
