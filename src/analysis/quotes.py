"""Quote race, offline: is 1Click's price competitive, corridor by corridor?

Reads every round saved by `python3 -m src.ingest.quotes` (data/raw/quotes/) and compares, for the same
swap asked within the same minute, what the user receives from 1Click (NEAR Intents) and from Relay,
LI.FI and Across. A positive gap means 1Click pays the user more. All quotes include each router's own
fees; LI.FI's public API adds its default fixed fee (0.25%), so LI.FI is also shown without it, and the
headline compares every router as quoted, with the LI.FI-without-its-fee comparison next to it.

Why it matters for the thesis: NEAR's take sits inside 1Click's price. Where 1Click still pays the user
as much as the best alternative, that take is not being competed away on that corridor; where it pays
less, the gap is the pressure on it.

Outputs: data/processed/quote_race.csv (one row per route and size), quote_race.json (summary).
"""
from __future__ import annotations

import json

import pandas as pd

from .ledger import OUT, RAW

OTHERS = ("relay", "across", "lifi")


def rounds() -> list[dict]:
    return [json.loads(f.read_text()) for f in sorted((RAW / "quotes").glob("*.json"))]


def table() -> pd.DataFrame:
    rows = []
    for r in rounds():
        for x in r["rows"]:
            q = {k: v for k, v in x["quotes"].items() if v and v.get("amount_out")}
            if "1click" not in q:
                continue
            out = {k: int(v["amount_out"]) for k, v in q.items()}
            if "lifi" in out and q["lifi"].get("lifi_fee_pct"):
                out["lifi_ex_fee"] = out["lifi"] / (1 - q["lifi"]["lifi_fee_pct"])
            others = {k: v for k, v in out.items() if k != "1click"}
            if not others:
                continue
            asq = {k: v for k, v in others.items() if k != "lifi_ex_fee"}  # every router as its public API quotes it
            best_k = max(asq, key=asq.get)
            row = {"round": r["started_utc"], "route": x["route"], "corridor": x["corridor"], "size_in": x["size_in"],
                   "size": f"{x['size_in']:,g} {x['from'].split('.')[0]}", "competitors": len(asq), "best_competitor": best_k,
                   "gap_vs_best_bps": (out["1click"] / asq[best_k] - 1) * 1e4,
                   "gap_vs_best_ex_lifi_fee_bps": (out["1click"] / max(others.values()) - 1) * 1e4}
            for k in ("relay", "across", "lifi", "lifi_ex_fee"):
                row[f"gap_vs_{k}_bps"] = (out["1click"] / out[k] - 1) * 1e4 if k in out else float("nan")
            rows.append(row)
    return pd.DataFrame(rows)


def main() -> dict:
    t = table()
    g = t.groupby(["route", "corridor", "size_in", "size"], sort=False)
    per = g.agg(rounds=("round", "nunique"), competitors=("competitors", "max"),
                median_gap_vs_best_bps=("gap_vs_best_bps", "median"), min_gap_bps=("gap_vs_best_bps", "min"),
                max_gap_bps=("gap_vs_best_bps", "max"), oneclick_best_share=("gap_vs_best_bps", lambda s: float((s >= 0).mean())),
                median_gap_vs_best_ex_lifi_fee_bps=("gap_vs_best_ex_lifi_fee_bps", "median"),
                median_gap_vs_relay_bps=("gap_vs_relay_bps", "median"), median_gap_vs_across_bps=("gap_vs_across_bps", "median"),
                median_gap_vs_lifi_ex_fee_bps=("gap_vs_lifi_ex_fee_bps", "median"),
                most_often_best_rival=("best_competitor", lambda s: s.mode().iloc[0])).reset_index()
    per.round(4).to_csv(OUT / "quote_race.csv", index=False)
    cor = t.groupby("corridor", sort=False)["gap_vs_best_bps"].median()
    summary = {
        "rounds": int(t["round"].nunique()), "first_round": t["round"].min(), "last_round": t["round"].max(),
        "quotes_compared": int(len(t)),
        "oneclick_best_share": float((t["gap_vs_best_bps"] >= 0).mean()),
        "oneclick_best_share_ex_lifi_fee": float((t["gap_vs_best_ex_lifi_fee_bps"] >= 0).mean()),
        "median_gap_vs_best_ex_lifi_fee_bps": float(t["gap_vs_best_ex_lifi_fee_bps"].median()),
        "median_gap_vs_best_bps": float(t["gap_vs_best_bps"].median()),
        "by_corridor_median_gap_bps": {k: round(float(v), 2) for k, v in cor.items()},
        "best_corridor": cor.idxmax(), "worst_corridor": cor.idxmin(),
        "note": "gap = 1Click's output over the best competitor's for the same swap, in basis points; positive = 1Click pays the user more. "
                "Every router as its public API quotes it, fees included; LI.FI's quote includes its default 0.25% fixed fee, "
                "so the comparison is also given with LI.FI's output grossed up by that fee ('ex LI.FI fee', the harder test for 1Click).",
    }
    (OUT / "quote_race.json").write_text(json.dumps(summary, indent=1))
    print(f"quotes: {summary['rounds']} rounds, {summary['quotes_compared']} swaps; 1Click pays the most in "
          f"{summary['oneclick_best_share']:.0%} (ex LI.FI fee {summary['oneclick_best_share_ex_lifi_fee']:.0%}); "
          f"median gap {summary['median_gap_vs_best_bps']:+.1f} bps; by corridor {summary['by_corridor_median_gap_bps']}")
    return summary


if __name__ == "__main__":
    main()
