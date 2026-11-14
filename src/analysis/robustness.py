"""How fragile is each finding? Every reasonable alternative choice, recomputed, from the committed outputs.

Each finding rests on choices: a window, a source, a denominator, a price date. This step recomputes the
findings' numbers under the alternatives a careful reader would try first, and records for each whether the
finding still holds. A finding that flips under one of them is reported as fragile, not hidden.

Output: data/processed/robustness.csv (finding, variant, value, holds) and robustness.json (summary).
"""
from __future__ import annotations

import json
import math

import numpy as np
import pandas as pd

from .ledger import OUT, RAW, llama_daily, near_price

FEE_SWITCH = "2026-02-23"


def _j(name: str) -> dict:
    return json.loads((OUT / name).read_text())


def f1(rows: list) -> None:
    rev = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True)
    end = rev.index.max() - pd.Timedelta(days=1)
    settle = _j("source_revisions.json")["defillama"]["holders revenue"]["settled_after_days"]
    snap = pd.Timestamp(_j("source_revisions.json")["defillama"]["holders revenue"]["snapshots"][-1])

    def ratio(a, b):
        x = rev.loc[a:b]
        return float(x["rebuilt_total_usd"].sum() / x["llama_holders_revenue_usd"].sum())
    add = lambda v, val: rows.append({"finding": "F1", "variant": v, "value": val, "holds": abs(val - 1) <= 0.02})  # noqa: E731
    add("baseline: fee switch to the last complete day", ratio(FEE_SWITCH, end))
    add(f"settled DefiLlama days only (to {(snap - pd.Timedelta(days=settle)).date()})", ratio(FEE_SWITCH, snap - pd.Timedelta(days=settle)))
    add("from 1 March (first full month)", ratio("2026-03-01", end))
    add("last 90 days", ratio(end - pd.Timedelta(days=89), end))
    add("last 30 days", ratio(end - pd.Timedelta(days=29), end))
    m = rev.loc["2026-03-01":"2026-10-31"].resample("MS")[["rebuilt_total_usd", "llama_holders_revenue_usd"]].sum()
    r = m["rebuilt_total_usd"] / m["llama_holders_revenue_usd"]
    rows.append({"finding": "F1", "kind": "stress", "variant": f"worst full month ({r.sub(1).abs().idxmax():%b})", "value": float(r[r.sub(1).abs().idxmax()]),
                 "holds": abs(float(r[r.sub(1).abs().idxmax()]) - 1) <= 0.05, "note": "a single month is held to ±5%"})


def f3(rows: list) -> None:
    sm = pd.read_csv(OUT / "supply_monthly.csv", index_col=0, parse_dates=True)
    off = _j("official_crosscheck.json")["offset_feb_to_last_full_month"]

    def share(a, b, col="captured_near_3_wallets"):
        x = sm.loc[a:b]
        return float(x[col].sum() / x["net_issuance_near"].sum())
    add = lambda v, val: rows.append({"finding": "F3", "variant": v, "value": val, "holds": val < 0.2})  # noqa: E731
    add("baseline: Feb–Oct, three wallets", off["rebuilt"])
    add("NEAR's dashboard (its revenue and emissions series)", off["official"])
    add("Mar–Oct (first full month)", share("2026-03-01", "2026-10-01"))
    add("Aug–Oct (since the take rose)", share("2026-08-01", "2026-10-01"))
    rows.append({"finding": "F3", "kind": "stress", "variant": "best single month since February",
                 "value": float(sm.loc["2026-02-01":"2026-10-01", "captured_share_of_issuance"].max()),
                 "holds": float(sm.loc["2026-02-01":"2026-10-01", "captured_share_of_issuance"].max()) < 0.2})
    add("buyback multisig only", share("2026-02-01", "2026-10-01", "captured_near_buyback_wallet"))


