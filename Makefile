.PHONY: anchor-check bigquery reproduce refresh data ledger revenue supply swaps montecarlo backtest comps risk confidential dashboard dashboard-serve test all manifest check-clean governance governance-fetch predictions leadlag leadlag-fetch docs verify

data:        ## fetch DefiLlama, RPC, NearBlocks and price snapshots into data/raw/
	python3 -m src.ingest.sources

ledger:      ## first-pass reconciliation, buyback wallet only
	python3 -m src.analysis.ledger

revenue:     ## rebuild captured revenue from the 3 revenue wallets and reconcile with DefiLlama
	python3 -m src.analysis.revenue_wallets

supply:      ## measured issuance (archival RPC) vs NEAR captured
	python3 -m src.analysis.supply

swaps:       ## 1Click swap-level analysis: weekly take, ZEC, concentration, snapshot, retention (needs data/intents_v2)
	python3 -m src.analysis.swaps

montecarlo:  ## H5.1: Monte Carlo of NEAR captured vs issued to end-2027, scenarios + sensitivity table
	python3 -m src.analysis.montecarlo

backtest:    ## walk-forward check of the Monte Carlo engine (calibration of past forecasts)
	python3 -m src.analysis.backtest_mc

comps:       ## peers (market cap / holders revenue) and cross-chain swap market share; refreshes data/raw/comps
	python3 -m src.analysis.comps

risk:        ## holder's view: NEAR vs BTC risk, issuance, stake, buyback yield; refreshes BTC prices and stake
	python3 -m src.analysis.token_risk

confidential: ## confidential swaps from NEAR's Dune dashboard (data/raw/dune): volume share, take-rate regression, H4.1, incentive cost
	python3 -m src.analysis.confidential

official:    ## cross-check against NEAR's own dashboard (revenue.near.org snapshot in data/raw/near_revenue)
	python3 -m src.analysis.official

official-fetch: ## same, after fetching today's snapshot (network)
	python3 -m src.analysis.official --refresh

dashboard:   ## bundle committed outputs into dashboard/data.json
	python3 -m src.analysis.dashboard_data

dashboard-serve: ## open the dashboard at http://localhost:8000 (live figures load in the browser)
	cd dashboard && python3 -m http.server 8000

test:        ## model checks
	python3 -m pytest -q tests

reproduce:   ## every offline step on the committed snapshots, then the tests
	$(MAKE) ledger revenue supply governance montecarlo backtest leadlag bigquery confidential official dashboard test

refresh:     ## fetch fresh public snapshots (network), then re-run everything
	$(MAKE) data comps risk official-fetch governance-fetch leadlag-fetch manifest reproduce

manifest:    ## sha256 of every raw snapshot -> data/raw/MANIFEST.json
	python3 -m src.manifest

governance:  ## HSP-029 vote, timelock and earliest ramp start, from the vote.dao snapshot
	python3 -m src.analysis.governance

governance-fetch:
	python3 -m src.analysis.governance --refresh

anchor-check: ## read the hashes anchored on NEAR testnet and compare them with the files (needs network)
	python3 -m src.anchor_check

bigquery:    ## third-source check on NEAR's BigQuery dataset (queries in sql/, results in data/raw/bigquery/)
	python3 -m src.analysis.bigquery_check

leadlag:     ## the track's hypothesis: does usage (Intents volume, L1 activity) lead NEAR's price? Holm-corrected
	python3 -m src.analysis.leadlag

leadlag-fetch:
	python3 -m src.analysis.leadlag --refresh

predictions: ## resolve the frozen predictions whose date has passed -> predictions/RESULTS.md
	python3 -m src.predictions

docs:        ## render README.md, REPORT.md and FAQ.md from docs/templates/ with the figures in data/processed/
	python3 -m src.figures

verify:      ## re-check the headline findings and fail if a committed document has drifted from the data
	python3 -m src.figures --check

check-clean: ## rebuild from the committed snapshots and fail if any committed output changes
	$(MAKE) reproduce
	python3 -m src.check_outputs
	python3 -m src.figures --check

all: reproduce
