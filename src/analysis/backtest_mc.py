"""Walk-forward check of the Monte Carlo engine: would it have been calibrated in the past?

At each origin date t, the block bootstrap is calibrated only on daily changes observed before t
(no look-ahead), simulates the next H days, and we record where the realised outcome fell in
the simulated distribution (its PIT, probability integral transform).

Target: the log change of "buyback capacity" = 7-day Intents volume / NEAR price, i.e. how many NEAR
one unit of take rate buys. With a fixed take rate, buybacks per issued NEAR move one-for-one with it.

A calibrated forecast has PIT roughly uniform: about 80% of outcomes inside its 10th–90th band,
mean PIT near 0.5. Forecasts from origins less than H days apart overlap, so the effective number
of independent checks is about (span / H), small. Read the result as a sanity check, not a test.

Output: data/processed/montecarlo_backtest.csv (one row per window x horizon x price-drift setting)
and montecarlo_backtest_origins.csv (one row per origin).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .ledger import OUT
from .montecarlo import BLOCK, history

N_PATHS = 2_000
STEP_DAYS = 7
MIN_HISTORY = 120


def _simulate(steps: np.ndarray, horizon: int, rng: np.random.Generator) -> np.ndarray:
    """Cumulative log change over `horizon` days, joint block bootstrap of (dlog_vol, dlog_price)."""
    n_blocks = -(-horizon // BLOCK)
    block = min(BLOCK, len(steps) - 1)
    starts = rng.integers(0, len(steps) - block, size=(N_PATHS, n_blocks))
    idx = (starts[:, :, None] + np.arange(block)).reshape(N_PATHS, -1)[:, :horizon]
    draws = steps[idx]
    return draws.sum(axis=1)  # (paths, 2)


def run(seed: int = 7) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    h = history()
    steps_all = h[["dlog_vol", "dlog_price"]].to_numpy()
    log_cap = np.log(h["volume_7d"].to_numpy()) - np.log(h["near_usd"].to_numpy())
    rows = []
    windows = {"expanding (all history)": None, "rolling 365 days": 365, "rolling 180 days": 180}
    for horizon in (30, 90):
        for t in range(MIN_HISTORY, len(h) - horizon, STEP_DAYS):
            realised = log_cap[t + horizon] - log_cap[t]
            for wname, w in windows.items():
                past = steps_all[: t] if w is None else steps_all[max(0, t - w): t]
                if len(past) < MIN_HISTORY:
                    continue
                for demean in (False, True):
                    s = past.copy()
                    if demean:
                        s[:, 1] -= s[:, 1].mean()  # base case of the forecast: no price drift
                    sim = _simulate(s, horizon, rng)
                    cap = sim[:, 0] - sim[:, 1]
                    rows.append({
                        "origin": h.index[t].date(), "horizon_days": horizon, "window": wname,
                        "price_drift": "removed" if demean else "kept",
                        "pit": float((cap <= realised).mean()),
                        "median_error": float(realised - np.median(cap)),
                        "band_width": float(np.quantile(cap, 0.9) - np.quantile(cap, 0.1)),
                    })
    origins = pd.DataFrame(rows)
    g = origins.groupby(["window", "horizon_days", "price_drift"])
    summary = g.agg(
        origins=("pit", "size"),
        first_origin=("origin", "min"),
        last_origin=("origin", "max"),
        coverage_10_90=("pit", lambda p: float(((p >= 0.1) & (p <= 0.9)).mean())),
        below_p10=("pit", lambda p: float((p < 0.1).mean())),
        above_p90=("pit", lambda p: float((p > 0.9).mean())),
        mean_pit=("pit", "mean"),
        median_error_log=("median_error", "median"),
        band_width_log=("band_width", "median"),
    ).reset_index()
    return summary, origins


def main() -> None:
    summary, origins = run()
    OUT.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUT / "montecarlo_backtest.csv", index=False)
    origins.to_csv(OUT / "montecarlo_backtest_origins.csv", index=False)
    pd.set_option("display.width", 220, "display.max_columns", 20)
    print(summary.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
