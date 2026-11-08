"""Crossref/OpenAlex lookup for shading-response evidence (validation of simulated relative yield) and two named papers.
Prints top hits with the first 700 characters of the abstract. Run in Cloud Shell."""
import json, re, urllib.parse, urllib.request
H = {"User-Agent": "agripv-refcheck (mailto:almandharimohammed90@gmail.com)"}
def get(u): return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=30))
def abstract(m):
    ab = re.sub(r"<[^>]+>", " ", m.get("abstract", "")).strip()
    if ab: return ab
    try:
        idx = get("https://api.openalex.org/works/doi:" + m["DOI"]).get("abstract_inverted_index") or {}
        return " ".join(k for k, _ in sorted(((k, p) for k, v in idx.items() for p in v), key=lambda x: x[1]))
    except Exception: return ""
Q = [
 "Curioni agrivoltaic global rainfed crops radiation attenuation yield harvested area",
 "Aswal agrivoltaic India crop light transmission land equivalent ratio",
 "wheat grain yield artificial shading reduction in solar radiation field experiment",
 "chickpea shade yield field experiment reduced radiation",
 "groundnut peanut shading yield reduction field experiment light intensity",
 "pearl millet shading effect on grain yield",
 "agrivoltaic wheat yield under panels relative yield land equivalent ratio",
 "agrivoltaic legumes soybean yield under solar panels",
 "agrivoltaic maize OR sorghum OR millet yield solar panels shading",
 "crop model agrivoltaic validation measured yield under panels DSSAT OR APSIM OR STICS",
]
for q in Q:
    u = "https://api.crossref.org/works?rows=5&select=DOI,title,container-title,issued,author,type&query.bibliographic=" + urllib.parse.quote(q)
    try: items = get(u)["message"]["items"]
    except Exception as e: print("ERR", q, e); continue
    print("\n#", q)
    for i in items:
        if i.get("type") != "journal-article": continue
        a = (i.get("author") or [{}])[0].get("family", "")
        print(f"\n  {i['DOI']} | {a} {i['issued']['date-parts'][0][0]} | {(i.get('title') or [''])[0][:110]} | {(i.get('container-title') or [''])[0]}")
        try: print("    ABS:", abstract(i)[:700] or "(none)")
        except Exception: pass
