"""Checks that must fail: a planted false finding, and a tampered output are caught.

A test suite that only ever passes proves little. These feed the same checks with wrong inputs and require a
FAIL or a reported difference, so a green run means the checks can see an error of that size.
"""
from __future__ import annotations

import json

from src import check_outputs, figures


def test_planted_false_revenue_finding_fails():
    v = dict(figures.values())
    v["rev_ratio"] = 1.05  # a planted error: revenue 5% off DefiLlama
    f1 = next(r for r in figures.claims(v) if r["id"] == "F1")
    assert not f1["passed"]


def test_planted_false_wallet_finding_fails():
    v = dict(figures.values())
    v["wallets_gap"] = 0.02  # NEAR's dashboard 2% away from the wallets
    f2 = next(r for r in figures.claims(v) if r["id"] == "F2")
    assert not f2["passed"]


def test_tampered_number_in_an_output_is_caught():
    path = figures.OUT / "control.json"
    real = json.loads(path.read_text())
    fake = json.loads(path.read_text())
    fake["multisig"]["balance_near"] *= 1 + 1e-6  # one part in a million
    assert check_outputs._diff_json(real, fake)
    assert not check_outputs._diff_json(real, json.loads(path.read_text()))


def test_tampered_csv_is_caught():
    raw = (figures.OUT / "supply_monthly.csv").read_bytes()
    lines = raw.decode().splitlines()
    head, first = lines[0], lines[1].split(",")
    first[1] = str(float(first[1]) * 1.000001)
    fake = "\n".join([head, ",".join(first), *lines[2:]]).encode()
    assert check_outputs._diff_csv(raw, fake)
