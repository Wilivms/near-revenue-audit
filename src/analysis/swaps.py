"""Swap-level analysis of 1Click data (collector v2, data/intents_v2).

Covers what the Intents Explorer API can see: 1Click swaps only (~28% of Intents volume),
no confidential swaps. Every result below is about the 1Click channel.

Outputs (data/processed/):
- swaps_weekly.csv     one row per 7-day period (Feb–Jul sample weeks, then weekly from Aug 15): volume, NEAR's bps, ZEC share, mix, concentration
- snapshot_windows.csv before / after the NEAR@3.33 snapshot (2026-09-15/17)
- retention.csv        sender retention between sample weeks and into the continuous window
- revenue_by_asset_last30d.csv volume and NEAR revenue by the volatile leg of each swap (last 30 days)
- fee_shares_last30d.csv each referral's share of volume, app fees and NEAR revenue (last 30 days)
- oneclick_quality.json  is the volume broad? sender concentration, heavy senders and round trips (last 30 days)
- snapshot_entrants.csv retention of senders who arrived just before the snapshot vs a placebo cohort
"""
from __future__ import annotations

import glob
import json

import numpy as np
import pandas as pd

from ..ingest.sources import ROOT, REVENUE_WALLETS

DATA = ROOT / "data" / "intents_v2"
OUT = ROOT / "data" / "processed"
COLS = ["created_at", "status", "origin_asset", "destination_asset", "amount_in_usd",
        "referral", "app_fees", "deposit_type", "sender_hash", "deposit_address", "deposit_memo"]
NEAR_WALLETS = set(REVENUE_WALLETS)
SNAPSHOT = pd.Timestamp("2026-09-16", tz="UTC")  # middle of the 2026-09-15/17 snapshot window
CONTINUOUS_START = pd.Timestamp("2026-08-15", tz="UTC")


def _near_bps(app_fees: str) -> int:
    """Basis points of a swap paid to NEAR's revenue wallets."""
    if not isinstance(app_fees, str) or not app_fees:
        return 0
    total = 0
    for part in app_fees.split("|"):
        recipient, _, bps = part.rpartition(":")
        if recipient in NEAR_WALLETS:
            total += int(bps or 0)
    return total


def _total_bps(app_fees: str) -> int:
    if not isinstance(app_fees, str) or not app_fees:
        return 0
    return sum(int(p.rpartition(":")[2] or 0) for p in app_fees.split("|"))


def load(success_only: bool = True) -> pd.DataFrame:
    frames = [pd.read_csv(f, usecols=COLS, dtype=str) for f in sorted(glob.glob(str(DATA / "swaps_*.csv.gz")))]
    df = pd.concat(frames, ignore_index=True)
    # Window boundaries overlap and the API is not strictly time-ordered: deduplicate.
    df = df.drop_duplicates(["deposit_address", "deposit_memo", "created_at"])
    if success_only:
        df = df[df["status"] == "SUCCESS"]
    df["ts"] = pd.to_datetime(df["created_at"], utc=True, format="ISO8601")
    df["usd"] = pd.to_numeric(df["amount_in_usd"], errors="coerce").fillna(0.0)
    fees = df["app_fees"].fillna("")
    uniq = pd.Series(fees.unique())
    near_map = dict(zip(uniq, uniq.map(_near_bps)))
    tot_map = dict(zip(uniq, uniq.map(_total_bps)))
    df["near_bps"] = fees.map(near_map)
    df["total_bps"] = fees.map(tot_map)
    df["near_usd"] = df["usd"] * df["near_bps"] / 1e4
    df["fee_usd"] = df["usd"] * df["total_bps"] / 1e4
    df["zec"] = df["origin_asset"].str.contains("zec", na=False) | df["destination_asset"].str.contains("zec", na=False)
    df["ref"] = df["referral"].fillna("").replace("", "(none)")
    return df


def _concentration(g: pd.DataFrame, value: str) -> tuple[float, float]:
    shares = g.groupby("ref")[value].sum()
    shares = shares[shares.index != "(none)"]  # unattributed users are not one integrator
    total = g[value].sum()
    if total <= 0:
        return np.nan, np.nan
    s = shares / total
    return float(s.nlargest(3).sum()), float((s.pow(2).sum()) * 1e4)


