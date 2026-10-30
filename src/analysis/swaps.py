"""Swap-level analysis of 1Click data (collector v2, data/intents_v2).

Covers what the Intents Explorer API can see: 1Click swaps only (~28% of Intents volume),
no confidential swaps. Every result below is about the 1Click channel.

Outputs (data/processed/):
- swaps_weekly.csv     one row per 7-day period (Feb–Jul sample weeks, then weekly from Aug 15): volume, NEAR's bps, ZEC share, mix, concentration
- snapshot_windows.csv before / after the NEAR@3.33 snapshot (2026-09-15/17)
- retention.csv        sender retention between sample weeks and into the continuous window
- fee_shares_last30d.csv each referral's share of volume, app fees and NEAR revenue (last 30 days)
- snapshot_entrants.csv retention of senders who arrived just before the snapshot vs a placebo cohort
"""
from __future__ import annotations

import glob

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


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
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
    print("fee shares, last 30 days", fs.attrs["window"])
    print(fs.head(6).round(3).to_string())
    pd.set_option("display.width", 220, "display.max_columns", 30)
    cols = ["period_start", "volume_usd_per_day", "near_bps", "fee_bps", "near_share_of_fees", "zec_vol_share",
            "zec_near_rev_share", "noref_near_rev_share", "swapkit_vol_share", "top3_integrators_vol",
            "top3_integrators_near_rev", "hhi_near_rev", "senders_per_day"]
    print(w[cols].round(3).to_string(index=False))
    print(snap.drop(columns=["days"]).round(3).T.to_string())
    print(ret.round(3).to_string(index=False))
    ent = snapshot_entrants(df)
    ent.to_csv(OUT / "snapshot_entrants.csv", index=False)
    print(ent.round(3).to_string(index=False))
    z = df[df["ts"] >= CONTINUOUS_START]
    print(f"ZEC share of 1Click volume since {CONTINUOUS_START.date()}: {z.loc[z['zec'], 'usd'].sum() / z['usd'].sum():.3f}")


if __name__ == "__main__":
    main()
