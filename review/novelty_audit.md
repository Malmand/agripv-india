# Novelty audit (task H)

Date: 1 November 2026. Scope: national or regional agrivoltaic (APV) potential studies, 2024-2026, that use
process-based crop models, a yield threshold or future climate, with attention to India. Benchmark: Table 1
and the novelty sentences in `paper/methods/intro.js`.

Method. Web searches (general and targeted to India, China, Europe, the USA, Mexico, Korea and global
studies), then every DOI checked against the Crossref API (`api.crossref.org/works/<DOI>`) on 1 Nov 2026.
Publisher pages (ScienceDirect, MDPI, Nature, SSRN) could not be opened from this session, so where Crossref
carries no abstract the description rests on search-engine snippets and is marked [verify]. Nothing below
should be quoted in the manuscript before the full text has been read.

## 1. Bottom line

- **Nagaraju et al. is still a preprint.** Crossref lists only `10.2139/ssrn.7305263` (type posted-content,
  2026). No journal version was found under the title or under the author names (Nagaraju, Kiesecker).
  Under the citation rules it cannot be cited as a peer-reviewed source. It also does not threaten the
  novelty claim: it is a GIS/MCDM/AHP study (details in 3.1).
- **No study found does what this paper does at national scale**: process-based crop model x light model x
  several layouts and GCRs x management x future climate x regulatory yield threshold. The core claim
  (first national map of APV potential constrained by simulated crop yield, for India) holds, and
  keeping "to our knowledge" is enough.
- **Two sentences in the Introduction should be softened or made more precise** because of
  Arendarczyk et al. (2026, Applied Energy), a global land-system study that runs LPJ-GUESS crop yields under
  climate, nitrogen and irrigation regimes for agrivoltaics to 2060 (details in 3.3):
  1. "where crop response has been modelled at scale, irrigation and nitrogen management have been ignored"
  2. "to our knowledge no national APV potential has been tested with crop models under future climate"
     (true as worded, "national", but a reviewer who knows Arendarczyk et al. or Jia et al. will push on it).
- **Table 1 should add** Arendarczyk et al. (2026), and probably Jia et al. (2026) (already cited in the
  Introduction text, regional, process-based, future climate). Nagaraju et al. can be mentioned only if MO
  accepts citing a preprint, which the rules forbid; recommended: leave it out and be ready to answer a
  reviewer who raises it.

## 2. Studies checked (overview)

| # | Study (DOI verified on Crossref) | Scale | Crop yield under PV | Climate | Yield rule | In Table 1? | Threat to a "first" claim |
|---|---|---|---|---|---|---|---|
| 1 | Nagaraju et al. 2026, SSRN preprint, 10.2139/ssrn.7305263 | India, 500 m | Literature synthesis of shade compatibility, 154 crops; no crop model | Current | None stated | No (preprint) | Low |
| 2 | Mehta and Betz 2026, Energy Sustain Dev 91:101915, 10.1016/j.esd.2025.101915 | India, 1 km | Not modelled | Current | None | Yes | None |
| 3 | Fraunhofer ISE/EY/CSTEP 2024 (report) | India, district | Suitability matrix | Current | None | Yes | None |
| 4 | TERI 2026 (policy brief) | India, 250 m | Field crops excluded | Current | None | Yes | None |
| 5 | Arendarczyk et al. 2026, Appl Energy 426:128628, 10.1016/j.apenergy.2026.128628 | Global, 0.5 deg (LandSyMM) [verify] | LPJ-GUESS yields under climate, N and irrigation regimes [verify how shade enters] | Future, to 2060, 1.5 C scenario (RCP2.6, MRI-ESM2.0 [verify]) | None (land-use scenario) | No | **Medium**: crop model + management + future climate at global scale |
| 6 | Jia et al. 2026, PNAS 123:e2514380123, 10.1073/pnas.2514380123 | US Midwest, county | Integrated biophysical-economic model [verify model name] | Current and CMIP6 SSP1-2.6/3-7.0/5-8.5 | None; fixed GCR 0.33 | Cited in text, not in table | Medium (regional, one GCR) |
| 7 | Curioni et al. 2025, Earth's Future 13:e2024EF005291, 10.1029/2024EF005291 | Global, ~10 km | Agro-hydrological model, uniform light cut | Historical | None | Yes | Low |
| 8 | Xia et al. 2024, Sustain Prod Consum 50:205-15, 10.1016/j.spc.2024.08.001 | China | Shading-response curves | Current | None | Yes | None |
| 9 | Yang et al. 2026, Commun Earth Environ 7:655, 10.1038/s43247-026-03448-5 | China | Response curves (ground PV on marginal land, not APV per se) | Scenarios to 2050 (energy demand, not climate) | None | No | None |
| 10 | Saguchi Pérez de Alva et al. 2026, J Clean Prod 577:149433, 10.1016/j.jclepro.2026.149433 | Mexico, national | Density assumptions, upper-bound potential [verify] | Current | None [verify] | No | Low |
| 11 | Rodrigo et al. 2026, Energy Convers Manag 369:122049, 10.1016/j.enconman.2026.122049 | Utility-scale plant | Photosynthesis light-response curves, "spatial yield constraints" (e.g. 80% of area at >90% yield [verify]) | Current | Yes (site design) | No | Low (site scale), but cite as yield-constrained design |
| 12 | Thaler et al. 2024, Agronomy 14:2511, 10.3390/agronomy14112511 | One region, eastern Austria | DSSAT (wheat, barley, maize), 7 APV designs, shading only | 2013-2021 | None | No | None (site/regional); useful methods precedent for DSSAT + shading |
| 13 | Kim and Kim 2023, Renew Energy 206:928-38, 10.1016/j.renene.2023.02.090 | One site, South Korea | ALMANAC, 5 crops | SSP1-2.6 to SSP5-8.5, 2021-2050 and 2051-2080 | None (profit optimum) | No | None for national claim; it is a precedent for crop model + APV + SSPs at site scale |
| 14 | Willockx et al. 2022, Energy Rep 8:8736-51, 10.1016/j.egyr.2022.06.076 | Europe, 25 km | Assumed unchanged | Current | Light requirement | Yes | None |
| 15 | Rösch and Fakharizadehshirazi 2024, Renew Sustain Energy Rev 202:114706, 10.1016/j.rser.2024.114706 | Germany | Not modelled (socio-technical GIS) | Current | None | No | None |
| 16 | Khanna et al. 2026, npj Clean Energy 2:32, 10.1038/s44406-026-00049-1 | USA (review/perspective, row crops) [verify] | Summarises Jia et al. type results | - | - | No | None |
| 17 | Prakash et al. 2023, Eur J Agron 149:126922, 10.1016/j.eja.2023.126922 | One site, Gujarat, India | Shading/PAR simulation and wheat yield in field trial | Current | None | No | None; useful Indian field evidence for wheat under APV |