def f4(rows: list) -> None:
    rev = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True)["rebuilt_total_usd"]
    rev = rev.loc[:rev.index.max() - pd.Timedelta(days=1)]
    comps = pd.read_csv(OUT / "comps.csv")
    mcap = float(comps.loc[comps.token == "NEAR", "market_cap_usd"].iloc[0])
    hy = pd.read_csv(OUT / "holder_yield.csv").set_index("measure")["value"]
    cut = 1 / (hy.iloc[0] * 1.6 / 2.5)
    price = near_price().dropna()
    p_now = float(price.iloc[-1])
    for days in (30, 60, 90, 180):
        mult = mcap / (rev.iloc[-days:].sum() * 365 / days)
        rows.append({"finding": "F4", "variant": f"revenue annualised over the last {days} days", "value": mult, "holds": mult > cut,
                     "note": f"post-cut break-even {cut:.0f}x"})
    best = rev.rolling(30).sum().max() * 365 / 30
    rows.append({"finding": "F4", "variant": "best 30 days since the fee switch, annualised", "value": mcap / best, "holds": mcap / best > cut})
    mult30 = mcap / (rev.iloc[-30:].sum() * 365 / 30)
    be = p_now * cut / mult30
    rows.append({"finding": "F4", "kind": "stress", "variant": "NEAR price at which today's revenue would reach the post-cut break-even",
                 "value": be, "holds": be < p_now, "note": f"against ${p_now:.2f} on {price.index[-1]:%Y-%m-%d}; lowest of the last year ${float(price.iloc[-365:].min()):.2f}"})


def f5(rows: list) -> None:
    om = pd.read_csv(OUT / "official_monthly.csv", index_col=0, parse_dates=True)
    rev = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True)["rebuilt_total_usd"]
    vol = llama_daily("llama_volume", "v")
    vol.index = pd.to_datetime(vol.index).tz_localize(None)
    t = lambda a, b: float(rev.loc[a:b].sum() / vol.loc[a:b].sum() * 1e4)  # noqa: E731
    add = lambda v, a, o: rows.append({"finding": "F5", "variant": v, "value": o / a, "holds": o >= 2 * a, "note": f"{a:.1f} → {o:.1f} bps"})  # noqa: E731
    add("baseline: NEAR-reported volume, August vs October", om.loc["2026-08-01", "take_bps"], om.loc["2026-10-01", "take_bps"])
    add("DefiLlama volume, August vs October", t("2026-08-01", "2026-08-31"), t("2026-10-01", "2026-10-31"))
    add("DefiLlama volume, last two weeks of Aug vs of Oct", t("2026-08-18", "2026-08-31"), t("2026-10-18", "2026-10-31"))
    add("DefiLlama volume, July–August vs October", t("2026-07-01", "2026-08-31"), t("2026-10-01", "2026-10-31"))


def f8(rows: list) -> None:
    cf = _j("confidential_summary.json")
    drop = cf["incentive"]["drop1_usd_at_conversion"]
    rev = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True)["rebuilt_total_usd"]
    vol = llama_daily("llama_volume", "v")
    vol.index = pd.to_datetime(vol.index).tz_localize(None)
    so_v, so_r = vol.loc["2026-09-01":"2026-10-31"].sum(), rev.loc["2026-09-01":"2026-10-31"].sum()
    for a, label in (("2026-05-01", "May–Aug"), ("2026-06-01", "Jun–Aug"), ("2026-07-01", "Jul–Aug"), ("2026-08-01", "August")):
        base = rev.loc[a:"2026-08-31"].sum() / vol.loc[a:"2026-08-31"].sum()
        up = so_r - so_v * base
        rows.append({"finding": "F8", "variant": f"take before the campaign = {label} (DefiLlama volume)", "value": drop / up, "holds": drop / up < 1,
                     "note": "Drop 1 cost / uplift"})
    up = cf["counterfactual"]["uplift_usd"]
    for k in (1.25, 1.5):
        rows.append({"finding": "F8", "kind": "stress", "variant": f"Drop 1 valued at {k:.2f}x the conversion price", "value": drop * k / up, "holds": drop * k / up < 1})


def f10(rows: list) -> None:
    tvl = pd.read_csv(OUT / "confidential_tvl.csv", index_col=0, parse_dates=True)["confidential_tvl_usd"]
    at = float(tvl.loc["2026-09-16"])
    for d in (14, 30, 45, 60):
        day = pd.Timestamp("2026-09-16") + pd.Timedelta(days=d)
        if day in tvl.index:
            rows.append({"finding": "F10", "variant": f"TVL {d} days after the snapshot vs at it", "value": float(tvl.loc[day]) / at, "holds": float(tvl.loc[day]) > at})
    rows.append({"finding": "F10", "variant": "lowest TVL since the snapshot vs at it", "value": float(tvl.loc["2026-09-17":].min()) / at,
                 "holds": float(tvl.loc["2026-09-17":].min()) > at})


