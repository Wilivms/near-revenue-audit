"""The freeze and the exploit (29 Sep to 2 Oct 2026): did NEAR Intents' business survive them?

On 29 September 1Click blocked a $50M swap linked to the Bitget hacker; on 1 October an exploit in the
Omni deposit and withdrawal path drained about $3.8M and NEAR Intents stopped its services; the funds
were returned on 2 October. A durable-revenue thesis has to say what that did to the business.

Two steps, like the rest of the 1Click work:
- `collect()` needs the per-swap 1Click data (partner key, kept private) and saves only aggregates to
  data/raw/oneclick_aggregates/incident_2026-10.json: the swaps around the halt by minute, daily totals,
  and each large integrator's volume in the windows below (`make incident-collect`).
- `main()` works offline from that file and DefiLlama's daily volumes of the rival cross-chain venues
  (THORChain, Chainflip, Maya) in the latest comps snapshot (`make incident`).

What it measures:
1. The halt itself, from the swaps: the longest gap with no swap on 1 October, and NEAR's 1Click revenue
   it cost at the previous week's hourly pace.
2. Volume and NEAR's revenue on the median day of the 14 days after (3 to 16 Oct) against the 14 days before (15 to 28 Sep),
   against the rival venues over the same days (difference in differences), and against a placebo: the
   same comparison one month earlier (18 to 31 Aug against 1 to 14 Sep), when nothing happened.
3. Integrator retention: of the 25 largest integrators before, how many kept at least half their volume
   after, against the same count in the placebo windows.
"""
from __future__ import annotations

import glob
import json

import pandas as pd

from .ledger import OUT, RAW

AGG = RAW / "oneclick_aggregates" / "incident_2026-10.json"
WINDOWS = {"event": (("2026-09-15", "2026-09-28"), ("2026-10-03", "2026-10-16")),
           "placebo": (("2026-08-18", "2026-08-31"), ("2026-09-01", "2026-09-14"))}
TOP = 25
RIVALS = ["thorchain-dex", "chainflip-amm", "maya-protocol"]


def collect() -> dict:
    from . import swaps
    keep = lambda f: "2026-08-17" <= f.split("swaps_")[1][:10] <= "2026-10-18"  # noqa: E731
    files = [f for f in sorted(glob.glob(str(swaps.DATA / "swaps_*.csv.gz"))) if keep(f)]
    real = swaps.glob.glob
    swaps.glob.glob = lambda pattern: files
    try:
        df = swaps.load()
    finally:
        swaps.glob.glob = real
    df = df[(df["ts"] >= "2026-08-18") & (df["ts"] < "2026-10-17")]
    day = df["ts"].dt.strftime("%Y-%m-%d")
    daily = df.groupby(day).agg(swaps=("usd", "size"), volume_usd=("usd", "sum"), fee_usd=("fee_usd", "sum"),
                                near_usd=("near_usd", "sum"), integrators=("ref", "nunique"))
    around = df[(df["ts"] >= "2026-09-24") & (df["ts"] < "2026-10-03")]
    minute = around.groupby(around["ts"].dt.floor("min")).agg(swaps=("usd", "size"), volume_usd=("usd", "sum"), near_usd=("near_usd", "sum"))
    by_ref = {}
    for name, (before, after) in WINDOWS.items():
        b = df[(day >= before[0]) & (day <= before[1]) & (df["ref"] != "(none)")].groupby("ref")["usd"].sum()
        a = df[(day >= after[0]) & (day <= after[1])].groupby("ref")["usd"].sum()
        top = b.sort_values(ascending=False).head(TOP)
        by_ref[name] = [{"rank": i + 1, "before_usd": round(float(v), 2), "after_usd": round(float(a.get(r, 0.0)), 2)}
                        for i, (r, v) in enumerate(top.items())]  # integrators by rank only: no names needed
    out = {"note": "aggregates of 1Click swaps (NEAR Intents Explorer API); no swap, address or integrator name",
           "daily": daily.round(4).reset_index(names="day").to_dict("records"),
           "minute_2026-09-24_to_10-02": [{"minute": str(k), **{c: round(float(v), 4) for c, v in r.items()}} for k, r in minute.iterrows()],
           "top_integrators": by_ref}
    AGG.parent.mkdir(parents=True, exist_ok=True)
    AGG.write_text(json.dumps(out))
    print(f"incident: saved {AGG.relative_to(RAW.parents[1])} ({len(df):,} swaps aggregated)")
    return out


