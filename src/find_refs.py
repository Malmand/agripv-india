"""Look up candidate references on Crossref (run in Cloud Shell; the build sandbox cannot reach Crossref).
Prints the top hits per query so that DOIs, titles and journals can be checked before use."""
import json, urllib.parse, urllib.request
Q = [
 "Trommsdorff Combining food and energy production agrivoltaic system arable and vegetable farming in Germany",
 "Schindele Implementation of agrophotovoltaics techno-economic analysis price-performance ratio policy implications",
 "Sekiyama Nagashima Solar sharing for both food and clean energy production agrivoltaic corn",
 "Majumdar Pasqualetti Dual use of agricultural land agrivoltaics Phoenix",
 "Barron-Gafford Agrivoltaics provide mutual benefits across the food-energy-water nexus in drylands",
 "agrivoltaic potential India crop land solar photovoltaic",
 "agrivoltaic system India crop yield shading experiment",
 "agrivoltaics wheat yield shade photovoltaic field experiment",
 "chickpea yield reduction shading light interception",
 "groundnut peanut yield shade photovoltaic agrivoltaic",
 "pearl millet shade agrivoltaic yield",
 "agrivoltaic national land use potential cropland photovoltaic GIS assessment",
 "global agrivoltaic potential cropland food security energy",
 "agrivoltaics farmer acceptance social acceptance survey",
 "agrivoltaics land equivalent ratio systematic review meta-analysis",
]
for q in Q:
    u = "https://api.crossref.org/works?rows=4&select=DOI,title,container-title,issued,author,type&query.bibliographic=" + urllib.parse.quote(q)
    try:
        items = json.load(urllib.request.urlopen(u, timeout=30))["message"]["items"]
    except Exception as e:
        print("ERR", q, e); continue
    print("\n#", q)
    for i in items:
        a = (i.get("author") or [{}])[0].get("family", "")
        print(f"  {i['DOI']} | {a} {i['issued']['date-parts'][0][0]} | {(i.get('title') or [''])[0][:95]} | {(i.get('container-title') or [''])[0]} | {i.get('type')}")