def f11(rows: list) -> None:
    sc = pd.read_csv(OUT / "montecarlo_scenarios.csv")
    for r in sc.itertuples():
        v = float(r.median_offset_2027)
        stress = any(w in r.name for w in ("hyper-growth", "doubles", "bull"))
        rows.append({"finding": "F11", "kind": "stress" if stress else "alternative", "variant": f"scenario: {r.name}", "value": v, "holds": v < 1,
                     "note": "median share of 2027 issuance offset"})
    se = pd.read_csv(OUT / "montecarlo_sensitivity.csv", index_col=0)
    rows.append({"finding": "F11", "kind": "info", "variant": f"sensitivity grid: cells where supply still grows ({se.size} cells)", "value": float((se < 1).mean().mean()),
                 "holds": True, "note": "share of volume × take cells below 100%; informative, not a test"})


def f12(rows: list) -> None:
    payload = json.loads(sorted((RAW / "comps").glob("*.json"))[-1].read_text())
    hr = pd.DataFrame(payload["holders_revenue"])
    by30 = hr.groupby("parentProtocol")["total30d"].sum()
    by1y = hr.groupby("parentProtocol")["total1y"].sum()
    from .comps import PEERS
    mk = {m["id"]: m for m in payload["markets"]}
    rev = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True)["rebuilt_total_usd"]
    since = rev.loc[FEE_SWITCH:rev.index.max() - pd.Timedelta(days=1)]
    near_annual = since.sum() * 365 / len(since)
    for label, peer_rev in (("30 days ×365/30 (baseline)", lambda p: by30.get(p, 0) * 365 / 30), ("last 12 months (DefiLlama total1y)", lambda p: by1y.get(p, 0))):
        mult = {}
        for cid, parent in PEERS.items():
            if cid == "near" or cid not in mk:
                continue
            a = float(peer_rev(parent) or 0)
            if a >= 100_000 * 365 / 30:
                mult[cid] = mk[cid]["market_cap"] / a
        s = pd.Series(mult)
        near = mk["near"]["market_cap"] / (by30.get(PEERS["near"], 0) * 365 / 30 if "30" in label else near_annual)
        rows.append({"finding": "F12", "variant": f"annualised over {label}", "value": near, "holds": near > s.quantile(0.75),
                     "note": f"peers median {s.median():.0f}x, Q3 {s.quantile(0.75):.0f}x ({len(s)} peers)"})


def f13(rows: list) -> None:
    ll = pd.read_csv(OUT / "leadlag.csv")
    n = int(ll["n"].median())
    from statistics import NormalDist
    z = lambda a: NormalDist().inv_cdf(1 - a / 2)  # noqa: E731
    z80 = 0.8416
    for alpha, label in ((0.05, "a single test at 5%"), (0.05 / len(ll), f"the strictest Holm step ({len(ll)} tests)")):
        r = math.tanh((z(alpha) + z80) / math.sqrt(n - 3))
        rows.append({"finding": "F13", "kind": "info", "variant": f"smallest |r| detected with 80% power, {label}, n = {n} weeks", "value": r, "holds": True,
                     "note": "power, not a test: a weaker lead could exist and go undetected"})
    rows.append({"finding": "F13", "variant": "largest correlation found (absolute)", "value": float(ll["r"].abs().max()), "holds": float(ll["p_holm"].min()) >= 0.05})


def main() -> dict:
    rows: list = []
    for f in (f1, f3, f4, f5, f8, f10, f11, f12, f13):
        f(rows)
    t = pd.DataFrame(rows)
    t["note"] = t.get("note", pd.Series(dtype=str)).fillna("")
    t["kind"] = t["kind"].fillna("alternative")
    t.round(6).to_csv(OUT / "robustness.csv", index=False)
    alt = t[t["kind"] == "alternative"]
    summ = {k: {"alternatives": int(len(g)), "hold": int(g["holds"].sum())} for k, g in alt.groupby("finding", sort=False)}
    res = {"findings": summ, "fragile": [k for k, x in summ.items() if x["hold"] < x["alternatives"]], "variants": int(len(t)),
           "alternatives": int(len(alt)), "alternatives_hold": int(alt["holds"].sum()),
           "stress_breaks": [{"finding": r.finding, "variant": r.variant, "value": r.value} for r in t[(t["kind"] == "stress") & ~t["holds"]].itertuples()],
           "note": "alternative = the same claim under another reasonable choice (a flip makes the finding fragile); stress = a harder "
                   "test the claim does not make (where it would break); info = context such as statistical power"}
    (OUT / "robustness.json").write_text(json.dumps(res, indent=1))
    for r in t.itertuples():
        print(f"  {r.finding:4s} {r.kind[:5]:5s} {'holds' if r.holds else 'FLIPS'}  {r.value:10.4f}  {r.variant}  {r.note}")
    print(f"robustness: {len(t)} variants; fragile: {res['fragile'] or 'none'}")
    return res


if __name__ == "__main__":
    main()