def _summarise(g: pd.DataFrame) -> dict:
    vol = g["usd"].sum()
    top3_vol, hhi_vol = _concentration(g, "usd")
    top3_rev, hhi_rev = _concentration(g, "near_usd")
    days = g["ts"].dt.floor("D").nunique()
    return {
        "days": days,
        "swaps": len(g),
        "volume_usd_per_day": vol / days if days else np.nan,
        "near_usd_per_day": g["near_usd"].sum() / days if days else np.nan,
        "near_bps": g["near_usd"].sum() / vol * 1e4 if vol else np.nan,
        "fee_bps": g["fee_usd"].sum() / vol * 1e4 if vol else np.nan,
        "near_share_of_fees": g["near_usd"].sum() / g["fee_usd"].sum() if g["fee_usd"].sum() else np.nan,
        "zec_vol_share": g.loc[g["zec"], "usd"].sum() / vol if vol else np.nan,
        "zec_near_rev_share": g.loc[g["zec"], "near_usd"].sum() / g["near_usd"].sum() if g["near_usd"].sum() else np.nan,
        "noref_vol_share": g.loc[g["ref"] == "(none)", "usd"].sum() / vol if vol else np.nan,
        "noref_near_rev_share": g.loc[g["ref"] == "(none)", "near_usd"].sum() / g["near_usd"].sum() if g["near_usd"].sum() else np.nan,
        "swapkit_vol_share": g.loc[g["ref"].str.lower().str.contains("swapkit"), "usd"].sum() / vol if vol else np.nan,
        "top3_integrators_vol": top3_vol,
        "hhi_vol": hhi_vol,
        "top3_integrators_near_rev": top3_rev,
        "hhi_near_rev": hhi_rev,
        "senders_per_day": g.groupby(g["ts"].dt.floor("D"))["sender_hash"].nunique().mean(),
        "median_swap_usd": g["usd"].median(),
        "whale_vol_share": g.loc[g["usd"] >= 100_000, "usd"].sum() / vol if vol else np.nan,
    }


