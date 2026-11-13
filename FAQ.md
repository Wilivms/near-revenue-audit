<!-- Generated from docs/templates/FAQ.md by `make docs`; edit the template, not this file. -->
# Reviewer FAQ

Short answers to the questions a judge (human or AI) is likely to ask. Each points to the code or log entry that backs it.

**What is the thesis, in one line?**
NEAR's protocol revenue is real (it reaches NEAR's wallets: 0.9% gap with DefiLlama, 0.14% with NEAR's own dashboard). It more than doubled as a share of volume from September, led by confidential swaps that grew under an airdrop campaign (NEAR@3.33), and it has eased since. And at today's market cap it buys back only about a sixth of new NEAR, so it does not yet support the token. See [`REPORT.md`](REPORT.md).

**NEAR now has its own revenue dashboard. Why does this project still matter?**
Because it answers different questions. revenue.near.org reports revenue, buybacks and the share of emissions offset, and this audit agrees with it (wallets within 0.14%, log 29). It does not say who pays the revenue, what the growth cost, whether it holds, or what it implies for the token's value. Those are this thesis: integrator and asset concentration on 1Click, the NEAR@3.33 cost against its uplift, a failed out-of-sample week, and the 41x / 64x break-even identity against a 217x market. The README table "What this adds to NEAR's own dashboard" lists it side by side.

**Is this a bull or a bear case?**
Neither by design. Hypotheses and kill criteria were written before the analysis ([`HYPOTHESES.md`](HYPOTHESES.md), untouched since). Results that went against expectations are reported as written, in both directions. H4.1, a bearish expectation (confidential TVL would leave after the airdrop snapshot), was rejected: TVL doubled. Kill criterion 2 (one integrator above 60% of fees) triggered on 1Click data. The weekly fit missed its first unseen week. Conviction is "Medium-low" on durability (REPORT, "Conviction and limits").

**How do I check a number myself?**
`make reproduce` runs every offline step from committed snapshots and ends with the tests passing. The "do X → see Y" table in the [README](README.md) maps each headline to a command. The dashboard recomputes its headline figures and two kill criteria live from DefiLlama and the NEAR RPC on every visit.

**Where does "revenue" come from? Isn't it just DefiLlama's number?**
No. `src/analysis/revenue_wallets.py` rebuilds it from the inflows of three NEAR revenue wallets (NearBlocks), priced at the daily close: $7.94M rebuilt vs $8.01M reported since the 2026-02-23 fee switch. Each complete month is within ±5% (log 2). NEAR later published its own revenue dashboard: it names the same three wallets, and the NEAR they received agrees with this rebuild within 0.14% (`make official`, log 29). One gap is open: NEAR's monthly revenue series is about 21% above what those wallets receive, every month. The audit counts only what reaches the wallets (log 32).

**Why do you say growth is "bought"?**
- NEAR's take went from 2.2 bps of volume in August to 5.5 in October while volume did not rise in proportion.
- A weekly regression on NEAR's own Dune data gives captured revenue ≈ 1.0 bps × public volume + 11.0 bps × confidential volume over Aug–Oct (13 weeks). R² is 0.85; the 90% bootstrap interval for the confidential term is 9.7–13.4 bps (`src/analysis/confidential.py`). On week-to-week changes the same fit gives 5.5 bps (2.2–9.0), so the premium is real but its size is uncertain.
- Confidential volume took off after the launch of NEAR@3.33, a campaign that pays NEAR to users who park and trade through confidential intents.
- Its first drop cost about $1.39M. At the May–Aug take rate, Sep–Oct revenue would have been about $1.87M lower (log 25).

So the first drop cost about three quarters of the uplift. "Bought" is the reading the timing supports; the data cannot prove the campaign caused the growth, and the report says "partly".

**Did the fit hold after October?**
No, and the log says so (entry 30). For the week of 2 November it predicted $901k of revenue ($475k with the fit on weekly changes); NEAR captured $355k. From 3 November NEAR's Dune dataset labels almost all volume confidential while public 1Click swaps continue, so the label changed and the confidential share can no longer be tracked. The take on all volume fell to 3.9 bps (5.5 in October) as confidential TVL fell 25% from its peak; DefiLlama and NEAR's own revenue series show the same fall. The fit is reported for Aug–Oct only.

