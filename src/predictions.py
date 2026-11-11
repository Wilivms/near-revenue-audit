"""Dated predictions, frozen before they can be checked.

predictions/PREDICTIONS.csv was written on 2026-11-11. Its sha256 is committed next to it
(PREDICTIONS.sha256, checked by a test) and the file is timestamped in Bitcoin with OpenTimestamps
(PREDICTIONS.csv.ots; check with `ots verify predictions/PREDICTIONS.csv.ots`), so any later edit
shows. Each prediction names the number that decides
it, the threshold and the date from which it can be resolved. Two resolve before judging starts
(P1 and P2 on 2026-11-15) and one on its first day (P3, 2026-11-16).

`python3 -m src.predictions` resolves every prediction whose date has passed, from the committed
snapshots (run `make refresh` first for today's data), and prints the rest as pending.
Output: predictions/RESULTS.md.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PRED = ROOT / "predictions" / "PREDICTIONS.csv"
RESULTS = ROOT / "predictions" / "RESULTS.md"
OUT = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"


def _latest(source: str, pattern: str = "*.json"):
    return json.loads(sorted((RAW / source).glob(pattern))[-1].read_text())


def _official():
    snap = _latest("near_revenue")
    vol = pd.DataFrame(snap["intentVolumeSeries"]).assign(d=lambda x: pd.to_datetime(x.date_at)).set_index("d")["volume_usd"]
    tvl = pd.DataFrame(snap["tvlChartSeries"]).assign(d=lambda x: pd.to_datetime(x.date)).set_index("d")["value"]
    return vol, tvl


def _rev() -> pd.Series:
    return pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True)["rebuilt_total_usd"]


def take_bps(start: str, end: str):
    vol = _official()[0]
    if vol.index.max() < pd.Timestamp(end):
        return None
    r, v = _rev().loc[start:end], vol.loc[start:end]
    return float(r.sum() / v.sum() * 1e4)


def tvl_on(day: str):
    tvl = _official()[1]
    return float(tvl.loc[day]) if pd.Timestamp(day) in tvl.index else None


def hsp029_status():
    files = sorted((RAW / "governance").glob("hsp029_*.json"))
    p = json.loads(files[-1].read_text()) if files else None
    return None if p is None or p["status"] == "Timelock" else p["status"]


def month_offset(month: str):
    sm = pd.read_csv(OUT / "supply_monthly.csv", index_col=0, parse_dates=True)
    return float(sm.loc[month, "captured_share_of_issuance"]) if pd.Timestamp(month) in sm.index else None


def supply_on_or_after(day: str):
    pts = sorted(_latest("supply_history", "blocks.json"), key=lambda p: p["ts"])
    after = [p for p in pts if p["ts"] >= pd.Timestamp(day).timestamp()]
    return after[0]["supply"] if after else None


METRICS = {
    "take_bps": take_bps, "tvl_on": tvl_on, "hsp029_status": hsp029_status,
    "month_offset": month_offset, "supply_on_or_after": supply_on_or_after,
}


def _check(value, op: str, threshold: str) -> bool:
    if op == "in":
        return str(value) in threshold.split("|")
    t = float(threshold)
    return {"<": value < t, ">": value > t, "<=": value <= t, ">=": value >= t}[op]


def sha256() -> str:
    return hashlib.sha256(PRED.read_bytes()).hexdigest()


def resolve(today: pd.Timestamp | None = None) -> pd.DataFrame:
    today = today or pd.Timestamp.now(tz="UTC").tz_localize(None).normalize()
    df = pd.read_csv(PRED, dtype=str)
    rows = []
    for _, p in df.iterrows():
        value = None
        if pd.Timestamp(p.resolve_on) <= today:
            args = [a for a in p.metric_args.split(";") if a]
            value = METRICS[p.metric](*args)
            if p.metric == "supply_on_or_after" and value is not None:  # compared with the supply on the day made
                pts = _latest("supply_history", "blocks.json")
                base = min(pts, key=lambda q: abs(q["ts"] - pd.Timestamp(p.made_on).timestamp()))["supply"]
                value = value - base if base is not None else None
        if value is None:
            status = "pending" if pd.Timestamp(p.resolve_on) > today else "awaiting data"
        else:
            status = "confirmed" if _check(value, p.op, p.threshold) else "refuted"
        rows.append({"id": p.id, "prediction": p.prediction, "resolve_on": p.resolve_on, "value": value, "status": status})
    return pd.DataFrame(rows)


def main() -> None:
    r = resolve()
    lines = [f"# Predictions: results\n", f"Frozen file: `predictions/PREDICTIONS.csv`, sha256 `{sha256()}` "
             "(timestamped in Bitcoin: `ots verify predictions/PREDICTIONS.csv.ots`). Resolved from the committed snapshots by "
             "`python3 -m src.predictions`.\n", "| ID | Prediction | Resolves on | Value | Status |", "| --- | --- | --- | --- | --- |"]
    for _, x in r.iterrows():
        val = "" if x.value is None or (isinstance(x.value, float) and x.value != x.value) else (f"{x.value:,.2f}" if isinstance(x.value, float) else str(x.value))
        lines.append(f"| {x.id} | {x.prediction} | {x.resolve_on} | {val} | {x.status} |")
    RESULTS.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