def _period(ts: pd.Series) -> pd.Series:
    """Sample weeks (days 8–14 of Feb–Jul) are labelled by month; the continuous window
    from 2026-08-15 is cut into 7-day bins starting on the 15th."""
    days = (ts - CONTINUOUS_START).dt.days
    cont = CONTINUOUS_START + pd.to_timedelta((days // 7) * 7, unit="D")
    sample = ts.dt.strftime("%Y-%m-08")
    label = np.where(ts >= CONTINUOUS_START, cont.dt.strftime("%Y-%m-%d"), sample)
    in_sample = (ts < CONTINUOUS_START) & ts.dt.day.between(8, 14)
    return pd.Series(np.where((ts >= CONTINUOUS_START) | in_sample, label, ""), index=ts.index)


def weekly(df: pd.DataFrame) -> pd.DataFrame:
    """One row per 7-day period: Feb–Jul sample weeks, then continuous weeks from Aug 15."""
    df = df.assign(period=_period(df["ts"]))
    rows = [{"period_start": k, **_summarise(g)} for k, g in df[df["period"] != ""].groupby("period")]
    out = pd.DataFrame(rows)
    return out[out["days"] >= 5]  # drop incomplete periods (July sample, last days of October)


def snapshot_windows(df: pd.DataFrame) -> pd.DataFrame:
    """Four-week windows either side of the snapshot, plus the latest two weeks."""
    windows = {
        "pre_4w (Aug 18–Sep 14)": ("2026-08-18", "2026-09-15"),
        "snapshot (Sep 15–17)": ("2026-09-15", "2026-09-18"),
        "post_4w (Sep 18–Oct 15)": ("2026-09-18", "2026-10-16"),
        "latest_2w (Oct 16–29)": ("2026-10-16", "2026-10-30"),
    }
    rows = []
    for name, (a, b) in windows.items():
        g = df[(df["ts"] >= pd.Timestamp(a, tz="UTC")) & (df["ts"] < pd.Timestamp(b, tz="UTC"))]
        rows.append({"window": name, **_summarise(g)})
    return pd.DataFrame(rows)


def _senders(df: pd.DataFrame) -> pd.DataFrame:
    s = df[["sender_hash", "ts", "usd"]].dropna(subset=["sender_hash"])
    return s[s["sender_hash"] != ""]


def snapshot_entrants(df: pd.DataFrame) -> pd.DataFrame:
    """Do senders who arrived just before the snapshot stay less than those who arrived after?

    Symmetric design: each cohort = senders active in a 14-day window and not active in the
    17 days before it; follow-up = a 14-day window starting 14 days after the cohort ends.
    Pre-snapshot cohort: Sep 1–14 (farming window). Placebo cohort: Sep 18–Oct 1.
    """
    s = _senders(df)
    t = lambda x: pd.Timestamp(x, tz="UTC")  # noqa: E731
    rows = []
    for name, a in (("arrived Sep 1–14 (pre-snapshot)", t("2026-09-01")),
                    ("arrived Sep 18–Oct 1 (placebo)", t("2026-09-18"))):
        b = a + pd.Timedelta(days=14)
        seen_before = set(s.loc[(s["ts"] >= a - pd.Timedelta(days=17)) & (s["ts"] < a), "sender_hash"])
        active = s[(s["ts"] >= a) & (s["ts"] < b)]
        cohort = set(active["sender_hash"]) - seen_before
        f0, f1 = b + pd.Timedelta(days=14), b + pd.Timedelta(days=28)
        follow = s[(s["ts"] >= f0) & (s["ts"] < f1) & s["sender_hash"].isin(cohort)]
        cohort_vol = active.loc[active["sender_hash"].isin(cohort), "usd"].sum()
        rows.append({
            "cohort": name,
            "new_senders": len(cohort),
            "new_senders_per_day": len(cohort) / 14,
            "retained_share": follow["sender_hash"].nunique() / len(cohort),
            "cohort_volume_usd": cohort_vol,
            "follow_volume_usd": follow["usd"].sum(),
            "volume_retained": follow["usd"].sum() / cohort_vol,
        })
    return pd.DataFrame(rows)


def retention(df: pd.DataFrame) -> pd.DataFrame:
    """H3.4 proxy. Cohort = senders active on days 8–14 of month M (Feb–Jul).

    - active_sample_week_M+k: also active on days 8–14 of month M+k (understates monthly retention);
    - active_in_aug15_oct29: active at any time in the continuous window (an upper bound on
      single-month retention for cohorts 2–5 months earlier).
    Sender = first address of the deposit, hashed: a user who comes back from another address
    or chain counts as new, so all figures are lower bounds on user retention.
    """
    s = _senders(df)
    s = s[s["ts"].dt.day.between(8, 14) | (s["ts"] >= CONTINUOUS_START)]
    wk = s[s["ts"].dt.day.between(8, 14)]
    months = [m for m in (2, 3, 4, 5, 6, 7, 9, 10)]  # no Aug 8–14 sample; July sample complete once collected
    by_month = {m: set(wk.loc[wk["ts"].dt.month == m, "sender_hash"]) for m in months}
    cont = set(s.loc[s["ts"] >= CONTINUOUS_START, "sender_hash"])
    rows = []
    for m in (2, 3, 4, 5, 6, 7):
        senders = by_month[m]
        if not senders:
            continue
        row = {"month": m, "senders_sample_week": len(senders),
               "active_in_aug15_oct29": len(senders & cont) / len(senders)}
        for k in (1, 3):
            row[f"active_sample_week_M+{k}"] = (len(senders & by_month[m + k]) / len(senders)
                                                if by_month.get(m + k) else np.nan)
        rows.append(row)
    return pd.DataFrame(rows)


def fee_shares(df: pd.DataFrame, days: int = 30) -> pd.DataFrame:
    """Last `days` days: each referral's share of volume, of all app fees and of NEAR's revenue.

    Feeds kill criterion 2 (top integrator > 60% of fees). Swaps without referral are one row,
    "(none)", but are not an integrator.
    """
    end = df["ts"].max()
    g = df[df["ts"] > end - pd.Timedelta(days=days)].groupby("ref")[["usd", "fee_usd", "near_usd"]].sum()
    out = pd.DataFrame({
        "volume_share": g["usd"] / g["usd"].sum(),
        "fee_share": g["fee_usd"] / g["fee_usd"].sum(),
        "near_revenue_share": g["near_usd"] / g["near_usd"].sum(),
    }).sort_values("fee_share", ascending=False)
    out.attrs["window"] = f"{(end - pd.Timedelta(days=days)).date()}..{end.date()}"
    return out


STABLES = {
    "nep141:eth-0xdac17f958d2ee523a2206206994597c13d831ec7.omft.near", "nep141:eth-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48.omft.near",
    "nep141:eth-0x6b175474e89094c44da98b954eedeac495271d0f.omft.near", "nep141:tron-d28a265909efecdcee7c5028585214ea0b96f015.omft.near",
    "nep141:base-0x833589fcd6edb6e08f4c7c32d4f71b54bda02913.omft.near", "nep141:sol-5ce3bf3a31af18be40ba30f721101b4341690186.omft.near",
    "nep141:sol-c800a4bd850783ccb82c2b2c7e84175443606352.omft.near", "nep141:arb-0xaf88d065e77c8cc2239327c5edb3a432268e5831.omft.near",
    "nep141:arb-0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9.omft.near", "nep141:usdt.tether-token.near",
    "nep141:17208628f84f5d6ad33f0da3bbbeb27ffcb398eac501a31bd6ad2011e36133a1",
}
MAJORS = {
    "nep141:eth.omft.near": "ETH", "nep141:base.omft.near": "ETH", "nep141:arb.omft.near": "ETH", "nep141:sol.omft.near": "SOL",
    "1cs_v1:btc:native:coin": "BTC", "nep141:nbtc.bridge.near": "BTC", "nep141:zec.omft.near": "ZEC", "nep141:ltc.omft.near": "LTC",
    "nep141:xrp.omft.near": "XRP", "nep141:doge.omft.near": "DOGE", "nep141:tron.omft.near": "TRX", "nep141:wrap.near": "NEAR",
    "nep141:sui.omft.near": "SUI", "nep141:cardano.omft.near": "ADA", "nep141:bch.omft.near": "BCH",
}


def _family(asset: str) -> str:
    if asset in STABLES:
        return "stable"
    return MAJORS.get(asset, "other")


def revenue_by_asset(df: pd.DataFrame, days: int = 30) -> pd.DataFrame:
    """Last `days` days: volume and NEAR's revenue by the non-stable asset of each swap.

    A swap is labelled by its non-stablecoin leg (BTC→USDT is "BTC"); stable→stable swaps are
    "stable↔stable"; when both legs are volatile, the origin asset is used.
    """
    end = df["ts"].max()
    d = df[df["ts"] > end - pd.Timedelta(days=days)]
    o, t = d["origin_asset"].map(_family), d["destination_asset"].map(_family)
    label = o.where(o != "stable", t).where(~((o == "stable") & (t == "stable")), "stable↔stable")
    g = d.assign(label=label).groupby("label")[["usd", "near_usd", "fee_usd"]].sum()
    out = pd.DataFrame({
        "volume_share": g["usd"] / g["usd"].sum(),
        "near_revenue_share": g["near_usd"] / g["near_usd"].sum(),
        "near_bps": g["near_usd"] / g["usd"] * 1e4,
        "all_fees_bps": g["fee_usd"] / g["usd"] * 1e4,
    }).sort_values("near_revenue_share", ascending=False)
    return out


def november(df: pd.DataFrame) -> dict:
    """What changed on 1Click between the second half of October and the first ten days of November.

    NEAR's take on 1Click by window, with and without Trust Wallet (whose 20 bps flow, mostly ZEC,
    surged on 23-28 Oct), the part of NEAR's 1Click revenue from swaps without an integrator
    (NEAR's own front-end and direct users), ZEC, and NEAR's share of the whole fee pool.
    """
    day = df["ts"].dt.tz_convert(None).dt.normalize()
    ref = df["referral"].fillna("").str.lower()
    trust = ref.str.startswith("trust")
    out = {}
    for name, a, b in (("oct16_29", "2026-10-16", "2026-10-29"), ("nov01_10", "2026-11-01", "2026-11-10")):
        m = (day >= a) & (day <= b)
        n = (pd.Timestamp(b) - pd.Timestamp(a)).days + 1
        s, x = df[m], df[m & ~trust]
        noref = s[ref[m] == ""]
        out[name] = {
            "days": n, "volume_usd_per_day": float(s["usd"].sum() / n), "near_usd_per_day": float(s["near_usd"].sum() / n),
            "near_bps": float(s["near_usd"].sum() / s["usd"].sum() * 1e4),
            "near_bps_ex_trust": float(x["near_usd"].sum() / x["usd"].sum() * 1e4),
            "trust_near_share": float(s.loc[trust[m], "near_usd"].sum() / s["near_usd"].sum()),
            "trust_volume_usd": float(s.loc[trust[m], "usd"].sum()),
            "noref_near_usd_per_day": float(noref["near_usd"].sum() / n), "noref_near_bps": float(noref["near_usd"].sum() / noref["usd"].sum() * 1e4),
            "noref_near_share": float(noref["near_usd"].sum() / s["near_usd"].sum()),
            "zec_volume_share": float(s.loc[s["zec"], "usd"].sum() / s["usd"].sum()),
            "zec_near_share": float(s.loc[s["zec"], "near_usd"].sum() / s["near_usd"].sum()),
            "near_share_of_fee_pool": float(s["near_usd"].sum() / s["fee_usd"].sum()),
        }
    burst = df[trust & (day >= "2026-10-23") & (day <= "2026-10-28")]
    out["trust_burst_oct23_28"] = {"volume_usd": float(burst["usd"].sum()), "near_usd": float(burst["near_usd"].sum()),
                                   "zec_share": float(burst.loc[burst["zec"], "usd"].sum() / burst["usd"].sum())}
    last30 = df[df["ts"] >= df["ts"].max() - pd.Timedelta(days=30)]
    out["last30"] = {"from": str(last30["ts"].min().date()), "to": str(df["ts"].max().date()),
                     "near_share_of_fee_pool": float(last30["near_usd"].sum() / last30["fee_usd"].sum()),
                     "swaps": int(len(last30)), "swaps_collected": int(len(df))}
    return out


def quality(df: pd.DataFrame, days: int = 30) -> dict:
    """Is the 1Click volume broad, or a few addresses trading with themselves? (last `days` days)

    Sender = hash of the first address of the deposit; one person can use several addresses, so
    concentration is a lower bound and the share of one-swap senders an upper bound.
    Round trip = a sender swaps asset family A into B, then B back into A within 24 hours.
    """
    g = df[df["ts"] >= df["ts"].max() - pd.Timedelta(days=days)]
    s = _senders(g).join(g[["near_usd", "origin_asset", "destination_asset", "ref"]])
    by = s.groupby("sender_hash").agg(n=("usd", "size"), usd=("usd", "sum"), near=("near_usd", "sum"))
    vol, rev = by["usd"].sum(), by["near"].sum()
    top = lambda col, k: float(by[col].nlargest(k).sum() / by[col].sum())  # noqa: E731
    s = s.assign(o=s["origin_asset"].map(_family), d=s["destination_asset"].map(_family)).sort_values("ts")
    rt = set()
    for _, grp in s[s["sender_hash"].isin(by.index[by["n"] >= 2])].groupby("sender_hash"):
        t, o, d, idx = grp["ts"].values, grp["o"].values, grp["d"].values, grp.index.values
        for i in range(len(grp)):
            j = i + 1
            while j < len(grp) and t[j] - t[i] <= np.timedelta64(24, "h"):
                if o[i] != d[i] and o[j] == d[i] and d[j] == o[i]:
                    rt.update((idx[i], idx[j]))
                    break
                j += 1
    r = s.loc[sorted(rt)]
    by_ref = (r.groupby("ref")["usd"].sum() / r["usd"].sum()).sort_values(ascending=False)
    heavy = by[by["n"] >= 100]
    return {
        "from": str(g["ts"].min().date()), "to": str(g["ts"].max().date()), "swaps": int(len(g)),
        "swaps_with_sender": float(len(s) / len(g)), "senders": int(len(by)), "one_swap_senders": float((by["n"] == 1).mean()),
        "top10_volume": top("usd", 10), "top100_volume": top("usd", 100), "top10_near_revenue": top("near", 10),
        "top100_near_revenue": top("near", 100), "hhi_volume": float(((by["usd"] / vol) ** 2).sum() * 1e4),
        "senders_100plus_swaps": int(len(heavy)), "senders_100plus_volume": float(heavy["usd"].sum() / vol),
        "senders_100plus_near_revenue": float(heavy["near"].sum() / rev),
        "round_trip_volume": float(r["usd"].sum() / s["usd"].sum()), "round_trip_near_revenue": float(r["near_usd"].sum() / s["near_usd"].sum()),
        "round_trip_top_integrator": [str(by_ref.index[0]), float(by_ref.iloc[0])] if len(by_ref) else None,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if not glob.glob(str(DATA / "swaps_*.csv.gz")):
        print(f"No per-swap 1Click data in {DATA}: it comes from the NEAR Intents Explorer API, which needs a partner key\n"
              "(INTENTS_JWT in a git-ignored .env), and it is not committed. Its aggregates are committed in data/processed/\n"
              "(swaps_weekly.csv, fee_shares_last30d.csv, oneclick_november.json, oneclick_quality.json, ...), and every\n"
              "document and check reads those. To rebuild them: put a key in .env, run `python3 -m src.ingest.intents_explorer`,\n"
              "then `make swaps`. Nothing to do here; exiting.")
        return
    df = load()
    print(f"{len(df):,} successful 1Click swaps, {df['ts'].min()} → {df['ts'].max()}")
    w = weekly(df)
    w.to_csv(OUT / "swaps_weekly.csv", index=False)
    snap = snapshot_windows(df)
    snap.to_csv(OUT / "snapshot_windows.csv", index=False)
    ret = retention(df)
    ret.to_csv(OUT / "retention.csv", index=False)
    fs = fee_shares(df)
    fs.head(25).to_csv(OUT / "fee_shares_last30d.csv")
    ra = revenue_by_asset(df)
    ra.to_csv(OUT / "revenue_by_asset_last30d.csv")
    print("NEAR revenue by asset, last 30 days"); print(ra.round(3).to_string())
    print("fee shares, last 30 days", fs.attrs["window"])
    print(fs.head(6).round(3).to_string())
    pd.set_option("display.width", 220, "display.max_columns", 30)
    cols = ["period_start", "volume_usd_per_day", "near_bps", "fee_bps", "near_share_of_fees", "zec_vol_share",
            "zec_near_rev_share", "noref_near_rev_share", "swapkit_vol_share", "top3_integrators_vol",
            "top3_integrators_near_rev", "hhi_near_rev", "senders_per_day"]
    print(w[cols].round(3).to_string(index=False))
    print(snap.drop(columns=["days"]).round(3).T.to_string())
    print(ret.round(3).to_string(index=False))
    nov = november(df)
    (OUT / "oneclick_november.json").write_text(json.dumps(nov, indent=1))
    print(json.dumps(nov, indent=1))
    q = quality(df)
    (OUT / "oneclick_quality.json").write_text(json.dumps(q, indent=1))
    print(json.dumps(q, indent=1))
    ent = snapshot_entrants(df)
    ent.to_csv(OUT / "snapshot_entrants.csv", index=False)
    print(ent.round(3).to_string(index=False))
    z = df[df["ts"] >= CONTINUOUS_START]
    print(f"ZEC share of 1Click volume since {CONTINUOUS_START.date()}: {z.loc[z['zec'], 'usd'].sum() / z['usd'].sum():.3f}")


if __name__ == "__main__":
    main()
