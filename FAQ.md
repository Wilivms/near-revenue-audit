# Reviewer FAQ

Short answers to the questions a judge (human or AI) is likely to ask. Each points to the code or log entry that backs it.

**What is the thesis, in one line?**
NEAR's protocol revenue is real (it reaches NEAR's wallets: 0.1% gap with DefiLlama). It is growing, but the September doubling is mostly confidential swaps that an airdrop campaign (NEAR@3.33) is paying for. And at today's market cap it buys back only about a fifth of new NEAR, so it does not yet support the token. See [`REPORT.md`](REPORT.md).

**Is this a bull or a bear case?**
Neither by design. Hypotheses and kill criteria were written before the analysis ([`HYPOTHESES.md`](HYPOTHESES.md), untouched since). Two came out against the bull case: H4.1 (confidential TVL leaves after the snapshot) was rejected, and kill criterion 2 triggered on 1Click data. Both are reported as written. Conviction is "Medium-low" on durability (REPORT, "Conviction and limits").

**How do I check a number myself?**
`make reproduce` runs every offline step from committed snapshots and ends with the tests passing. The "do X → see Y" table in the [README](README.md) maps each headline to a command. The dashboard recomputes its headline figures and two kill criteria live from DefiLlama and the NEAR RPC on every visit.

**Where does "revenue" come from? Isn't it just DefiLlama's number?**
No. `src/analysis/revenue_wallets.py` rebuilds it from the inflows of three NEAR revenue wallets (NearBlocks), priced at the daily close: $7.287M rebuilt vs $7.295M reported since the 2026-02-23 fee switch. Each month is within ±5% (log 2).

**Why do you say growth is "bought"?**
- The take rate went from about 2.4 to 5.4 bps of volume in September while volume did not change much.
- A weekly regression on NEAR's own Dune data gives captured revenue ≈ 0.65 bps × public volume + 12.2 bps × confidential volume. R² is 0.86; the 90% bootstrap interval for the confidential term is 10.8–14.5 bps (`src/analysis/confidential.py`).
- Confidential volume took off after NEAR@3.33, a campaign that pays NEAR to users who park and trade through confidential intents.
- Its first drop cost about $1.39M. At the May–Aug take rate, Sep–Oct revenue would have been about $1.72M lower (log 25).

So most of the uplift is roughly what the incentive cost.

**The 12 bps fit is above the 7.4 bps fee Dune shows for confidential swaps. Which is right?**
This is the main open question, and the log says so (entry 26). The regression is a revenue *attribution*: it can absorb correlated flows, such as fees from public swaps that the same users make. Dune's fee table is all-time and may count a different fee base. Either value leaves the conclusion unchanged: confidential volume explains the jump. The open question has been asked to the NEAR Intents team.

**Why should I trust a Monte Carlo on a token this volatile?**
You shouldn't trust it blindly. The point is the identity, not the forecast: supply stops growing only when market cap is below about 41 × annual captured revenue, and today it is about 200×.

The simulation draws volume and price together in 30-day blocks (joint block bootstrap). A walk-forward backtest (`make backtest`) shows the engine was biased *upward* in 2026, so the base case (21% of 2027 issuance offset) is if anything optimistic. Nine scenarios are shown, including "the incentive winds down over 6 months" (11% offset).

**Is the private 1Click data in the repo?**
No. Per-swap data from the NEAR Intents Explorer API needs a partner key and is git-ignored; only aggregates are committed (`data/processed/`). No sender is identified; addresses are hashed.

**Why was Dune read through a browser?**
Dune's API needs a paid plan. The result tables of NEAR's public dashboard were read page by page and saved as text in `data/raw/dune/`, with each query id in the file header, so anyone can compare them with the source.

**What was added after the fact?**
The criterion "incentive volume fades" is marked "added after the fact" on the dashboard and in the log. It is reported separately from the pre-registered criteria. The wind-down scenario and the confidential-channel analysis were also added after the Dune data came in; the log dates each change.

**What NEAR features does this use?**
NEAR Intents (`intents.near` contract views, fee and fee collector, 1Click and confidential channels), the NEAR RPC and archival RPC (total supply, validators, contract state), and NEAR's revenue wallets on-chain.

**Is this investment advice?**
No. It is independent research, not affiliated with NEAR Foundation.
