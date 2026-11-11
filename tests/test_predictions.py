"""The frozen predictions file has not been edited, and the resolver decides them as written."""
import hashlib

import pandas as pd

from src.predictions import PRED, _check, resolve


def test_predictions_unchanged_since_frozen():
    recorded = (PRED.parent / "PREDICTIONS.sha256").read_text().strip()
    assert hashlib.sha256(PRED.read_bytes()).hexdigest() == recorded


def test_resolver_rules():
    assert _check(3.9, "<", "5.0") and not _check(5.1, "<", "5.0")
    assert _check("Approved", "in", "Approved|Executed") and not _check("Rejected", "in", "Approved|Executed")
    r = resolve(pd.Timestamp("2026-11-12"))  # before every resolution date
    assert set(r.status) == {"pending"}