Not citable under MO's rules but checked for novelty: Schuck et al. 2025 (AgriVoltaics Conference Proceedings
3, 10.52825/agripv.v3i.1361), a PROMET shading module "capable of worldwide simulations", applied to one
French site; Kortshagen and Ferry 2025 (same proceedings, 10.52825/agripv.v3i.1368), a coupled crop, soil
water and PV model at county level, example Renville County, MN (about 0.55% yield loss per 1% shading). Both
are conference contributions, site or county scale, current climate. They show the direction of the field
(PROMET could produce a national map soon), but neither is a national potential.

## 3. Notes on the studies that matter most

### 3.1 Nagaraju et al. (SSRN, 2026), India
- Status: preprint only (Crossref type posted-content; no journal DOI found on 1 Nov 2026). Re-check before
  submission.
- What it does (Crossref abstract): national-to-district GIS framework with MCDM and AHP; an
  Agrivoltaics Suitability Index at 500 m from biophysical, technical, agricultural, infrastructural,
  socio-economic and environmental criteria; shade compatibility from a synthesis of experiments on 154 crop
  species; translates suitability into configuration-specific capacity. Results: 19.59 Mha suitable,
  12.85 Mha highly suitable; 9,278-12,207 GWp; priority states Rajasthan, Maharashtra, Andhra Pradesh,
  Karnataka, Telangana, Madhya Pradesh.
