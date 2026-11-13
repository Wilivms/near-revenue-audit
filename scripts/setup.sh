#!/usr/bin/env bash
# Creates .venv with Python 3.12 or later and the four pinned dependencies.
# Uses the system python3 if it is recent enough; otherwise installs uv, which fetches Python 3.12 itself.
set -euo pipefail
if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' 2>/dev/null; then
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
else
  echo "python3 is older than 3.12: using uv to get Python 3.12"
  command -v uv >/dev/null 2>&1 || python3 -m pip install -q --user uv || pip install -q uv
  UV=$(command -v uv || echo "$HOME/.local/bin/uv")
  "$UV" venv -q -p 3.12 .venv
  VIRTUAL_ENV="$PWD/.venv" "$UV" pip install -q -r requirements.txt
fi
echo "ready: run  . .venv/bin/activate  then  make check-clean"
