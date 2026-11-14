"""The verdict, computed: three questions (real, durable, sufficient) and the three conditions that would turn it
constructive, each with a status recomputed from the data on every run (`make verdict`).

The rule was written before it was computed (README, "The verdict"): constructive if two of the three conditions
hold for a quarter (13 weeks, or 3 months for a monthly measure). The daily refresh recomputes it, so the dashboard's
banner moves with the data, not with an author's mood. Also tracked: the condition that would prove the "partly
bought" reading wrong (the take holding at 5 bps or more for 60 days).

Output: data/processed/verdict.json.
"""
from __future__ import annotations

import json

import pandas as pd

from .ledger import OUT

TAKE_BAR = 5.0        # bps
COVER_BAR = 0.50      # half of issuance
QUARTER_WEEKS = 13


def main() -> dict:
    tw = pd.read_csv(OUT / "take_weekly.csv", index_col=0, parse_dates=True)["take_bps"]
    sm = pd.read_csv(OUT / "supply_monthly.csv", index_col=0, parse_dates=True)
    sm = sm[sm["captured_near_3_wallets"] > 0]
    dp = json.loads((OUT / "deeper.json").read_text())
    ct = json.loads((OUT / "control.json").read_text())
    rev_ok = all(r["passed"] for r in _findings() if r["id"] in ("F1", "F2", "F19"))
    last13 = tw.iloc[-QUARTER_WEEKS:]
    weeks_take = int((last13 >= TAKE_BAR).sum())
    streak = 0
    for x in tw.iloc[::-1]:
        if x < TAKE_BAR:
            break
        streak += 1
    cover_now = dp["levers"]["coverage_now"]
    last3 = sm["captured_share_of_issuance"].iloc[-3:]
    months_cover = int((last3 >= COVER_BAR).sum())
    locked = (ct["burned_near"] + ct["locked_near"]) / ct["held_near"]

    def status(now_ok: bool, quarter_ok: bool) -> str:
        return "met for a quarter" if quarter_ok else ("met now" if now_ok else "not met")
    conds = [
        {"id": "C1", "condition": f"NEAR's take at {TAKE_BAR:g} bps or more", "now": f"{tw.iloc[-1]:.1f} bps (week ending {tw.index[-1]:%d %b})",
         "record": f"{weeks_take} of the last {QUARTER_WEEKS} weeks", "status": status(tw.iloc[-1] >= TAKE_BAR, weeks_take == QUARTER_WEEKS)},
        {"id": "C2", "condition": "revenue covers half of new issuance or more", "now": f"{cover_now:.0%} (last 30 days)",
         "record": f"{months_cover} of the last 3 months", "status": status(cover_now >= COVER_BAR, months_cover == 3)},
        {"id": "C3", "condition": "bought NEAR burned or locked by a rule", "now": f"{locked:.0%} of {ct['held_near'] / 1e6:.2f}M NEAR held",
         "record": f"read on {ct['read_at'][:10]}", "status": status(locked > 0, False)},
    ]
    met_quarter = sum(c["status"] == "met for a quarter" for c in conds)
    peak = max(r["take_bps"] for r in dp["monthly_take"])
    take4 = float(tw.iloc[-4:].mean())  # the last four complete weeks
    durable = "holds" if take4 >= 0.8 * peak else ("weakening" if take4 > 2.4 else "fading")
    res = {
        "rule": "constructive if two of the three conditions hold for a quarter",
        "verdict": "constructive" if met_quarter >= 2 else "not constructive",
        "questions": [
            {"q": "Real?", "answer": "yes" if rev_ok else "check", "why": "rebuilt from the chain; F1, F2 and F19 hold" if rev_ok else "a reconciliation finding fails"},
            {"q": "Durable?", "answer": durable, "why": f"take {take4:.1f} bps over the last four weeks against a {peak:.1f} bps monthly peak (October); 2.4 bps was its May-August level"},
            {"q": "Sufficient?", "answer": "yes" if cover_now >= 1 else "no", "why": f"buybacks cover {cover_now:.0%} of new issuance (100% stops supply growing)"},
        ],
        "conditions": conds, "met_for_a_quarter": met_quarter,
        "bought_reading_refuted": {"rule": f"the take holds at {TAKE_BAR:g} bps or more for 60 days (about 9 weeks)",
                                   "streak_weeks": streak, "refuted": streak >= 9},
    }
    (OUT / "verdict.json").write_text(json.dumps(res, indent=1))
    print(f"verdict: {res['verdict']} ({met_quarter} of 3 conditions held for a quarter); "
          + "; ".join(f"{q['q']} {q['answer']}" for q in res["questions"]) + "; "
          + "; ".join(f"{c['id']} {c['status']} ({c['now']})" for c in conds))
    return res


def _findings() -> list[dict]:
    from ..figures import claims
    return claims()


if __name__ == "__main__":
    main()
