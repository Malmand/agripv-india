#!/bin/bash
# Applied Energy version, built from the same sources as the Earth's Future version (paper/ef) with AGRIPV_STYLE=ae:
# numbered references, Elsevier front and back matter, highlights, graphical abstract, supplementary material.
#   bash paper/methods/build_ae.sh
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE/../ef"
export AGRIPV_STYLE=ae
AGRIPV_OUT=$HERE/Manuscript_AgriPV_India.docx node build_methods.js
AGRIPV_OUT=$HERE/Supplementary_Material_AgriPV_India.docx node build_supp.js
AGRIPV_OUT=$HERE/CoverLetter_AgriPV_India.docx node cover_ef.js
node highlights.js "$HERE"
cd "$HERE"
FUT=ssp585_current; [ -f ../../results/potential/india_combined_ssp585_current_robust.csv ] && FUT=ssp585_current_robust
python3 graphical_abstract_v3.py --future $FUT >/dev/null && echo "graphical abstract: graphical_abstract_v3.png ($FUT)"
