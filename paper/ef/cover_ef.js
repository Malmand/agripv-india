const {Document,Packer,Paragraph,TextRun,AlignmentType}=require("docx");
const fs=require("fs");
const F="Times New Roman";
const t=(x,o={})=>new TextRun({text:x,font:F,size:23,...o});
const p=(parts,o={})=>new Paragraph({spacing:{after:140,line:276},alignment:AlignmentType.JUSTIFIED,...o,children:(Array.isArray(parts)?parts:[parts]).map(x=>typeof x==="string"?t(x):x)});
const L=(n,x)=>new Paragraph({spacing:{after:100,line:276},indent:{left:360,hanging:360},alignment:AlignmentType.JUSTIFIED,children:[t(n+"\t"),t(x)]});
const doc=new Document({sections:[{properties:{page:{margin:{top:1300,bottom:1300,left:1400,right:1400}}},children:[
p("Dear Editor,"),
p(["We submit our original research article, “Yield-constrained agrivoltaic potential of India under current and mid-century climate”, to ",t("Earth’s Future",{italics:true}),", under the Sustainable Resource Systems theme."]),
p("Solar power and farming compete for the same land, and in India the competition is acute: solar carries most of the country’s clean-power growth, croplands are among the most productive places for PV, and agriculture still employs about 46% of workers. Raising panels above the crop can let one field serve both, but only if the crop keeps enough light. National estimates of that potential for India span roughly a tenfold range, from 1.2 to 13.8 TW, because they assume which crops tolerate shade and what density is acceptable. None simulates what an array does to the crop below it."),
p("We make the food–energy trade-off the unit of analysis. A strip-resolved light model for three array layouts drives crop models of wheat, chickpea, pearl millet and groundnut across India, with nitrogen calibrated to observed state yields and five climate models for 1995–2014 and 2041–2060 under two emission pathways. Capacity is accepted in each grid cell only where the crop keeps 66%, 80% or 90% of its yield, the thresholds of existing German, Japanese and French rules. Three results stand out:"),
L("1.","At 80% retained yield, east-west arrays on slopes up to 5% give up to 39.2 TW peak on 39.7 million hectares, and 22.6 TW peak when the crop model is rescaled to field observations of shade response. We report that range as a technical potential, not a forecast."),
L("2.","How densely panels can be built depends on the crop (about twice as dense over cereals as over legumes) and on fertiliser use, because low nitrogen hides shade loss. By mid-century the potential changes by about 1% (range −7 to +1% across climate models and pathways), so management and rules matter more than climate."),
L("3.","A screening cost layer using Indian auction prices and the ministerial premium shows that elevated frames need a tariff adder that the crop income they protect cannot cover, so any support should be tied to a yield threshold."),
p("The paper goes beyond resource characterization, as the journal’s theme asks, by linking a biophysical model, management, climate and policy. It builds on the global study published in Earth’s Future by Curioni et al. (2025), which applied uniform light reductions to rainfed crops and named parts of India as hotspots. We add explicit array layouts, irrigated crops, nitrogen, regulatory yield thresholds, future climate and a cost screen at national scale. Equity and land tenure are discussed but not modelled, and we say so."),
p("Thank you for considering our work."),
p("Sincerely,",{spacing:{after:60}}),
p("Aritra Ghosh (corresponding author) and Mohamed Al-Mandhari",{spacing:{after:0}}),
]}]});
Packer.toBuffer(doc).then(b=>fs.writeFileSync("CoverLetter_AgriPV_India_EarthsFuture.docx",b));
