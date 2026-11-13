// AGU (APA-based) reference style for the Earth's Future version. REF in lib.js keeps the Elsevier-style strings;
// agu(k) converts journal articles automatically and uses AGU_MANUAL for reports, standards, laws, data and web pages.
const JOURNAL = {
  "Agron Sustain Dev": "Agronomy for Sustainable Development", "Acta Agron Sin": "Acta Agronomica Sinica",
  "Agric Ecosyst Environ": "Agriculture, Ecosystems & Environment", "Agric Syst": "Agricultural Systems",
  "Agrofor Syst": "Agroforestry Systems", "Agronomy": "Agronomy", "Ann Arid Zone": "Annals of Arid Zone",
  "Ann Bot": "Annals of Botany", "Appl Energy": "Applied Energy", "Biosyst Eng": "Biosystems Engineering",
  "Clim Serv": "Climate Services", "Earth Syst Sci Data": "Earth System Science Data", "Earth's Future": "Earth's Future",
  "Energy Clim Change": "Energy and Climate Change", "Energy Nexus": "Energy Nexus", "Energy Rep": "Energy Reports",
  "Environ Sci Technol Lett": "Environmental Science & Technology Letters", "Environments": "Environments",
  "Eur J Agron": "European Journal of Agronomy", "Food Energy Secur": "Food and Energy Security",
  "Front Energy Res": "Frontiers in Energy Research", "Geophys Res Lett": "Geophysical Research Letters",
  "Geosci Model Dev": "Geoscientific Model Development", "J Hydrol": "Journal of Hydrology",
  "J Open Source Softw": "Journal of Open Source Software", "Land Use Policy": "Land Use Policy",
  "Landsc Urban Plan": "Landscape and Urban Planning", "Nat Commun": "Nature Communications", "Nat Food": "Nature Food",
  "New Phytol": "New Phytologist", "Prog Photovolt Res Appl": "Progress in Photovoltaics: Research and Applications",
  "Renew Energy": "Renewable Energy", "Renew Sustain Energy Rev": "Renewable and Sustainable Energy Reviews",
  "SOIL": "SOIL", "Sci Adv": "Science Advances", "Sci Data": "Scientific Data", "Sci Rep": "Scientific Reports",
  "Science": "Science", "Soil Sci Soc Am J": "Soil Science Society of America Journal", "Sol Energy": "Solar Energy",
  "Sustain Energy Res": "Sustainable Energy Research", "Nat Sustain": "Nature Sustainability",
  "Agric Water Manag": "Agricultural Water Management", "Proc Natl Acad Sci USA": "Proceedings of the National Academy of Sciences of the United States of America",
  "Sustain Energy Technol Assess": "Sustainable Energy Technologies and Assessments", "Energy Sustain Dev": "Energy for Sustainable Development",
  "Sustain Prod Consum": "Sustainable Production and Consumption",
  "Energy Convers Manag": "Energy Conversion and Management", "Environ Res Lett": "Environmental Research Letters",
};
const AGU_MANUAL = {
  datameet: "DataMeet India Community. (2021). *India state boundaries (States/Admin2)* [Dataset]. GitHub. https://github.com/datameet/maps/tree/master/States",
  ifct: "Longvah, T., Ananthan, R., Bhaskarachary, K., & Venkaiah, K. (2017). *Indian food composition tables*. National Institute of Nutrition, Indian Council of Medical Research. https://www.nin.res.in/ebooks/IFCT2017.pdf",
  fhg: "Fraunhofer ISE, EY, & CSTEP. (2024). *Agrivoltaics in India*. Indo-German Energy Forum. https://energyforum.in/fileadmin/india/media_elements/publications/20240502_AgriPV_in_India/Agrivoltaics_in_India.pdf",
  ndc: "Government of India. (2022). *India's updated first Nationally Determined Contribution under the Paris Agreement (2021–2030)*. UNFCCC. https://unfccc.int/sites/default/files/NDC/2022-08/India%20Updated%20First%20Nationally%20Determined%20Contrib.pdf",
  kusum: "Ministry of New and Renewable Energy. (2024). *Comprehensive guidelines for implementation of Pradhan Mantri Kisan Urja Suraksha evam Utthaan Mahabhiyaan (PM-KUSUM) scheme*. MNRE. https://mnre.gov.in/?p=22280",
  mnre: "Ministry of New and Renewable Energy. (2026). *Physical progress: Programme-wise cumulative installed capacity*. Retrieved October 2026, from https://mnre.gov.in/en/physical-progress/",
  plfs: "National Statistics Office. (2024). *Annual report, Periodic Labour Force Survey (PLFS), July 2023–June 2024*. Ministry of Statistics and Programme Implementation. https://microdata.gov.in/nada43/index.php/catalog/213",
  teri: "Yadav, S., Tiwari, A. K., Malik, H., & Dortch, R. (2026). *Agri-photovoltaics potential in India: Pathways for sustainable energy–food solutions* (Policy brief). The Energy and Resources Institute (TERI). https://www.teriin.org/policy-brief/agri-photovoltaics-potential-india-pathways-sustainable-energy-food-solutions",
  deshmukh: "Deshmukh, R., Wu, G. C., & Phadke, A. (2017). *Renewable energy zones for balancing siting trade-offs in India: Multi-criteria analysis for planning renewable energy (MapRE)* (Report LBNL-1007272). Lawrence Berkeley National Laboratory. https://escholarship.org/uc/item/5cf6k335",
  pibrabi: "Press Information Bureau. (2025, October 1). *Cabinet approves Minimum Support Prices (MSP) for Rabi crops for marketing season 2026-27*. Government of India. https://www.pib.gov.in/PressReleasePage.aspx?PRID=2173567",
  pibkharif: "Press Information Bureau. (2026, May 13). *Cabinet approves Minimum Support Prices (MSP) for Kharif crops for marketing season 2026-27*. Government of India. https://www.pib.gov.in/PressReleasePage.aspx?PRID=2260618",
  mnre25: "Economic Times EnergyWorld. (2026, October). *Govt framing policy to enhance farmers' income via adoption of agrivoltaics*. https://energy.economictimes.indiatimes.com/news/renewable/govt-framing-policy-to-enhance-farmers-income-via-adoption-of-agrivoltaics/135120304",
  gerc: "Gujarat Electricity Regulatory Commission. (2026). *Order in Petition No. 2603 of 2026: Adoption of tariff discovered by reverse auction for PM-KUSUM Component A solar plants (DGVCL)*. https://jmkresearch.com/wp-content/uploads/2026/03/2603-of-2026-DGVCL.pdf",
  itrpv: "VDMA Photovoltaic Equipment. (2026). *International Technology Roadmap for Photovoltaic (ITRPV): Results 2025* (17th ed.). VDMA. https://www.vdma.org/international-technology-roadmap-photovoltaic",
  hoogenboom: "Hoogenboom, G., Porter, C. H., Boote, K. J., Shelia, V., Wilkens, P. W., Singh, U., et al. (2021). *Decision Support System for Agrotechnology Transfer (DSSAT)* (Version 4.8) [Software]. DSSAT Foundation. https://dssat.net",
  copdem: "European Space Agency, & Airbus. (2022). *Copernicus DEM, global 90 m (GLO-90)* [Dataset]. https://doi.org/10.5270/ESA-c5d3d65",
  icrisat: "Swamikannu, N., Pingali, P. R., Padmanabhan, J., Ravula, P., Gumma, M. K., Mohammed, I. A., et al. (2021). *District Level Data (DLD) and dashboard for agriculture and allied sectors in India* (Version 1) [Dataset]. ICRISAT Dataverse. https://doi.org/10.21421/D2/XFB1BZ",
  allen: "Allen, R. G., Pereira, L. S., Raes, D., & Smith, M. (1998). *Crop evapotranspiration: Guidelines for computing crop water requirements* (FAO Irrigation and Drainage Paper 56). FAO. https://www.fao.org/4/x0490e/x0490e00.htm",
  din: "DIN. (2021). *DIN SPEC 91434:2021-05. Agri-photovoltaic systems – Requirements for primary agricultural use*. Beuth Verlag. https://doi.org/10.31030/3257526",
  maff: "Ministry of Agriculture, Forestry and Fisheries of Japan. (2024). *Handling under the farmland conversion permit system of solar power generation facilities installed on supporting pillars while farming continues* (Notice 24-Noshin-2657 of 31 March 2013, superseded by a guideline in 2024; in Japanese). https://www.maff.go.jp/j/nousin/noukei/totiriyo/einogata.html",
  decret: "Décret n° 2024-318. (2024). *Décret n° 2024-318 du 8 avril 2024 relatif au développement de l'agrivoltaïsme et aux conditions d'implantation des installations photovoltaïques sur des terrains agricoles, naturels ou forestiers* (NOR ECOR2321918D). Journal officiel de la République française n° 0083. https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000049386027",
  fao2005: "FAO. (2005). *Fertilizer use by crop in India*. Food and Agriculture Organization of the United Nations. https://www.fao.org/4/a0257e/a0257e00.htm",
  iec61724: "IEC. (2021). *IEC 61724-1:2021. Photovoltaic system performance – Part 1: Monitoring*. International Electrotechnical Commission. https://webstore.iec.ch/en/publication/65561",
  dobos: "Dobos, A. P. (2014). *PVWatts version 5 manual* (Technical Report NREL/TP-6A20-62641). National Renewable Energy Laboratory. https://doi.org/10.2172/1158421",
  marrou: "Marrou, H., Guilioni, L., Dufour, L., Dupraz, C., & Wéry, J. (2013). Microclimate under agrivoltaic systems: Is crop growth rate affected in the partial shade of solar panels? *Agricultural and Forest Meteorology*, 177, 117–132. https://doi.org/10.1016/j.agrformet.2013.04.012",
  lopez: "Lopez, A., Roberts, B., Heimiller, D., Blair, N., & Porro, G. (2012). *U.S. renewable energy technical potentials: A GIS-based analysis* (Technical Report NREL/TP-6A20-51946). National Renewable Energy Laboratory. https://doi.org/10.2172/1219777",
  cea: "Central Electricity Authority. (2026). *Load generation balance report 2026-27*. Ministry of Power, Government of India. https://cea.nic.in/wp-content/uploads/l_g_b_r_reports/2025/LGBR_2026_27.pdf",
  nasapower: "NASA Langley Research Center. (2026). *Prediction Of Worldwide Energy Resources (POWER) Project, daily and climatology data* [Dataset]. Retrieved November 2026, from https://power.larc.nasa.gov",
  kusumfaq: "Ministry of New and Renewable Energy. (2026). *PM-KUSUM: Frequently asked questions*. Retrieved October 2026, from https://pmkusum.mnre.gov.in/landing-faq.html",
};
function authors(s) {
  const etal = /,? et al$/.test(s); s = s.replace(/,? et al$/, "");
  const parts = s.split(/, /).map(a => {
    const m = a.match(/^(.+?) ([A-Z]{1,4})$/);           // "Wu GC" -> "Wu, G. C."
    return m ? `${m[1]}, ${m[2].split("").map(c => c + ".").join(" ")}` : a;
  });
  if (etal) return parts.join(", ") + ", et al.";
  if (parts.length === 1) return parts[0];
  return parts.slice(0, -1).join(", ") + ", & " + parts[parts.length - 1];
}
function pages(p) {   // "117–32" -> "117–132"
  const m = p.match(/^(\d+)–(\d+)$/);
  if (!m || m[2].length >= m[1].length) return p;
  return `${m[1]}–${m[1].slice(0, m[1].length - m[2].length)}${m[2]}`;
}
function agu(k, s, year) {   // year: the label year of the in-text citation, with its a/b suffix
  const fix = r => year ? r.replace(/\((\d{4})[a-z]?(?=[,)])/, `(${year}`) : r;
  if (AGU_MANUAL[k]) return fix(AGU_MANUAL[k]);
  const y = s.match(/ (\d{4}[a-z]?);([^.]+?)\. (https?:\S+?)\.?$/);
  if (!y) { console.log("AGU no pattern: " + k + " | " + s); return s; }
  const head = s.slice(0, y.index);
  const am = head.match(/^(.+? et al|.+?)\. /);           // authors end at the first ". " (or after "et al.")
  const au = am[1], rest = head.slice(am[0].length);
  const j = rest.lastIndexOf(". ");
  const title = rest.slice(0, j), jab = rest.slice(j + 2);
  const jn = JOURNAL[jab]; if (!jn) { console.log("AGU unknown journal: " + jab + " (" + k + ")"); return s; }
  const [vol, pg] = y[2].split(":");
  return fix(`${authors(au)} (${y[1]}). ${title}. *${jn}*, ${vol}, ${pages(pg)}. ${y[3]}`);
}
module.exports = { agu };
