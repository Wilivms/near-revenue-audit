.PHONY: data ledger revenue supply swaps montecarlo backtest comps dashboard dashboard-serve test all

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

dashboard:   ## bundle committed outputs into dashboard/data.json
	python3 -m src.analysis.dashboard_data

dashboard-serve: ## open the dashboard at http://localhost:8000 (live figures load in the browser)
	cd dashboard && python3 -m http.server 8000

test:        ## model checks
	python3 -m pytest -q tests

all: data ledger revenue supply
