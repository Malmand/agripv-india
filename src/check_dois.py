"""Check every DOI in the manuscript reference list (paper/methods/lib.js) against Crossref.

For each reference with a https://doi.org/ link, prints the Crossref first-author surname, year and title next
to ours and flags a mismatch in surname or year. References without a DOI are listed for a manual URL check.
Run where api.crossref.org is reachable (Google Cloud Shell): python3 src/check_dois.py
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

_m = Path(__file__).resolve().parents[1] / "paper" / "methods"
src = "\n".join((_m / f).read_text(encoding="utf-8") for f in ("lib.js", "intro.js"))
refs = dict(re.findall(r'^\s+([a-z0-9_]+): "(.*)",\s*$', src, flags=re.M))
bad = 0
for key, txt in refs.items():
    m = re.search(r"https://doi\.org/(\S+?)\.?$", txt)
    if not m:
        print(f"{key:14s} NO DOI   {txt[:100]}")
        continue
    doi = m.group(1)
    if doi.startswith("10.2172/"):        # OSTI technical reports are DataCite DOIs, not in Crossref
        print(f"{key:14s} OSTI     {doi} (check https://doi.org/{doi} by hand)")
        continue
    try:
        url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "agripv-india-refcheck"}),
                                    timeout=30) as r:
            msg = json.load(r)["message"]
    except Exception as e:  # noqa: BLE001
        print(f"{key:14s} FAIL     {doi}  ({e})"); bad += 1; continue
    fam = (msg.get("author") or [{}])[0].get("family", "") or ""
    yr = str((msg.get("issued", {}).get("date-parts") or [[None]])[0][0])
    title = (msg.get("title") or [""])[0]
    ok_fam = fam and fam.split()[-1].lower()[:5] in txt.lower()
    ok_yr = yr in txt
    flag = "OK  " if ok_fam and ok_yr else "CHECK"
    bad += flag != "OK  "
    print(f"{key:14s} {flag}    {doi}  | {fam} {yr} | {title[:70]}")
    time.sleep(0.2)
print(f"\n{bad} reference(s) to check by hand")
sys.exit(0)
