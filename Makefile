.PHONY: data ledger all

data:
	python3 -m src.ingest.sources

ledger:
	python3 -m src.analysis.ledger

all: data ledger
