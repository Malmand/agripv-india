"""Usage: python3 src/find_one.py "query" ["query2" ...]  -> top Crossref journal hits with abstract start (Cloud Shell)."""
import sys, re, json, urllib.parse, urllib.request
H = {"User-Agent": "agripv-refcheck (mailto:almandharimohammed90@gmail.com)"}
get = lambda u: json.load(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=30))
for q in sys.argv[1:]:
    print("\n#", q)
    for i in get("https://api.crossref.org/works?rows=6&select=DOI,title,container-title,issued,author,type,abstract&query=" + urllib.parse.quote(q))["message"]["items"]:
        if i.get("type") != "journal-article": continue
        a = (i.get("author") or [{}])[0].get("family", "")
        print(f"  {i['DOI']} | {a} {i['issued']['date-parts'][0][0]} | {(i.get('title') or [''])[0][:110]} | {(i.get('container-title') or [''])[0]}")
        print("     ", re.sub(r"<[^>]+>", " ", i.get("abstract", ""))[:500])
