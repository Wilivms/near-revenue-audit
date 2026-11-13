"""Rebuild check: are the outputs on disk the committed ones?

Text must match exactly; numbers must match to 1e-9 relative. Last-digit float noise from a
different CPU or BLAS build is not a difference in the result, a changed figure is.
Compares data/processed/* and dashboard/data.json with the versions in git HEAD.
Exit code 1 and a list of differences if anything else changed.
"""
from __future__ import annotations

import io
import json
import math
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REL = 1e-9


BASELINE = ROOT / ".check_baseline"  # copy of the outputs taken before the rebuild, for a checkout without git


def _in_git() -> bool:
    return subprocess.run(["git", "rev-parse", "--git-dir"], cwd=ROOT, capture_output=True).returncode == 0


def _committed(path: str) -> bytes | None:
    if not _in_git():  # downloaded as a ZIP: compare with the copy saved before the rebuild
        f = BASELINE / path
        return f.read_bytes() if f.exists() else None
    r = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=ROOT, capture_output=True)
    return r.stdout if r.returncode == 0 else None


def snapshot() -> None:
    """Save the outputs as shipped, so a checkout without git (a ZIP) can still be compared after the rebuild."""
    import shutil
    shutil.rmtree(BASELINE, ignore_errors=True)
    for f in sorted((ROOT / "data" / "processed").glob("*")) + [ROOT / "dashboard" / "data.json"]:
        dst = BASELINE / f.relative_to(ROOT)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst)


def _close(a, b) -> bool:
    if isinstance(a, bool) or isinstance(b, bool) or not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        return a == b
    if math.isnan(a) and math.isnan(b):
        return True
    return math.isclose(a, b, rel_tol=REL, abs_tol=1e-12)


def _diff_json(a, b, path="") -> list[str]:
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            return [f"{path}: keys {sorted(set(a) ^ set(b))[:3]}"]
        return [d for k in a for d in _diff_json(a[k], b[k], f"{path}/{k}")]
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{path}: length {len(a)} vs {len(b)}"]
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in _diff_json(x, y, f"{path}[{i}]")]
    return [] if _close(a, b) else [f"{path}: {a!r} vs {b!r}"]


def _diff_csv(old: bytes, new: bytes) -> list[str]:
    a, b = pd.read_csv(io.BytesIO(old)), pd.read_csv(io.BytesIO(new))
    if list(a.columns) != list(b.columns) or a.shape != b.shape:
        return [f"shape/columns {a.shape} vs {b.shape}"]
    out = []
    for c in a.columns:
        if pd.api.types.is_numeric_dtype(a[c]) and pd.api.types.is_numeric_dtype(b[c]):
            x, y = a[c].to_numpy(dtype=float), b[c].to_numpy(dtype=float)
            bad = ~((x == y) | (pd.isna(x) & pd.isna(y)) | (abs(x - y) <= REL * abs(x).clip(min=1e-12 / REL)))
            if bad.any():
                out.append(f"{c}: row {int(bad.argmax())} {x[bad.argmax()]} vs {y[bad.argmax()]}")
        elif not a[c].equals(b[c]):
            out.append(f"{c}: text differs")
    return out


def main() -> int:
    files = sorted((ROOT / "data" / "processed").glob("*")) + [ROOT / "dashboard" / "data.json"]
    problems = {}
    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        old, new = _committed(rel), f.read_bytes()
        if old is None:
            problems[rel] = ["not committed"]
        elif old != new:
            d = _diff_json(json.loads(old), json.loads(new)) if f.suffix == ".json" else _diff_csv(old, new) if f.suffix == ".csv" else ["differs"]
            if d:
                problems[rel] = d
    for rel, d in problems.items():
        print(f"CHANGED {rel}: " + "; ".join(d[:3]))
    print(f"{len(files) - len(problems)}/{len(files)} outputs match the committed ones (text exactly, numbers to {REL:g} relative)")
    return 1 if problems else 0


if __name__ == "__main__":
    if "--snapshot" in sys.argv:
        snapshot()
        sys.exit(0)
    sys.exit(main())