def _rivals() -> pd.Series:
    payload = json.loads(sorted((RAW / "comps").glob("*.json"))[-1].read_text())
    frames = {s: pd.Series({pd.to_datetime(t, unit="s").strftime("%Y-%m-%d"): v for t, v in payload["crosschain_volume"][s]})
              for s in RIVALS if isinstance(payload["crosschain_volume"].get(s), list)}
    return pd.DataFrame(frames).fillna(0.0).sum(axis=1)


def _mean(s: pd.Series, w: tuple[str, str]) -> float:
    # the median day: rival venues carried a few very large days on 25-30 Sep (about $250M-300M a day against
    # about $50M usually), which a mean would read as the market collapsing afterwards
    return float(s[(s.index >= w[0]) & (s.index <= w[1])].median())


def main() -> dict:
    agg = json.loads(AGG.read_text())
    daily = pd.DataFrame(agg["daily"]).set_index("day")
    m = pd.DataFrame(agg["minute_2026-09-24_to_10-02"])
    m["minute"] = pd.to_datetime(m["minute"])
    # 1. the halt: the longest gap between two swaps on 1 October
    oct1 = m[(m["minute"] >= "2026-10-01") & (m["minute"] < "2026-10-02")].sort_values("minute")
    gaps = oct1["minute"].diff()
    i = gaps.idxmax()
    last_before, first_after = oct1.loc[oct1.index[oct1.index.get_loc(i) - 1], "minute"], oct1.loc[i, "minute"]
    hours = (first_after - last_before).total_seconds() / 3600
    week = m[(m["minute"] >= "2026-09-24") & (m["minute"] < "2026-10-01")]
    hourly = week.groupby(week["minute"].dt.floor("h"))[["near_usd", "volume_usd"]].sum()
    halt = {"last_swap_before_utc": str(last_before), "first_swap_after_utc": str(first_after), "hours": round(hours, 2),
            "near_revenue_forgone_usd": round(hours * float(hourly["near_usd"].median()), 0),
            "volume_forgone_usd": round(hours * float(hourly["volume_usd"].median()), 0),
            "longest_gap_in_prior_week_minutes": float(week.sort_values("minute")["minute"].diff().max().total_seconds() / 60)}
    # 2. before and after, against rivals and against a placebo month
    rivals = _rivals()
    windows = {}
    for name, (b, a) in WINDOWS.items():
        r = {}
        for col in ("volume_usd", "near_usd", "swaps", "integrators"):
            r[col] = {"before_per_day": _mean(daily[col], b), "after_per_day": _mean(daily[col], a)}
            r[col]["change"] = r[col]["after_per_day"] / r[col]["before_per_day"] - 1
        r["rivals_volume"] = {"before_per_day": _mean(rivals, b), "after_per_day": _mean(rivals, a)}
        r["rivals_volume"]["change"] = r["rivals_volume"]["after_per_day"] / r["rivals_volume"]["before_per_day"] - 1
        r["volume_vs_rivals"] = (1 + r["volume_usd"]["change"]) / (1 + r["rivals_volume"]["change"]) - 1
        top = agg["top_integrators"][name]
        r["top_integrators_kept_half"] = sum(1 for x in top if x["after_usd"] >= 0.5 * x["before_usd"])
        r["top_integrators"] = len(top)
        r["top_integrators_volume_change"] = sum(x["after_usd"] for x in top) / sum(x["before_usd"] for x in top) - 1
        r["windows"] = {"before": list(b), "after": list(a)}
        windows[name] = r
    e, p = windows["event"], windows["placebo"]
    res = {"halt": halt, "event": e, "placebo": p,
           "volume_vs_rivals_beyond_placebo": (1 + e["volume_vs_rivals"]) / (1 + p["volume_vs_rivals"]) - 1,
           "retention_event_vs_placebo": [e["top_integrators_kept_half"], p["top_integrators_kept_half"], TOP]}
    (OUT / "incident.json").write_text(json.dumps(res, indent=1))
    print(f"incident: halt {hours:.1f} h ({last_before:%H:%M} to {first_after:%H:%M} UTC, 1 Oct), NEAR revenue forgone about "
          f"${halt['near_revenue_forgone_usd']:,.0f}; volume {e['volume_usd']['change']:+.0%} after vs before "
          f"(rivals {e['rivals_volume']['change']:+.0%}; placebo month {p['volume_usd']['change']:+.0%}, rivals {p['rivals_volume']['change']:+.0%}); "
          f"top {TOP} integrators keeping half their volume: {e['top_integrators_kept_half']} (placebo {p['top_integrators_kept_half']})")
    return res


if __name__ == "__main__":
    import sys
    collect() if "--collect" in sys.argv else main()
