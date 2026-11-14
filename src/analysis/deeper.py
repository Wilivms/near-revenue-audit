"""Deeper checks on the headline findings, all offline on committed outputs (`make deeper`).

1. When did the take change? Breaks found by the data, not chosen: a one- and a two-break model on NEAR's weekly
   take since the fee switch (least squares on log take), with a residual bootstrap for the break weeks; compared
   with the dated events (confidential intents open to all, the airdrop snapshot).
2. How sure is each month's take? 90% bootstrap intervals, resampling days within the month.
3. Why coverage moved: month-on-month change in "NEAR bought per NEAR issued" split exactly into revenue in
   dollars, the price paid per NEAR, and issuance.
4. What share of the market cap the buybacks justify, in a bear, base and bull case, valued as a perpetuity.
5. Levers: what each thing NEAR could change would do to coverage of issuance, from today's 30 days.
6. Integrators leaving: NEAR's 1Click revenue by integrator, and what it loses if the top ones go.
7. What the elasticity test could have detected (minimum detectable correlation), and a staker's real yield.

Output: data/processed/deeper.json.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .ledger import OUT, llama_daily

FEE_SWITCH = "2026-02-23"
SEED = 7
DISCOUNT, GROWTH = 0.15, 0.03


def _weekly_take() -> pd.Series:
    rev = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True)["rebuilt_total_usd"]
    vol = llama_daily("llama_volume", "v")
    d = pd.concat([rev, vol], axis=1, keys=["rev", "vol"], sort=True).loc[FEE_SWITCH:].dropna()
    w = d.resample("W-SUN").sum()
    w = w[(w.index <= d.index.max()) & (d.resample("W-SUN").size().reindex(w.index) == 7)]
    return (w["rev"] / w["vol"] * 1e4).rename("take_bps")


def _fit(y: np.ndarray, breaks: tuple) -> float:
    edges = [0, *breaks, len(y)]
    return float(sum(((y[a:b] - y[a:b].mean()) ** 2).sum() for a, b in zip(edges[:-1], edges[1:])))


def _best(y: np.ndarray, k: int, m: int = 4) -> tuple:
    n = len(y)
    if k == 1:
        cands = [(i,) for i in range(m, n - m + 1)]
    else:
        cands = [(i, j) for i in range(m, n - m + 1) for j in range(i + m, n - m + 1)]
    return min(cands, key=lambda c: _fit(y, c))


def breaks() -> dict:
    t = _weekly_take()
    y = np.log(t.values)
    out = {"weeks": len(t), "from": str(t.index[0].date()), "to": str(t.index[-1].date())}
    rng = np.random.default_rng(SEED)
    for k in (1, 2):
        b = _best(y, k)
        edges = [0, *b, len(y)]
        fitted = np.concatenate([np.full(e1 - e0, y[e0:e1].mean()) for e0, e1 in zip(edges[:-1], edges[1:])])
        res = y - fitted
        boots = []
        for _ in range(300):
            yb = fitted + rng.choice(res, size=len(y), replace=True)
            boots.append(_best(yb, k))
        boots = np.array(boots)
        weeks = [str(t.index[i].date()) for i in b]  # first week of each new regime (week ending that Sunday)
        ci = [[str(t.index[int(np.percentile(boots[:, j], q))].date()) for q in (5, 95)] for j in range(k)]
        levels = [float(np.exp(y[e0:e1].mean())) for e0, e1 in zip(edges[:-1], edges[1:])]
        sse0 = float(((y - y.mean()) ** 2).sum())
        out[f"model_{k}"] = {"break_weeks_ending": weeks, "ci90": ci, "levels_bps": levels, "r2": 1 - _fit(y, b) / sse0}
    t.to_frame().to_csv(OUT / "take_weekly.csv")
    return out


def monthly_ci() -> list[dict]:
    rev = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True)["rebuilt_total_usd"]
    vol = llama_daily("llama_volume", "v")
    d = pd.concat([rev, vol], axis=1, keys=["rev", "vol"], sort=True).loc[FEE_SWITCH:].dropna()
    rng = np.random.default_rng(SEED)
    rows = []
    for m, g in d.groupby(d.index.to_period("M")):
        if len(g) < 20:
            continue
        idx = rng.integers(0, len(g), size=(2000, len(g)))
        bs = g["rev"].values[idx].sum(1) / g["vol"].values[idx].sum(1) * 1e4
        rows.append({"month": str(m), "days": len(g), "take_bps": float(g["rev"].sum() / g["vol"].sum() * 1e4),
                     "ci90": [float(np.percentile(bs, 5)), float(np.percentile(bs, 95))]})
    return rows


def coverage_split() -> list[dict]:
    sm = pd.read_csv(OUT / "supply_monthly.csv", index_col=0, parse_dates=True)
    rev = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True)["rebuilt_total_usd"]
    usd = rev.groupby(rev.index.to_period("M")).sum()
    sm = sm.loc[FEE_SWITCH[:7] + "-01":]
    sm = sm[sm.index.to_period("M").isin(usd.index)]
    rows, prev = [], None
    for ts, r in sm.iterrows():
        m = ts.to_period("M")
        u, near, iss = float(usd[m]), float(r["captured_near_3_wallets"]), float(r["net_issuance_near"])
        if near <= 0 or u <= 0:
            continue
        cur = {"month": str(m), "revenue_usd": u, "near_bought": near, "price_paid": u / near, "issued_near": iss, "coverage": near / iss}
        if prev:
            cur["change_log"] = float(np.log(cur["coverage"] / prev["coverage"]))
            cur["from_revenue"] = float(np.log(u / prev["revenue_usd"]))
            cur["from_price"] = float(-np.log(cur["price_paid"] / prev["price_paid"]))
            cur["from_issuance"] = float(-np.log(iss / prev["issued_near"]))
        rows.append(cur)
        prev = cur
    return rows


def justified() -> dict:
    im = json.loads((OUT / "implied.json").read_text())
    mcap, annual, take = im["market_cap_usd"], im["revenue_annualised_usd"], im["take_bps"]
    mc = pd.read_csv(OUT / "montecarlo_scenarios.csv")
    bull_mult = 4.0
    mayaug = 2.4  # bps, May-August 2026 (REPORT section 2)
    cases = {"bear: take back to its May-August level": annual * mayaug / take,
             "base: the last 30 days": annual,
             "bull: four times the volume at today's take": annual * bull_mult}
    val = {k: v / (DISCOUNT - GROWTH) for k, v in cases.items()}
    return {"market_cap_usd": mcap, "discount": DISCOUNT, "growth": GROWTH, "scenarios_in_file": int(len(mc)),
            "cases": {k: {"annual_revenue_usd": cases[k], "value_usd": val[k], "share_of_market_cap": val[k] / mcap} for k in cases}}


def levers(cover0: float) -> dict:
    """Coverage of issuance over the same 30 days as Follow $100, if one thing changed (no volume response assumed)."""
    rev = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True)["rebuilt_total_usd"]
    oc = pd.read_csv(OUT / "oneclick_daily.csv")
    end = pd.Timestamp(json.loads((OUT.parent.parent / "dashboard" / "data.json").read_text())["live_fallback"]["as_of"])
    a = str((end - pd.Timedelta(days=29)).date())
    cap = float(rev.loc[a:str(end.date())].sum())
    o = oc[(oc["day"] >= a) & (oc["day"] <= str(end.date()))]
    integ = o[o["ref"] != "(none)"]
    near_now, vol_int = float(integ["near_usd"].sum()), float(integ["volume_usd"].sum())
    gain20 = vol_int * 20e-4 - near_now
    vol = llama_daily("llama_volume", "v").loc[a:str(end.date())].sum()
    take = cap / vol * 1e4
    cut = 1.6 / 2.5
    rows = [
        ("NEAR's published 20 bps applied to all integrator volume on 1Click", cover0 * (cap + gain20) / cap),
        ("take back to its October level (5.5 bps)", cover0 * 5.5 / take),
        ("twice today's volume", cover0 * 2),
        ("issuance cut (HSP-029) fully phased in", cover0 / cut),
        ("20 bps on 1Click integrators and the issuance cut", cover0 * (cap + gain20) / cap / cut),
        ("take of 5.5 bps, twice the volume and the issuance cut", cover0 * 5.5 / take * 2 / cut),
    ]
    return {"window": [a, str(end.date())], "coverage_now": cover0, "take_now_bps": take, "integrator_volume_usd": vol_int,
            "near_from_integrators_usd": near_now, "near_bps_on_integrators": near_now / vol_int * 1e4,
            "gain_20bps_usd": gain20, "rows": [{"lever": k, "coverage": v} for k, v in rows]}


def integrators_leave() -> dict:
    oc = pd.read_csv(OUT / "oneclick_daily.csv")
    end = json.loads((OUT.parent.parent / "dashboard" / "data.json").read_text())["live_fallback"]["as_of"]
    a = str((pd.Timestamp(end) - pd.Timedelta(days=29)).date())
    o = oc[(oc["day"] >= a) & (oc["day"] <= end)]
    g = o.groupby("ref")[["volume_usd", "fee_usd", "near_usd"]].sum()
    near_total, vol_total = g["near_usd"].sum(), g["volume_usd"].sum()
    rev = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True)["rebuilt_total_usd"].loc[a:end]
    cap = float(rev.sum())
    integ = g.drop(index="(none)", errors="ignore").sort_values("near_usd", ascending=False)
    by_vol = g.drop(index="(none)", errors="ignore").sort_values("volume_usd", ascending=False)
    inc = json.loads((OUT / "incident.json").read_text())
    return {"window": [a, end], "oneclick_near_usd": float(near_total), "captured_usd": cap, "oneclick_share_of_captured": float(near_total / cap),
            "no_integrator_share_of_oneclick_near": float(g.loc["(none)", "near_usd"] / near_total) if "(none)" in g.index else 0.0,
            "top1_by_near": {"ref": integ.index[0], "share_of_oneclick_near": float(integ["near_usd"].iloc[0] / near_total),
                             "share_of_captured": float(integ["near_usd"].iloc[0] / cap)},
            "top3_by_near": {"refs": list(integ.index[:3]), "share_of_oneclick_near": float(integ["near_usd"].iloc[:3].sum() / near_total),
                             "share_of_captured": float(integ["near_usd"].iloc[:3].sum() / cap)},
            "top1_by_volume": {"ref": by_vol.index[0], "share_of_oneclick_volume": float(by_vol["volume_usd"].iloc[0] / vol_total),
                               "share_of_oneclick_near": float(by_vol["near_usd"].iloc[0] / near_total)},
            "incident_comeback": inc.get("comeback")}


def mde(n: int, alpha: float = 0.05, power: float = 0.8) -> float:
    z = 1.959963984540054 + 0.8416212335729143  # two-sided 5%, 80% power
    return float(np.tanh(z / np.sqrt(n - 3)))


def staker() -> dict:
    h = pd.read_csv(OUT / "holder_yield.csv", index_col=0)["value"]
    gross, growth = float(h["Staker gross reward, % a year (before commission)"]), float(h["Net supply growth, % a year"])
    return {"gross": gross, "net_supply_growth": growth,
            "real_before_commission": (1 + gross) / (1 + growth) - 1,
            "real_at_10pct_commission": (1 + gross * 0.9) / (1 + growth) - 1,
            "unstaked_real": 1 / (1 + growth) - 1}


def path_to_yes(lf: dict, iss: float, take_bps: float) -> dict:
    """Month by month to December 2027: the daily Intents volume at which buybacks would match issuance, at today's
    price, with the HSP-029 ramp (no earlier than 14 Feb 2027, 24 months to 1.6/2.5 of the cap), against actual volume."""
    months = pd.date_range("2026-03-01", "2027-12-01", freq="MS")
    start, end_ramp = pd.Timestamp("2027-02-14"), pd.Timestamp("2029-02-14")

    def rate(t):
        if t < start:
            return iss
        x = min(1.0, (t - start) / (end_ramp - start))
        return iss * (1 - x * (1 - 1.6 / 2.5))
    vol = llama_daily("llama_volume", "v")
    actual = vol.loc[FEE_SWITCH:lf["as_of"]].groupby(vol.loc[FEE_SWITCH:lf["as_of"]].index.to_period("M")).mean()
    rows = []
    for m in months:
        need_rev = lf["supply"] * rate(m + pd.Timedelta(days=14)) / 365 * lf["price"]
        rows.append({"month": str(m.date())[:7], "issuance_rate": rate(m + pd.Timedelta(days=14)),
                     "volume_needed_now_take": need_rev / (take_bps / 1e4), "volume_needed_8bps": need_rev / 8e-4,
                     "volume_actual": float(actual[m.to_period("M")]) if m.to_period("M") in actual.index else None})
    v_now = float(vol.loc[:lf["as_of"]].iloc[-30:].mean())
    need_end = rows[-1]["volume_needed_now_take"]
    months_left = (pd.Timestamp("2027-12-01").to_period("M") - pd.Timestamp(lf["as_of"]).to_period("M")).n
    return {"rows": rows, "volume_now": v_now, "take_bps": take_bps, "price": lf["price"],
            "needed_dec_2027": need_end, "multiple_needed": need_end / v_now,
            "monthly_growth_needed": (need_end / v_now) ** (1 / months_left) - 1, "months_left": months_left}


def main() -> dict:
    lf = json.loads((OUT.parent.parent / "dashboard" / "data.json").read_text())["live_fallback"]
    rev = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True)["rebuilt_total_usd"]
    end = pd.Timestamp(lf["as_of"])  # the same 30 days as Follow $100
    cap30 = float(rev.loc[str((end - pd.Timedelta(days=29)).date()):str(end.date())].sum())
    iss = float(pd.read_csv(OUT / "holder_yield.csv", index_col=0)["value"]["NEAR issuance, % of supply a year"])
    cover0 = cap30 / (lf["supply"] * iss / 365 * 30 * lf["price"])
    el = json.loads((OUT / "elasticity.json").read_text())
    n = el["cross_section"]["integrators"]
    res = {"breaks": breaks(), "monthly_take": monthly_ci(), "coverage_split": coverage_split(), "justified": justified(),
           "levers": levers(cover0), "integrators_leave": integrators_leave(),
           "elasticity_mde": {"integrators": n, "min_detectable_spearman": mde(n), "observed": el["cross_section"]["spearman"]},
           "staker": staker()}
    res["path_to_yes"] = path_to_yes(lf, iss, res["levers"]["take_now_bps"])
    (OUT / "deeper.json").write_text(json.dumps(res, indent=1, default=str))
    b1, b2 = res["breaks"]["model_1"], res["breaks"]["model_2"]
    print(f"deeper: one break, week ending {b1['break_weeks_ending'][0]} (90% {b1['ci90'][0]}), {b1['levels_bps'][0]:.1f} -> {b1['levels_bps'][1]:.1f} bps; "
          f"two breaks {b2['break_weeks_ending']} levels {[round(x, 1) for x in b2['levels_bps']]} (R2 {b2['r2']:.2f})")
    for r in res["monthly_take"]:
        print(f"  take {r['month']}: {r['take_bps']:.2f} bps (90% {r['ci90'][0]:.2f}-{r['ci90'][1]:.2f})")
    for r in res["coverage_split"][1:]:
        print(f"  coverage {r['month']}: {r['coverage']:.1%}  change {r['change_log']:+.2f} = revenue {r['from_revenue']:+.2f} + price {r['from_price']:+.2f} + issuance {r['from_issuance']:+.2f}")
    for k, v in res["justified"]["cases"].items():
        print(f"  justified {k}: {v['share_of_market_cap']:.1%} of market cap")
    for r in res["levers"]["rows"]:
        print(f"  lever {r['lever']}: coverage {r['coverage']:.0%}")
    il = res["integrators_leave"]
    print(f"  1Click is {il['oneclick_share_of_captured']:.0%} of captured; top integrator by NEAR revenue {il['top1_by_near']['ref']} "
          f"{il['top1_by_near']['share_of_captured']:.1%} of captured; top 3 {il['top3_by_near']['share_of_captured']:.1%}; "
          f"top by volume {il['top1_by_volume']['ref']} {il['top1_by_volume']['share_of_oneclick_volume']:.0%} of volume, {il['top1_by_volume']['share_of_oneclick_near']:.1%} of NEAR's 1Click revenue")
    py = res["path_to_yes"]
    print(f"  path to yes: {py['multiple_needed']:.1f}x today's volume by Dec 2027 at {py['take_bps']:.1f} bps, {py['monthly_growth_needed']:.1%} a month")
    print(f"  elasticity MDE {res['elasticity_mde']['min_detectable_spearman']:.2f} with {n} integrators; staker real {res['staker']['real_before_commission']:+.2%} (before commission)")
    return res


if __name__ == "__main__":
    main()
