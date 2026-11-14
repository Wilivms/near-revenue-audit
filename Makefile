.PHONY: control control-fetch signers treasury elasticity elasticity-collect swap-cost swap-cost-collect implied robustness events incident incident-collect quotes quotes-fetch revisions open-questions oneclick-offline setup pycheck anchor-check bigquery reproduce refresh data ledger revenue supply swaps montecarlo backtest comps risk confidential dashboard dashboard-serve test all manifest check-clean governance governance-fetch predictions leadlag leadlag-fetch docs verify

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

comps:       ## peers (market cap / holders revenue) and cross-chain swap market share, from the committed snapshot (make refresh fetches a new one)
	python3 -m src.analysis.comps

risk:        ## holder's view: NEAR vs BTC risk, issuance, stake, buyback yield; refreshes BTC prices and stake
	python3 -m src.analysis.token_risk

confidential: ## confidential swaps from NEAR's Dune dashboard (data/raw/dune): volume share, take-rate regression, H4.1, incentive cost
	python3 -m src.analysis.confidential

incident:    ## the freeze and the exploit (29 Sep to 2 Oct): the halt, volume, NEAR's revenue and integrators, against a placebo month
	python3 -m src.analysis.incident

incident-collect: ## aggregates for `make incident` from the private per-swap 1Click data (needs make swaps-collect first)
	python3 -m src.analysis.incident --collect

swap-cost:   ## what a 1Click swap costs the user, split between integrators, NEAR and solvers/networks
	python3 -m src.analysis.swap_cost

swap-cost-collect: ## daily sums for `make swap-cost` from the private per-swap 1Click data
	python3 -m src.analysis.swap_cost --collect

signers:     ## who signs NEAR's transactions: human-scale signers against bots, and the lead-lag test on them
	python3 -m src.analysis.signers

control:     ## rule or choice: who controls each revenue wallet, with how many signatures, and every payment out
	python3 -m src.analysis.control

control-fetch: ## public view calls on NEAR mainnet (no key): multisig threshold, DAO policies and proposals, intents.near fee
	python3 -m src.analysis.control --fetch

treasury:    ## the protocol treasury's 30M NEAR in 2026, followed hop by hop: sold or staked?
	python3 -m src.analysis.treasury

elasticity:  ## do 1Click volumes react to fees? integrators' fee steps and fee levels against their volume
	python3 -m src.analysis.elasticity

elasticity-collect: ## daily integrator fees for `make elasticity` from the private per-swap 1Click data
	python3 -m src.analysis.elasticity --collect

implied:     ## reverse valuation: the revenue and growth NEAR's market cap implies
	python3 -m src.analysis.implied

robustness:  ## each finding recomputed under the alternatives a careful reader would try; fragile ones are named
	python3 -m src.analysis.robustness

events:      ## seven NEAR events tested the same way (volume, revenue, take, share, price vs BTC) against a placebo distribution
	python3 -m src.analysis.events

quotes:      ## quote race offline: 1Click against Relay, Across and LI.FI on the same swaps (data/raw/quotes)
	python3 -m src.analysis.quotes

quotes-fetch: ## one live quote round (network, about a minute, no key, nothing sent)
	python3 -m src.ingest.quotes

revisions:   ## do the sources revise past days? every dated snapshot of DefiLlama, NEAR's dashboard and the wallet rebuild, compared
	python3 -m src.analysis.revisions

official:    ## cross-check against NEAR's own dashboard (revenue.near.org snapshot in data/raw/near_revenue)
	python3 -m src.analysis.official

official-fetch: ## same, after fetching today's snapshot (network)
	python3 -m src.analysis.official --refresh

dashboard:   ## bundle committed outputs into dashboard/data.json
	python3 -m src.analysis.dashboard_data

dashboard-serve: ## open the dashboard at http://localhost:8000 (live figures load in the browser)
	cd dashboard && python3 -m http.server 8000

setup:       ## create .venv with Python 3.12+ and the pinned dependencies (uses uv if python3 is older)
	bash scripts/setup.sh

pycheck:
	@python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else "Python 3.12 or later is needed (pandas 3, numpy 2.5): run  make setup  then  . .venv/bin/activate")'

test:        ## model checks
	python3 -m pytest -q tests

STEPS = ledger revenue supply governance montecarlo backtest leadlag bigquery oneclick-offline confidential official revisions quotes incident events swap-cost elasticity signers treasury control implied robustness open-questions predictions dashboard

reproduce:   ## every offline step on the committed snapshots, then the tests
	$(MAKE) $(STEPS) test

refresh:     ## fetch fresh public snapshots (network), re-run everything, re-render the documents, then the tests
	REFRESH=1 $(MAKE) data supply comps risk official-fetch governance-fetch leadlag-fetch quotes-fetch control-fetch manifest $(STEPS) docs test

manifest:    ## sha256 of every raw snapshot -> data/raw/MANIFEST.json
	python3 -m src.manifest

governance:  ## HSP-029 vote, timelock and earliest ramp start, from the vote.dao snapshot
	python3 -m src.analysis.governance

governance-fetch:
	python3 -m src.analysis.governance --refresh

anchor-check: ## read the hashes anchored on NEAR testnet and compare them with the files (needs network)
	python3 -m src.anchor_check

open-questions: ## the two questions NEAR did not answer: the confidential fee per wallet, and what the revenue-series gap is made of
	python3 -m src.analysis.open_questions

oneclick-offline: ## recompute the 1Click tables from the published daily aggregates, no partner key needed
	python3 -m src.analysis.oneclick_offline

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

check-clean: pycheck ## rebuild from the committed snapshots and fail if any committed output changes
	python3 -m src.check_outputs --snapshot
	$(MAKE) reproduce
	python3 -m src.check_outputs
	python3 -m src.figures --check

all: reproduce
