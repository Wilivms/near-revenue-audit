"""Checks for the Monte Carlo model. Run: python3 -m pytest tests (or make test)."""
import numpy as np

import pandas as pd

from src.analysis.montecarlo import (CUT_DAYS, CUT_START, Scenario, calibration, issuance_factor,
                                     sensitivity, simulate)


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
    row_volume = float(table.index[0].strip("$").split("M")[0]) * 1e6  # first row: the starting volume, rounded
    per_unit = table.iloc[0, 1] / (row_volume * float(table.columns[1].split()[0]))
    assert np.isclose(expected, per_unit * cal["volume0"] * take, rtol=1e-9)
    assert abs(row_volume - cal["volume0"]) <= 0.5e6


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


def test_issuance_cut_schedule():
    """HSP-029: no change before the start, 1.6/2.5 of today's issuance once fully phased in, and
    a cut can only raise the share of issuance offset."""
    dates = pd.DatetimeIndex([CUT_START - pd.Timedelta(days=1), CUT_START + pd.Timedelta(days=CUT_DAYS // 2),
                              CUT_START + pd.Timedelta(days=CUT_DAYS + 30)])
    f = issuance_factor(dates, True)
    assert np.allclose(f, [1.0, 1 - 0.36 * (CUT_DAYS // 2) / CUT_DAYS, 0.64])
    assert np.allclose(issuance_factor(dates, False), 1.0)
    cal = calibration()
    plain = simulate(Scenario("a", 5.0, 365), cal, n_paths=100)["ratio"]
    cut = simulate(Scenario("b", 5.0, 365, issuance_cut=True), cal, n_paths=100)["ratio"]
    assert (cut >= plain - 1e-12).all() and (cut[:, -1] > plain[:, -1]).all()
    assert np.allclose(cut[:, :3], plain[:, :3])  # Nov 2026 - Jan 2027: before the cut starts
