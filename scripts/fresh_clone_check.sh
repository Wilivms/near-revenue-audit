#!/usr/bin/env sh
# Rebuild NEAR Revenue Audit from a fresh clone, in a fresh virtual environment, with only requirements.txt.
# Expected last lines: "N passed", "NN/NN outputs match the committed ones", "NN/NN findings hold".
set -eu
DIR="${1:-$(mktemp -d)}"
git clone --quiet https://github.com/Wilivms/near-revenue-audit "$DIR/near-revenue-audit"
cd "$DIR/near-revenue-audit"
python3 -m venv .venv && . .venv/bin/activate
pip install --quiet -r requirements.txt
time make check-clean
