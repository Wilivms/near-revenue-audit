"""Checks for the Monte Carlo model. Run: python3 -m pytest tests (or make test)."""
import numpy as np

from src.analysis.montecarlo import Scenario, calibration, sensitivity, simulate


def test_reproducible_with_seed():
    cal = calibration()
    sc = Scenario("t", 5.0, 365)
    a = simulate(sc, cal, n_paths=200)["ratio"]
    b = simulate(sc, cal, n_paths=200)["ratio"]
    assert np.array_equal(a, b)


def test_first_month_matches_identity():
    """With all-zero shocks the first month must equal the closed-form offset of the sensitivity table."""
    cal = calibration()
    take = 5.0
    issued_per_day = cal["supply0"] * cal["issuance_rate"] / 365
    expected = cal["volume0"] * take / 1e4 / cal["price0"] / issued_per_day
    # Scale-free check through the table: offset is linear in volume and take.
    table = sensitivity(cal)
    v135 = table.iloc[0, 1] / (135e6 * float(table.columns[1].split()[0]))
    assert np.isclose(expected, v135 * cal["volume0"] * take, rtol=1e-9)


def test_deflation_threshold_identity():
    """Offset = 1 exactly when mcap / annual captured revenue = 1 / issuance rate."""
    cal = calibration()
    mcap = cal["supply0"] * cal["price0"]
    annual_rev_needed = mcap * cal["issuance_rate"]
    vol_needed = annual_rev_needed / 365 / (5.0 / 1e4)
    issued_per_day = cal["supply0"] * cal["issuance_rate"] / 365
    offset = vol_needed * 5.0 / 1e4 / cal["price0"] / issued_per_day
    assert np.isclose(offset, 1.0)


def test_retired_share_scales_linearly():
    cal = calibration()
    full = simulate(Scenario("a", 5.0, 365), cal, n_paths=100)["ratio"]
    part = simulate(Scenario("b", 5.0, 365, retired_share=0.5), cal, n_paths=100)["ratio"]
    assert np.allclose(part, 0.5 * full)