- Against Table 1: same class as Fraunhofer and Mehta and Betz (no simulated yield, no light model, no
  management, current climate, no yield threshold). Its own framing ("spatial assessments and crop-response
  studies remain largely disconnected") supports our gap statement.
- Implication: our "first" claim stands. If it is published before our submission, add it to Table 1 as
  "India, 500 m | Literature-based shade compatibility, 154 crops | Configuration-specific | No | Current |
  None", and add its 9.3-12.2 TW to the range of national estimates in the Introduction and Discussion 4.1.

### 3.2 Indian literature in general
- No 2024-2026 peer-reviewed study was found that runs a crop model (DSSAT, APSIM, InfoCrop) under PV shade at
  state or national scale in India. Indian APV evidence remains site-level (Jodhpur, already cited; Anand,
  Gujarat, Prakash et al. 2023, not cited yet).
- Suggestion: cite Prakash et al. (2023) next to Santra and Poonia in the Introduction paragraph on Indian
  evidence ("Evidence from India is still sparse...").

### 3.3 Arendarczyk et al. (Applied Energy, 2026), global
- What it does (Crossref abstract of the SSRN version 10.2139/ssrn.6500089, and snippets): global land system
  model (LandSyMM: LPJ-GUESS crop yields + PLUM land use) under a 1.5 C mitigation scenario to 2060; replaces
  bioenergy with agrivoltaics or PV and compares land, fertiliser and irrigation use. LPJ-GUESS supplies
  yields "under different climate, nitrogen, and irrigation regimes" [verify in full text how the APV shading
  effect on yield is represented: a fixed yield factor or simulated light reduction].
- Against Table 1: global, coarse, scenario-driven, no layout or GCR variation, no yield threshold, not
  India-specific. It is not a yield-constrained potential, so it does not undercut contribution (ii).
- But it does weaken two generalisations in the Introduction (see section 4). It is also in the target
  journal, so reviewers may know it. Recommended: add to Table 1 and cite in the gap paragraph.

### 3.4 Jia et al. (PNAS, 2026), US Midwest
- Already cited in the Introduction as "a process-based study". Crossref abstract says "integrated
  biophysical-economic modeling framework" for current and projected climate at a single GCR of 0.33.
  [verify] that the crop component is process-based (search snippets mention a structural equation model
  used to attribute yield variance). If the crop model is not process-based, change "A process-based study"
  to "A modelling study".
- Recommended: add to Table 1 (regional, county; yield simulated; one GCR; rainfed; CMIP6 future; no yield
  rule). Showing it in the table makes our difference visible: multiple GCRs and layouts, management, and a
  yield threshold.

## 4. Claims in intro.js and recommended changes

| Claim (intro.js) | Verdict | Suggested wording |
|---|---|---|
| "None of these studies simulates crop yield under the panels" (Indian studies) | Holds (also true for Nagaraju et al.) | Keep |
| "national estimates of APV potential, including all those for India, do not model how much light a given array leaves for the crop" | Holds for national studies found. Curioni et al. apply a uniform light cut, not array geometry | Keep |
| "where crop response has been modelled at scale, irrigation and nitrogen management have been ignored" | **Too strong**: Arendarczyk et al. use LPJ-GUESS yields under N and irrigation regimes [verify] | "where crop response has been modelled at scale, management has been fixed or treated separately from shade, so its effect on the shade response has not been quantified" [check against Arendarczyk full text] |
| "to our knowledge no national APV potential has been tested with crop models under future climate" | Holds as worded (national, potential). Global land-use (Arendarczyk) and regional (Jia) studies exist | "Global land-use scenarios ${cite("arendarczyk")} and a regional study ${cite("jia")} have added future climate, but to our knowledge no national APV potential has been tested with crop models under future climate, and none has applied a yield threshold" |
| Contribution (ii) "to our knowledge, the first national map of APV potential constrained by simulated crop yield ... for India" | Holds | Keep. Optional, safer: "the first national map of APV potential for India constrained by simulated crop yield" (same meaning, less open to "first anywhere") |
| Contribution (iii) management changes simulated effect of shade | No competing study found that quantifies N x shade interaction at scale | Keep |
| "A process-based study across the United States Midwest" (Jia) | [verify] crop model type | See 3.4 |

## 5. Proposed Table 1 rows (for MO to approve before editing intro.js)

- Arendarczyk et al. (2026) | Global, 0.5 deg [verify] | LPJ-GUESS crop yields [verify shade treatment] | Not resolved | Varied N and irrigation [verify] | To 2060, 1.5 C scenario | None
- Jia et al. (2026) | US Midwest, county | Biophysical model, maize and soybean [verify] | GCR 0.33 | Rainfed | Current; CMIP6 SSP1-2.6, SSP3-7.0, SSP5-8.5 | None

REF entries (metadata and author names from Crossref):
- arendarczyk: Arendarczyk B, Saxena A, Arneth A, Rounsevell M, Alexander P. Agrivoltaics could increase global
  land use efficiency compared to bioenergy. Appl Energy 2026;426:128628.
  https://doi.org/10.1016/j.apenergy.2026.128628.
- prakash: Prakash V, Lunagaria MM, Trivedi AP, Upadhyaya A, Kumar R, Das A, et al. Shading and PAR under
  different density agrivoltaic systems, their simulation and effect on wheat productivity. Eur J Agron
  2023;149:126922. https://doi.org/10.1016/j.eja.2023.126922.

intro.js was not edited in this task; the changes above are for MO to accept.

## 6. Search log

Queries (web, 1 Nov 2026): Nagaraju agrivoltaic India national assessment; national agrivoltaic potential
crop model yield threshold future climate; agrivoltaic potential India crop simulation DSSAT APSIM;
country-scale process-based crop model GCR map; China crop model yield-loss threshold; CMIP6 APV
suitability Europe/Africa; national crop-model maps Germany/France/Italy/USA; India state-level potential;
global APV crop simulation SSP LER; APV future climate crop model; India APV crop model shading
(DSSAT/APSIM/InfoCrop); US national potential maize/soybean. Crossref title and author queries for every
study above. Re-run the Nagaraju check and a "agrivoltaic potential crop model" Crossref query for
2026 just before submission.
