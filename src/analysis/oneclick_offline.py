"""Recompute the 1Click results from the published daily aggregates, without the partner key.

The per-swap 1Click data comes from the NEAR Intents Explorer API, which needs a partner key and whose
terms do not allow archiving or redistributing it, so it is not in the repository. What is committed is
`data/processed/oneclick_daily.csv`: daily sums by integrator (referral), route type (same asset family
or not), NEAR fee tier and ZEC flag, with no swap, sender or address. This module rebuilds from that
file the 1Click figures the documents quote and compares them with the outputs of `make swaps`:

- integrators' share of the fee pool and each integrator's share of app fees and of NEAR's revenue (last 30 days);
- NEAR's 1Click take in the second half of October and the first ten days of November, with and
  without Trust Wallet, revenue without an integrator, and ZEC;
- the fee-schedule test (share of volume paying NEAR 20 bps or more, 1 bp, nothing).

The published outputs cut their 30-day window at the second; the daily file cuts at midnight, so the
comparison allows 1.5% (relative, or 0.5 percentage point on shares).

Output: data/processed/oneclick_offline_check.json
"""
from __future__ import annotations

import json
import sys

import pandas as pd

from .ledger import OUT

TOL_REL, TOL_ABS = 0.015, 0.005


def _load() -> pd.DataFrame:
    d = pd.read_csv(OUT / "oneclick_daily.csv", keep_default_na=False)
    d["trust"] = d["ref"].str.lower().str.startswith("trust")
    return d


def recompute(d: pd.DataFrame) -> dict:
    out = {}
    # the published window is the 30 days before the last swap, to the second; the daily file keeps every day
    # since 11 October, so keep the 30 days after the one in which the window starts (that day is partial)
    end = pd.Timestamp(d["day"].max())
    last = d[pd.to_datetime(d["day"]) > end - pd.Timedelta(days=30)]
    out["integrators_keep_of_fee_pool"] = float(1 - last["near_usd"].sum() / last["fee_usd"].sum())
    by = last.groupby("ref")[["volume_usd", "fee_usd", "near_usd"]].sum()
    top = by["fee_usd"].idxmax()
    out["top_integrator"] = top
    out["top_integrator_fee_share"] = float(by.loc[top, "fee_usd"] / by["fee_usd"].sum())
    out["top_integrator_near_share"] = float(by.loc[top, "near_usd"] / by["near_usd"].sum())
    out["no_integrator_near_share"] = float(by.loc["(none)", "near_usd"] / by["near_usd"].sum())
    for name, a, b in (("oct16_29", "2026-10-16", "2026-10-29"), ("nov01_10", "2026-11-01", "2026-11-10")):
        s = d[(d["day"] >= a) & (d["day"] <= b)]
        x = s[~s["trust"]]
        n = s[s["ref"] == "(none)"]
        days = (pd.Timestamp(b) - pd.Timestamp(a)).days + 1
        out[name] = {"near_bps": float(s["near_usd"].sum() / s["volume_usd"].sum() * 1e4),
                     "near_bps_ex_trust": float(x["near_usd"].sum() / x["volume_usd"].sum() * 1e4),
                     "noref_near_usd_per_day": float(n["near_usd"].sum() / days),
                     "zec_near_share": float(s.loc[s["zec"], "near_usd"].sum() / s["near_usd"].sum())}
    burst = d[d["trust"] & (d["day"] >= "2026-10-23") & (d["day"] <= "2026-10-28")]
    out["trust_burst_volume_usd"] = float(burst["volume_usd"].sum())
    for name, ref, same in (("no_ref_cross", False, False), ("no_ref_same", False, True), ("ref_cross", True, False), ("ref_same", True, True)):
        m = last[((last["ref"] != "(none)") == ref) & (last["same_family"] == same)]
        w = m["volume_usd"].sum()
        out[name] = {"near_bps": float(m["near_usd"].sum() / w * 1e4),
                     "share_at_20_or_more": float(m.loc[m["near_tier"] == "20+", "volume_usd"].sum() / w),
                     "share_at_1": float(m.loc[m["near_tier"] == "1", "volume_usd"].sum() / w),
                     "share_at_0": float(m.loc[m["near_tier"] == "0", "volume_usd"].sum() / w)}
    return out


def published() -> dict:
    nov = json.loads((OUT / "oneclick_november.json").read_text())
    fp = json.loads((OUT / "oneclick_fee_policy.json").read_text())
    fs = pd.read_csv(OUT / "fee_shares_last30d.csv", index_col=0)
    top = fs["fee_share"].idxmax()
    out = {"integrators_keep_of_fee_pool": 1 - nov["last30"]["near_share_of_fee_pool"], "top_integrator": top,
           "top_integrator_fee_share": float(fs.loc[top, "fee_share"]), "top_integrator_near_share": float(fs.loc[top, "near_revenue_share"]),
           "no_integrator_near_share": float(fs.loc["(none)", "near_revenue_share"]),
           "trust_burst_volume_usd": nov["trust_burst_oct23_28"]["volume_usd"]}
    for w in ("oct16_29", "nov01_10"):
        out[w] = {k: nov[w][k] for k in ("near_bps", "near_bps_ex_trust", "noref_near_usd_per_day", "zec_near_share")}
    for k in ("no_ref_cross", "no_ref_same", "ref_cross", "ref_same"):
        out[k] = {x: fp[k][x] for x in ("near_bps", "share_at_20_or_more", "share_at_1", "share_at_0")}
    return out


def _compare(a, b, path=""):
    if isinstance(a, dict):
        return [r for k in a for r in _compare(a[k], b[k], f"{path}/{k}")]
    if isinstance(a, str):
        return [] if a == b else [f"{path}: {a} vs {b}"]
    ok = abs(a - b) <= max(TOL_REL * abs(b), TOL_ABS if abs(b) <= 1 else 0)
    return [] if ok else [f"{path}: {a:.4g} recomputed vs {b:.4g} published"]


def main() -> int:
    re, pub = recompute(_load()), published()
    diffs = _compare(re, pub)
    out = {"recomputed": re, "published": pub, "differences": diffs, "agree": not diffs}
    (OUT / "oneclick_offline_check.json").write_text(json.dumps(out, indent=1, default=float))
    for x in diffs:
        print("DIFF", x)
    print(f"1Click figures recomputed from the daily aggregates: {'all agree' if not diffs else f'{len(diffs)} differ'} with the published outputs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
