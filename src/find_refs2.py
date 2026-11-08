"""Second Crossref lookup: climate-change effects on PV output and crops in India, food security, farmer income. Run in Cloud Shell."""
import json, urllib.parse, urllib.request
Q = ["climate change impact on photovoltaic power potential India projections CMIP6",
 "future solar radiation changes India CMIP6 photovoltaic potential",
 "climate change impact on wheat yield India crop model projections",
 "climate change impacts on pearl millet chickpea groundnut yield India",
 "CO2 fertilization effect crop model DSSAT wheat legumes mid-century",
 "agrivoltaics farmer income land lease India smallholder",
 "solar power farmland India land use competition food security",
 "agrivoltaics economic analysis India levelized cost crop revenue"]
for q in Q:
    u="https://api.crossref.org/works?rows=5&select=DOI,title,container-title,issued,author,type&query.bibliographic="+urllib.parse.quote(q)
    try: items=json.load(urllib.request.urlopen(u,timeout=30))["message"]["items"]
    except Exception as e: print("ERR",q,e); continue
    print("\n#",q)
    for i in items:
        a=(i.get("author") or [{}])[0].get("family","")
        print(f"  {i['DOI']} | {a} {i['issued']['date-parts'][0][0]} | {(i.get('title') or [''])[0][:95]} | {(i.get('container-title') or [''])[0]} | {i.get('type')}")
