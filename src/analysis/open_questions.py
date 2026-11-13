"""The two questions NEAR did not answer, and what the committed data says about each.

1. What does NEAR earn on a confidential swap? NEAR publishes no rate. The weekly fit on total revenue
   gives 11 bps in levels and 5.5 in first differences; NEAR's Dune fee table shows 7.4. Here the same
   fit is run per wallet: the buyback multisig and the front-end fund separately, Aug-Oct 2026, with a
   bootstrap, leave-one-week-out and first differences.
2. Why does NEAR's revenue series run above what its three revenue wallets receive? revenue.near.org
   splits its capture into three mechanisms (front-end fees, B2B partners, quote improvement) over four
   windows (7 days, 30 days, year to date, all time). Revenue in USD for each is the capture share times
   gross fees (its own fee series); it is compared with what the wallets received over the same window.

Inputs: confidential_weekly.csv, revenue_rebuilt_daily.csv, the latest data/raw/near_revenue snapshot.
Output: data/processed/open_questions.json
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from ..ingest.sources import RAW
from .ledger import OUT

WALLETS = {"buyback multisig": "rebuilt_buybacks_usd", "front-end fund": "rebuilt_fefundsadmin_usd"}


def _fit(df: pd.DataFrame, y: str) -> np.ndarray:
    a = df[["confidential_usd", "public_usd"]].to_numpy()
    return np.linalg.lstsq(a, df[y].to_numpy(), rcond=None)[0] * 1e4


def confidential_fee() -> dict:
    c = pd.read_csv(OUT / "confidential_weekly.csv", index_col=0, parse_dates=True).dropna()
    rng = np.random.default_rng(7)
    out = {"weeks": int(len(c)), "from": str(c.index.min().date()), "to": str(c.index.max().date())}
    for name, col in WALLETS.items():
        lv, fd = _fit(c, col), _fit(c.diff().dropna(), col)
        loo = [_fit(c.drop(i), col)[0] for i in c.index]
        boot = [_fit(c.iloc[rng.integers(0, len(c), len(c))], col)[0] for _ in range(2000)]
        out[name] = {"confidential_bps": float(lv[0]), "public_bps": float(lv[1]), "first_diff_confidential_bps": float(fd[0]),
                     "first_diff_public_bps": float(fd[1]), "loo_min": float(min(loo)), "loo_max": float(max(loo)),
                     "boot_p5": float(np.percentile(boot, 5)), "boot_p95": float(np.percentile(boot, 95)),
                     "corr_with_confidential": float(c[col].corr(c["confidential_usd"])), "corr_with_public": float(c[col].corr(c["public_usd"]))}
    return out


def revenue_gap() -> dict:
    snap = json.loads(sorted((RAW / "near_revenue").glob("*.json"))[-1].read_text())
    cb = snap["captureByMechanism"]
    fees = pd.DataFrame(snap["totalFeesSeries"]).assign(d=lambda x: pd.to_datetime(x["date_at"])).set_index("d")["fees_usd"]
    rev = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True)["rebuilt_total_usd"]
    end = min(fees.index.max(), rev.index.max() - pd.Timedelta(days=1))
    windows = {"d7": end - pd.Timedelta(days=6), "d30": end - pd.Timedelta(days=29), "ytd": pd.Timestamp(f"{end.year}-01-01"), "all_time": fees.index.min()}
    out = {"to": str(end.date())}
    for k, a in windows.items():
        f = float(fees.loc[a:end].sum())
        mech = {m: cb[f"pp_{m}_{k}"] * f for m in ("fe", "b2b", "qi")}
        total, wallets = sum(mech.values()), float(rev.loc[a:end].sum())
        out[k] = {"from": str(a.date()), "fees_usd": f, "front_end_usd": mech["fe"], "b2b_usd": mech["b2b"], "quote_improvement_usd": mech["qi"],
                  "reported_usd": total, "wallets_usd": wallets, "reported_over_wallets": total / wallets,
                  "without_quote_improvement_over_wallets": (total - mech["qi"]) / wallets, "quote_improvement_share_of_reported": mech["qi"] / total}
    return out


def main() -> None:
    out = {"confidential_fee": confidential_fee(), "revenue_gap": revenue_gap()}
    (OUT / "open_questions.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
