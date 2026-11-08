// Highlights: highlights_template.txt with {key} placeholders -> highlights.txt (numbers from
// results/potential/numbers.json via fill()). Elsevier limit: 85 characters per highlight, spaces included.
// Missing keys show as [pending]. Run on its own (node highlights.js) or through build_methods.js.
const fs = require("fs");
const { fill } = require("./lib.js");
const MAX = 85;

function writeHighlights(src = "highlights_template.txt", out = "highlights.txt") {
  const lines = fs.readFileSync(src, "utf8").split("\n").filter(l => l.trim()).map(l => fill(l));
  lines.forEach(l => { if (l.length > MAX && !l.includes("[pending]")) console.log(`WARNING highlight > ${MAX} chars (${l.length}): ${l}`); });
  fs.writeFileSync(out, lines.join("\n") + "\n");
  const L = require("./lib.js");
  const body = [new L.Paragraph({ spacing: { after: 200 }, children: [new L.TextRun({ text: "Highlights", bold: true, size: 28, font: L.FONT })] }),
    ...lines.map(l => new L.Paragraph({ spacing: { after: 120 }, indent: { left: 360, hanging: 360 },
      children: [new L.TextRun({ text: "\u2022\t" + l, font: L.FONT, size: 22 })] }))];
  L.save(body, "Highlights_AgriPV_India.docx");
  console.log("wrote", out, `(${lines.length} highlights, longest ${Math.max(...lines.map(l => l.length))} chars)`);
}
module.exports = { writeHighlights };
if (require.main === module) writeHighlights();
