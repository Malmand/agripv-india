"""Print title, authors, journal, volume/pages and abstract for DOIs (Crossref, OpenAlex fallback). Run in Cloud Shell."""
import json, re, urllib.request
DOIS = """10.1016/j.rser.2020.110694
10.1016/j.apenergy.2020.114737
10.3390/environments6060065
10.1016/j.landurbplan.2017.10.011
10.1016/j.agsy.2021.103193
10.1016/j.landusepol.2025.107604
10.1016/j.rser.2024.115066
10.1016/j.nexus.2025.100610
10.56093/aaz.v63i2.145518
10.3390/agronomy16100985
10.1038/s41893-019-0364-5
10.1007/s13593-022-00783-7""".split()
def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "agripv-refcheck (mailto:almandharimohammed90@gmail.com)"}), timeout=30))
import sys
if len(sys.argv) > 1: DOIS = sys.argv[1:]
for d in DOIS:
    print("\n=====", d)
    try:
        m = get("https://api.crossref.org/works/" + d)["message"]
        au = ", ".join(f"{a.get('family','')} {a.get('given','')[:1]}" for a in m.get("author", []))
        print(au); print(m["title"][0]); print((m.get("container-title") or [""])[0], m["issued"]["date-parts"][0][0], "vol", m.get("volume"), "pp", m.get("page") or m.get("article-number"))
        ab = re.sub(r"<[^>]+>", " ", m.get("abstract", "")).strip()
    except Exception as e:
        print("Crossref ERR", e); ab = ""
    if not ab:
        try:
            w = get("https://api.openalex.org/works/doi:" + d)
            idx = w.get("abstract_inverted_index") or {}
            ab = " ".join(k for k, _ in sorted(((k, p) for k, v in idx.items() for p in v), key=lambda x: x[1]))
        except Exception as e:
            ab = f"(OpenAlex ERR {e})"
    print("ABSTRACT:", ab or "(none available)")
