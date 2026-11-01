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
  console.log("wrote", out, `(${lines.length} highlights, longest ${Math.max(...lines.map(l => l.length))} chars)`);
}
module.exports = { writeHighlights };
if (require.main === module) writeHighlights();
