"""Whole-project checks: the documents say what the data says, the README promises what runs,
the public-claims ledger is well formed, the anchors are consistent and nothing secret is committed.

All offline: they read committed files only.
"""
import json
import re
import subprocess
from pathlib import Path

import pandas as pd
import pytest

from src import figures
from src.figures import OUT, ROOT

DOCS = ["README.md", "REPORT.md", "FAQ.md", "THESIS.md"]


@pytest.fixture(scope="module")
def rendered():
    return figures.render()


@pytest.mark.parametrize("name", DOCS)
def test_committed_document_is_the_rendered_one(rendered, name):
    assert (ROOT / name).read_text() == rendered[name], f"{name} is stale: run `make docs`"


@pytest.mark.parametrize("name", DOCS)
def test_no_unfilled_placeholder(rendered, name):
    assert not re.search(r"\{\{\w+\}\}", rendered[name])


FINDINGS = {r["id"]: r for r in figures.claims()}


def test_there_are_fourteen_findings_or_more():
    assert len(FINDINGS) >= 14


@pytest.mark.parametrize("fid", sorted(FINDINGS, key=lambda x: int(x[1:])))
def test_finding_holds(fid):
    r = FINDINGS[fid]
    assert r["passed"], f"{fid} no longer holds: {r['finding']}: {r['number']}"


def test_finding_ids_unique_and_commands_exist():
    rows = figures.claims()
    assert len({r["id"] for r in rows}) == len(rows)
    targets = set(re.findall(r"^([a-z][\w-]*):", (ROOT / "Makefile").read_text(), re.M))
    for r in rows:
        assert r["command"].split()[1] in targets, r["command"]


def test_readme_make_commands_exist():
    targets = set(re.findall(r"^([a-z][\w-]*):", (ROOT / "Makefile").read_text(), re.M))
    used = set(re.findall(r"`make ([a-z][\w-]*)`", (ROOT / "README.md").read_text()))
    assert used and used <= targets, used - targets


def test_public_claims_ledger_is_well_formed():
    rows = figures.public_claims()
    assert len(rows) >= 25
    prefixes = ("Survives", "Close", "Overstated", "Inflated", "Not shown", "Unverified", "Fees survive", "Intents yes", "The exception")
    for r in rows:
        assert all(r[k].strip() for k in ("claim", "source", "data", "verdict")), r
        assert r["verdict"].startswith(prefixes), r["verdict"]
        assert r["source"] != "same"
        for url in re.findall(r"\]\((https?://[^)]+)\)", r["source"]):
            assert url.startswith("https://"), url


def test_public_claims_counts_add_up(rendered):
    rows = figures.public_claims()
    m = re.search(r"(\d+) claims by NEAR, Nansen, analysts and the press tested at their own dates: (\d+) survive, (\d+) are close, (\d+) do not hold", rendered["README.md"])
    assert m and int(m.group(1)) == len(rows) == sum(int(m.group(i)) for i in (2, 3, 4))


def test_bigquery_agrees_with_pipeline_sources():
    bq = json.loads((OUT / "bigquery_crosscheck.json").read_text())
    for month, (a, b) in bq["revenue"]["monthly"].items():
        assert abs(a - b) <= 1e-6 * max(1.0, b), month
    assert abs(bq["supply"]["issued_gap"]) < 5e-3
    assert bq["activity"]["txns_ratio_min"] == bq["activity"]["txns_ratio_max"] == 1.0


def test_revenue_rebuild_monthly_within_five_percent():
    r = pd.read_csv(OUT / "revenue_rebuilt_daily.csv", index_col=0, parse_dates=True).loc[figures.FEE_SWITCH:]
    m = r.resample("MS").sum()
    m = m[(m.index >= "2026-03-01") & (m.index < r.index.max().replace(day=1))]  # complete months
    ratio = m["rebuilt_total_usd"] / m["llama_holders_revenue_usd"]
    assert ratio.between(0.95, 1.05).all(), ratio.round(3).to_dict()


def test_anchor_log_is_consistent():
    log = ROOT / "anchor" / "anchors.jsonl"
    rows = [json.loads(x) for x in log.read_text().splitlines() if x.strip()]
    kinds = {r["kind"] for r in rows}
    assert {"predictions", "snapshot", "daily"} <= kinds
    for r in rows:
        assert re.fullmatch(r"[0-9a-f]{64}", r["sha256"]) and r["account"] == "near-revenue-audit.testnet"
    pred = [r for r in rows if r["kind"] == "predictions"][-1]
    assert pred["sha256"] == (ROOT / "predictions" / "PREDICTIONS.sha256").read_text().strip()


def test_dashboard_bundle_has_what_the_page_reads():
    d = json.loads((ROOT / "dashboard" / "data.json").read_text())
    c = d["checks"]
    assert {"findings", "public_claims", "predictions", "leadlag", "anchors"} <= set(c)
    assert len(c["public_claims"]) == len(figures.public_claims())
    html = (ROOT / "dashboard" / "index.html").read_text()
    for el in ("tbChecks", "tbPublic", "tbPred", "tbAnchors", "leadlagSub"):
        assert f'id="{el}"' in html


def test_dashboard_loads_no_insecure_resource():
    html = (ROOT / "dashboard" / "index.html").read_text()
    assert not re.search(r"""(src|href)=["']http://""", html)


def test_swaps_explains_missing_private_data(tmp_path, monkeypatch, capsys):
    from src.analysis import swaps
    monkeypatch.setattr(swaps, "DATA", tmp_path)
    swaps.main()
    assert "partner key" in capsys.readouterr().out


def test_no_secret_is_committed():
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    assert ".env" not in files
    # the values in the local .env (testnet key, Explorer API key), plus any JWT or key assignment
    env = ROOT / ".env"
    secrets = [v.strip() for v in re.findall(r"^\w+=(.+)$", env.read_text(), re.M)] if env.exists() else []
    pattern = re.compile("|".join([r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.", r"(INTENTS_JWT|NEAR_TESTNET_KEY)=[^\s<]{20,}"] + [re.escape(x) for x in secrets if len(x) > 20]))
    for f in files:
        p = ROOT / f
        if p.suffix in {".png", ".jpg", ".gz", ".ots", ".mp4", ".mp3"} or not p.is_file() or p.stat().st_size > 5_000_000:
            continue
        text = p.read_text(errors="ignore")
        assert not pattern.search(text), f
