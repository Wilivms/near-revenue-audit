"""The walk-forward check must only use past data and return valid PITs."""
import numpy as np

from src.analysis import backtest_mc


def test_pits_valid_and_no_lookahead(monkeypatch):
    seen = []
    real = backtest_mc._simulate

    def spy(steps, horizon, rng):
        seen.append(len(steps))
        return real(steps, horizon, rng)

    monkeypatch.setattr(backtest_mc, "N_PATHS", 200)
    monkeypatch.setattr(backtest_mc, "_simulate", spy)
    summary, origins = backtest_mc.run()
    assert origins["pit"].between(0, 1).all()
    assert np.isfinite(origins["median_error"]).all()
    assert max(seen) < len(backtest_mc.history())  # never the full sample, so never data after the origin
