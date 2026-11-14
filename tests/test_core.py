"""Unit tests for the code behind the headline numbers, on small hand-made fixtures.

`make check-clean` catches drift in the outputs; these catch logic errors that would reproduce
consistently: what counts as revenue, what does not, and how a swap's fee is split.
"""
import pandas as pd
import pytest

from src.analysis import oneclick_offline, revenue_wallets as rw, swaps

BB, FE, OC = "buybacks.multisignature.near", "fefundsadmin.sputnik-dao.near", "1csfundsadmin.sputnik-dao.near"
DAY = 1_780_000_000 * 10**9  # a block timestamp in ns


def _tx(rid, sender, receiver, near, ok=True, ts=DAY):
    return {"receipt_id": rid, "predecessor_account_id": sender, "receiver_account_id": receiver, "block_timestamp": ts,
            "outcomes": {"status": ok}, "actions": [{"action": "TRANSFER", "deposit": near * 10**24}]}


@pytest.fixture
def wallets(monkeypatch):
    native = {
        "wallet_buybacks_txns": [
            _tx("a", "solver.near", BB, 100),        # external inflow: revenue
            _tx("a", "solver.near", BB, 100),        # same receipt listed twice: counted once
            _tx("b", "solver.near", BB, 50, ok=False),  # failed receipt: no money moved
            _tx("c", "system", BB, 7),               # gas refund from `system`: not revenue
            _tx("d", FE, BB, 30),                    # internal hop between revenue wallets: not revenue
            _tx("e", BB, "staking.near", 20),        # outflow
        ],
        "wallet_fefundsadmin_txns": [_tx("f", "user.near", FE, 10), _tx("d", FE, BB, 30)],
        "wallet_1csfundsadmin_txns": [],
    }
    ft = {
        "wallet_buybacks_ft": [
            {"block_timestamp": DAY, "delta_amount": str(5 * 10**24), "involved_account_id": "intents.near", "ft": {"decimals": 24, "symbol": "wNEAR"}},
            {"block_timestamp": DAY, "delta_amount": str(3 * 10**6), "involved_account_id": "intents.near", "ft": {"decimals": 6, "symbol": "USDC"}},
            {"block_timestamp": DAY, "delta_amount": "0", "involved_account_id": "x", "ft": {"decimals": 6, "symbol": "USDC"}},
        ],
        "wallet_fefundsadmin_ft": [], "wallet_1csfundsadmin_ft": [],
    }
    monkeypatch.setattr(rw, "_latest", lambda source: {**native, **ft}[source])
    price = pd.Series({pd.Timestamp(DAY, unit="ns").normalize(): 2.0})
    monkeypatch.setattr(rw, "near_price", lambda: price)
    return price


def test_native_flows_count_each_receipt_once_and_skip_failed_and_system(wallets):
    f = rw.native_flows(BB)
    ins = f[f.dir == "in"]
    assert sorted(ins.amount) == pytest.approx([30, 100])  # 100 once, the internal 30 still listed (filtered later), no 50, no 7
    assert f[f.dir == "out"].amount.tolist() == pytest.approx([20])


def test_ft_flows_apply_decimals_and_drop_zero_moves(wallets):
    f = rw.ft_flows(BB)
    assert dict(zip(f.token, f.amount)) == pytest.approx({"wNEAR": 5.0, "USDC": 3.0})


def test_revenue_counts_external_near_only(wallets, monkeypatch, tmp_path):
    monkeypatch.setattr(rw, "OUT", tmp_path)
    monkeypatch.setattr(rw, "llama_daily", lambda source, name: pd.Series(dtype=float, name=name))
    out = rw.rebuild_revenue(rw.all_flows())
    row = out.iloc[0]
    # buyback wallet: 100 NEAR + 5 wNEAR from outside (the 30 from the front-end fund is internal, USDC is not NEAR)
    assert row["rebuilt_buybacks_usd"] == pytest.approx(105 * 2.0)
    assert row["rebuilt_fefundsadmin_usd"] == pytest.approx(10 * 2.0)
    assert row["rebuilt_total_usd"] == pytest.approx(115 * 2.0)


def test_swap_fee_split_between_near_and_integrators():
    fees = f"{BB}:5|trust-wallet.near:80|{FE}:2"
    assert swaps._near_bps(fees) == 7
    assert swaps._total_bps(fees) == 87
    assert swaps._near_bps("") == swaps._near_bps(None) == 0


def test_fee_shares_last_window():
    ts = pd.to_datetime(["2026-11-01", "2026-11-02", "2026-09-01"], utc=True)
    df = pd.DataFrame({"ts": ts, "ref": ["a", "(none)", "a"], "usd": [100.0, 100.0, 1e9],
                       "fee_usd": [0.8, 0.05, 1e6], "near_usd": [0.05, 0.05, 1e6]})
    out = swaps.fee_shares(df, days=30)  # the September swap is outside the window
    assert out.loc["a", "fee_share"] == pytest.approx(0.8 / 0.85)
    assert out.loc["(none)", "near_revenue_share"] == pytest.approx(0.5)


@pytest.mark.filterwarnings("ignore::RuntimeWarning")  # route types absent from the toy table divide by zero
def test_offline_1click_recompute_on_a_toy_table():
    rows = []
    for day in ("2026-10-15", "2026-10-16", "2026-11-01"):
        rows.append({"day": day, "ref": "trust", "same_family": False, "near_tier": "1", "zec": False,
                     "swaps": 10, "volume_usd": 1000.0, "fee_usd": 9.0, "near_usd": 0.1})
        rows.append({"day": day, "ref": "(none)", "same_family": False, "near_tier": "20+", "zec": True,
                     "swaps": 2, "volume_usd": 100.0, "fee_usd": 0.2, "near_usd": 0.2})
    d = pd.DataFrame(rows)
    d["trust"] = d["ref"].str.startswith("trust")
    r = oneclick_offline.recompute(d)
    # first day dropped as partial: two days of 9.2 fees, 0.3 to NEAR
    assert r["integrators_keep_of_fee_pool"] == pytest.approx(1 - 0.6 / 18.4)
    assert r["top_integrator"] == "trust"
    assert r["no_integrator_near_share"] == pytest.approx(0.4 / 0.6)
    assert r["oct16_29"]["near_bps_ex_trust"] == pytest.approx(0.2 / 100 * 1e4)


def test_revisions_compare_by_age():
    from src.analysis import revisions
    d = lambda s: pd.Timestamp(s)  # noqa: E731
    snaps = {
        "2026-11-04": pd.Series({d("2026-11-01"): 100.0, d("2026-11-02"): 100.0, d("2026-11-03"): 10.0, d("2026-11-04"): 1.0}),
        "2026-11-10": pd.Series({d("2026-11-01"): 100.0, d("2026-11-02"): 100.0, d("2026-11-03"): 80.0, d("2026-11-04"): 90.0}),
    }
    r = revisions.compare(snaps)
    assert r["pairs"] == 3  # the snapshot's own (partial) day is not compared
    assert r["by_age"]["1"]["moved_1pct"] == 1 and r["by_age"]["3"]["moved_1pct"] == 0
    assert r["settled_after_days"] == 2
    assert r["largest"][0]["factor"] == 8.0
