// Highlights (Applied Energy version): 3-5 bullets, each <= 85 characters including spaces (Elsevier).
// Numbers from results/potential/numbers.json via fill(); rice and mid-century lines switch with the results.
const { fill, Paragraph, TextRun, FONT, save } = require("./lib.js");
const fs = require("fs");
const MAX = 85;
function lines() {
  return [
    "Coupled light and crop models find the panel cover that keeps 80% of crop yield.",
    "India's farmland could host {field.ew.t80.cap_twp}–{head.cap_twp_m} TWp of agrivoltaics at 80% crop yield.",
    "Panel cover that keeps 80% of yield: {head.gcr_wheat} for wheat and {head.gcr_chickpea} for chickpea.",
    fill.has("rice.cap_twp") ? "Holding rice after wheat to the same rule gives {rice.cap_twp} TWp." :
      "Low nitrogen hides shade losses; robust management cuts the potential by {robust.reduction_pct}%.",
    "Under high emissions, mid-century climate changes the potential by {fut.change_pct}%.",
  ].map(l => fill(l));
}
function writeHighlights(outDir = ".") {
  const ls = lines();
  ls.forEach(l => console.log(`highlight ${l.length} chars${l.length > MAX ? "  TOO LONG" : ""}: ${l}`));
  fs.writeFileSync(`${outDir}/highlights.txt`, ls.join("\n") + "\n");
  save([new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: "Highlights", bold: true, size: 28, font: FONT })] }),
    ...ls.map(l => new Paragraph({ spacing: { after: 120 }, indent: { left: 360, hanging: 360 },
      children: [new TextRun({ text: "•\t" + l, font: FONT, size: 22 })] }))], `${outDir}/Highlights_AgriPV_India.docx`);
}
module.exports = { writeHighlights };
if (require.main === module) writeHighlights(process.argv[2] || ".");