**The 11.0 bps fit is above the 7.4 bps fee Dune shows for confidential swaps. Which is right?**
Probably neither exactly, and the log says so (entries 26, 32). The regression is a revenue *attribution*: in levels it can absorb a shared trend and correlated flows. On week-to-week changes it gives 5.5 bps (2.2–9.0), which contains Dune's 7.4. The conclusion that survives every version: confidential swaps pay NEAR more than public ones, and they explain a part of the jump, from 22% to 84%. The open question has been asked to the NEAR Intents team.

**Other entries report a lower offset (about 11%). Why the difference?**
Definitions. This audit counts all NEAR captured by the three revenue wallets NEAR lists (buyback multisig, front-end fund, 1Click fund): 14.8% of issuance over Feb–Oct, 16.3% on NEAR's own count. Counting only NEAR actually bought into the buyback multisig, over a recent 30 days, gives a lower figure, which is what some entries report. Both read the same chain; neither changes the conclusion that buybacks offset a small fraction of issuance. REPORT section 9 checks the "permanently remove" claim: nothing is burned, and part of the captured NEAR sits in a treasury with no commitment not to sell.

**Is the volume real, or a few addresses trading with themselves?**
Real and broad, on 1Click where it can be measured (REPORT section 3, log 36). Over the last 30 days: 231k sending addresses, 78% swapping once, the top 10 at 19% of volume. Round trips (A to B and back within a day by the same address) are 2.7% of volume and 1.1% of NEAR's revenue. Confidential swaps cannot be checked this way: the Explorer API does not show them.

**Why should I trust a Monte Carlo on a token this volatile?**
You shouldn't trust it blindly. The point is the identity, not the forecast: supply stops growing only when market cap is below 41x annual captured revenue (64x once the issuance cut approved on 2 November is phased in), and today it is 217x.

The simulation draws volume and price together in 30-day blocks (joint block bootstrap). A walk-forward backtest (`make backtest`) shows the engine was biased *upward* in 2026, so the base case (17% of 2027 issuance offset) is if anything optimistic. Eleven scenarios are shown, including "the incentive winds down over 6 months" (10%) and the approved issuance cut (18%).

**How do I know the numbers in these documents match the code?**
README.md, REPORT.md and this file are rendered from templates in `docs/templates/` by `make docs`, with every figure filled in from `data/processed/`. `make verify` renders them again, fails if a committed document differs, and re-checks the 13 findings in the README. `make check-clean` rebuilds every output from the committed snapshots and compares it with the committed one.

**Did you test the track's suggested hypothesis?**
Yes (REPORT section 8, `make leadlag`). Weekly, NEAR's price net of BTC, Intents volume and L1 activity, lags of one to four weeks, both directions: 0 of 24 tests are significant after Holm's correction. Week to week, revenue moves with both Intents volume and L1 transactions; over a year only Intents volume grew with it. Nothing here leads the price.

**Can I hold you to anything?**
Six dated predictions, frozen on 2026-11-11 with a committed sha256 and a Bitcoin timestamp (`predictions/`). Two resolve on 2026-11-15, before judging starts.

**Is the private 1Click data in the repo?**
No. Per-swap data from the NEAR Intents Explorer API needs a partner key and is git-ignored; only aggregates are committed (`data/processed/`). No sender is identified; addresses are hashed.

**Why was Dune read through a browser?**
Dune's API needs a paid plan. The result tables of NEAR's public dashboard were read page by page and saved as text in `data/raw/dune/`, with each query id in the file header, so anyone can compare them with the source.

**What was added after the fact?**
The criterion "incentive activity fades" (now on confidential TVL, since the volume label changed) is marked "added after the fact" on the dashboard and in the log. It is reported separately from the pre-registered criteria. The wind-down scenario and the confidential-channel analysis were also added after the Dune data came in; the log dates each change.

**What NEAR features does this use?**
NEAR Intents (`intents.near` contract views, fee and fee collector, 1Click and confidential channels), the NEAR RPC and archival RPC (total supply, validators, contract state), and NEAR's revenue wallets on-chain.

**Is this investment advice?**
No. It is independent research, not affiliated with NEAR Foundation.
