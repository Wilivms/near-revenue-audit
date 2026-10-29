.PHONY: data ledger revenue supply all

data:        ## fetch DefiLlama, RPC, NearBlocks and price snapshots into data/raw/
	python3 -m src.ingest.sources

ledger:      ## first-pass reconciliation, buyback wallet only
	python3 -m src.analysis.ledger

revenue:     ## rebuild captured revenue from the 3 revenue wallets and reconcile with DefiLlama
	python3 -m src.analysis.revenue_wallets

supply:      ## measured issuance (archival RPC) vs NEAR captured
	python3 -m src.analysis.supply

all: data ledger revenue supply
