# Reviewer FAQ

Short answers to the questions a judge (human or AI) is likely to ask. Each points to the code or log entry that backs it.

**What is the thesis, in one line?**
NEAR's protocol revenue is real (it reaches NEAR's wallets: {{rev_gap}} gap with DefiLlama, {{wallets_gap}} with NEAR's own dashboard). It more than doubled as a share of volume from September, led by confidential swaps that grew under an airdrop campaign (NEAR@3.33), and it has eased since. And at today's market cap it buys back only about a sixth of new NEAR, so it does not yet support the token. See [`REPORT.md`](REPORT.md).

**NEAR now has its own revenue dashboard. Why does this project still matter?**
Because it answers different questions. revenue.near.org reports revenue, buybacks and the share of emissions offset, and this audit agrees with it (wallets within {{wallets_gap}}, log 29). It does not say who pays the revenue, what the growth cost, whether it holds, or what it implies for the token's value. Those are this thesis: integrator and asset concentration on 1Click, the NEAR@3.33 cost against its uplift, a failed out-of-sample week, and the {{breakeven_now}} / {{breakeven_cut}} break-even identity against a {{near_captured_mult}} market. The README table "What this adds to NEAR's own dashboard" lists it side by side.

**Is this a bull or a bear case?**
Neither by design. Hypotheses and kill criteria were written before the analysis ([`HYPOTHESES.md`](HYPOTHESES.md), untouched since). Results that went against expectations are reported as written, in both directions. H4.1, a bearish expectation (confidential TVL would leave after the airdrop snapshot), was rejected: TVL doubled. Kill criterion 2 (one integrator above 60% of fees) triggered on 1Click data. The weekly fit missed its first unseen week. Conviction is "Medium-low" on durability (REPORT, "Conviction and limits").

**How do I check a number myself?**
`make reproduce` runs every offline step from committed snapshots and ends with the tests passing. The "do X → see Y" table in the [README](README.md) maps each headline to a command. The dashboard recomputes its headline figures and two kill criteria live from DefiLlama and the NEAR RPC on every visit. Without installing anything, the dashboard's "Verify it in your browser" button reads the manifest hash anchored on NEAR testnet, hashes the raw wallet files against it, rebuilds the NEAR received by the three revenue wallets from the raw receipts and compares it with the pipeline (same to the last digit) and with NEAR's own dashboard.

**Where does "revenue" come from? Isn't it just DefiLlama's number?**
No. `src/analysis/revenue_wallets.py` rebuilds it from the inflows of three NEAR revenue wallets (NearBlocks), priced at the daily close: {{rev_rebuilt}} rebuilt vs {{rev_llama}} reported since the 2026-02-23 fee switch. Each complete month is within ±5% (log 2). NEAR later published its own revenue dashboard: it names the same three wallets, and the NEAR they received agrees with this rebuild within {{wallets_gap}} (`make official`, log 29). One gap is open: NEAR's monthly revenue series is about {{series_over_wallets}} above what those wallets receive, every month. The audit counts only what reaches the wallets (log 32).

**Why do you say growth is "bought"?**
- NEAR's take went from {{take_aug}} bps of volume in August to {{take_oct}} in October while volume did not rise in proportion.
- A weekly regression on NEAR's own Dune data gives captured revenue ≈ {{fit_pub}} bps × public volume + {{fit_conf}} bps × confidential volume over Aug–Oct ({{fit_weeks}} weeks). R² is {{fit_r2}}; the 90% bootstrap interval for the confidential term is {{fit_ci}} bps (`src/analysis/confidential.py`). On week-to-week changes the same fit gives {{fd_conf}} bps ({{fd_ci}}), so the premium is real but its size is uncertain.
- Confidential volume took off after the launch of NEAR@3.33, a campaign that pays NEAR to users who park and trade through confidential intents.
- Its first drop cost about {{drop1_usd}}. At the May–Aug take rate, Sep–Oct revenue would have been about {{uplift}} lower (log 25).

So the first drop cost about three quarters of the uplift. "Bought" is the reading the timing supports; the data cannot prove the campaign caused the growth, and the report says "partly".

**Did the fit hold after October?**
No, and the log says so (entry 30). For the week of 2 November it predicted {{oos_pred}} of revenue ({{oos_pred_fd}} with the fit on weekly changes); NEAR captured {{oos_actual}}. From 3 November NEAR's Dune dataset labels almost all volume confidential while public 1Click swaps continue, so the label changed and the confidential share can no longer be tracked. The take on all volume fell to {{take_last_week}} bps ({{take_oct}} in October) as confidential TVL fell {{tvl_from_peak}} from its peak; DefiLlama and NEAR's own revenue series show the same fall. The fit is reported for Aug–Oct only.

**The {{fit_conf}} bps fit is above the {{dune_fee_bps}} bps fee Dune shows for confidential swaps. Which is right?**
Probably neither exactly, and the log says so (entries 26, 32). The regression is a revenue *attribution*: in levels it can absorb a shared trend and correlated flows. On week-to-week changes it gives {{fd_conf}} bps ({{fd_ci}}), which contains Dune's {{dune_fee_bps}}. The conclusion that survives every version: confidential swaps pay NEAR more than public ones, and they explain a part of the jump, from {{jump_fd}} to {{jump_levels}}. Run per wallet (REPORT section 10, log 42), the fit resolves most of the difference: the buyback multisig takes {{oq_bb_conf}} bps of confidential volume (interval {{oq_bb_band}}), close to Dune's {{dune_fee_bps}}, while the front-end fund's apparent share ({{oq_fe_conf}} bps) vanishes on week-to-week changes ({{oq_fe_fd}}): it was a shared trend. Our working answer is therefore about {{oq_bb_conf}} bps; NEAR has not confirmed it.

**I see several offsets and take rates. Which number is which?**
They measure different windows, and each is labelled where it appears:
- **Share of issuance bought back:** {{offset_rebuilt}} over Feb–Oct 2026 on the three wallets (the headline, finding F3); {{offset_official}} on NEAR's own count over the same months; about a fifth over the last 30 days on the dashboard's live reading, recomputed on each visit.
- **NEAR's take, bps of Intents volume:** {{take_aug}} in August and {{take_oct}} in October (monthly, finding F5); {{take_last_week}} in the week of 2 November; the simulator starts from the last 30 days; the 2027 model uses {{take_now}}, its rounded starting point.
- **Market cap against captured revenue:** {{near_captured_mult}} on the last 30 days annualised; break-even is {{breakeven_now}}.

**Other entries report a lower offset (about 11%). Why the difference?**
Definitions. This audit counts all NEAR captured by the three revenue wallets NEAR lists (buyback multisig, front-end fund, 1Click fund): {{offset_rebuilt}} of issuance over Feb–Oct, {{offset_official}} on NEAR's own count. Counting only NEAR actually bought into the buyback multisig, over a recent 30 days, gives a lower figure, which is what some entries report. Both read the same chain; neither changes the conclusion that buybacks offset a small fraction of issuance. REPORT section 9 checks the "permanently remove" claim: nothing is burned, and part of the captured NEAR sits in a treasury with no commitment not to sell.

**Aggregators revise recent days. Can a number here change after the fact?**
Not the revenue. Every refresh keeps a dated snapshot of each source, and `make revisions` (finding F16) compares them day by day: the revenue rebuilt from the wallets, run on each of {{rv_rb_snaps}} snapshots from {{rv_first}} to {{rv_last}}, changed on {{rv_rb_moved}} of {{rv_rb_pairs}} complete days, because a settled receipt does not change. DefiLlama's gross fees are first published for a partial day and raised later, up to {{rv_fee_factor}} ({{rv_fee_day}}: {{rv_fee_first}} → {{rv_fee_latest}}); NEAR's own dashboard shows the same jumps, so its 7-day share of fees captured reads high on the day it is published. Fees settle after {{rv_fee_settle}} days, so the one figure here that uses them (the fees line of "Follow $100") stops at the last settled day.

**Did the October exploit hurt the business?**
Not its users or NEAR's revenue, but its large integrators. The swaps show no 1Click swap from {{ic_from}} to {{ic_to}} UTC on 1 October ({{ic_hours}} hours), about {{ic_rev_lost}} of NEAR revenue. Against {{ic_pn}} placebo dates, sending addresses ({{ic_d_senders_change}}) and NEAR's 1Click revenue ({{ic_d_near_usd_change}}) stayed within their usual range in the two weeks after, while the 25 largest integrators' volume fell {{ic_top_vol}}, more than at any placebo date; {{ic_back}} of the {{ic_cut}} that cut back had returned by November (REPORT section 3, F17).

**Which NEAR events actually moved anything?**
`make events` tests seven (the issuance halving, the fee switch, two Confidential Intents launches, the NEAR@3.33 snapshot, the exploit, HSP-029) the same way, against a placebo distribution. The airdrop snapshot is the only one that moved both revenue ({{ev_snap_rev}}) and price ({{ev_snap_px3}} against Bitcoin in three days); the supply cuts did not lift the price (REPORT section 11).

**What does a swap cost the user, and how much of it reaches NEAR?**
On 1Click, about {{sc_cost}} bps of what a user sends is gone on delivery ({{sc_swaps}} swaps, {{sc_from}} to {{sc_to}}): {{sc_int}} bps to integrators, {{sc_near}} to NEAR and {{sc_rest}} to solvers and networks, so NEAR keeps {{sc_near_share}} of the user's cost (F18). Swaps under $10 cost about {{sc_small}} bps, mostly fixed network costs; from $3k to $100k the cost is flat at {{sc_flat_lo}}–{{sc_flat_hi}} bps; above $100k it rises again and NEAR's slice shrinks (README, Follow $100).

**What revenue does NEAR's price imply?**
Run backwards (REPORT section 4): at a 15% discount rate and 3% growth, {{im_mid}}x today's captured revenue, about {{im_mid_vol}} a day of Intents volume at today's take; or {{im_g5}} a year of growth for five years before trading at the peer multiple ({{im_peer}}). It values revenue as if paid to holders, which favours the price.

**Will competing bridges compete NEAR's take away?**
Not on prices so far. `make quotes` compares what 1Click, Relay, Across and LI.FI pay for the same swap asked within the same minute: over {{qr_rounds}} rounds, 1Click paid the most in {{qr_best_share}} of {{qr_swaps}} swaps, median {{qr_median}} from the best alternative, fees included; it leads on native BTC ({{qr_c_btc}}) and trails on Ethereum to L2 ({{qr_c_l1l2}}) and Solana ({{qr_c_sol}}). The pressure on NEAR's take comes from integrators, who keep most of the fee pool, more than from rival routers (REPORT section 6).

**Is the volume real, or a few addresses trading with themselves?**
Real and broad, on 1Click where it can be measured (REPORT section 3, log 36). Over the last 30 days: {{q_senders}} sending addresses, {{q_one_swap}} swapping once, the top 10 at {{q_top10}} of volume. Round trips (A to B and back within a day by the same address) are {{q_rt_vol}} of volume and {{q_rt_rev}} of NEAR's revenue. Confidential swaps cannot be checked this way: the Explorer API does not show them.

**Did NEAR Intents usage jump in November?**
Not in any sense that pays NEAR. Comparing 20–31 October with 1–12 November in NEAR's BigQuery dataset, transactions to `intents.near` changed {{bq_is_tx}}, but {{bq_is_self_inc}} of the increase is `intents.near` signing its own transactions ({{bq_is_self_nov}} of all of them in November). Transactions from other accounts changed {{bq_is_others}} and the number of those accounts {{bq_is_other_signers}}. NEAR's captured revenue over the same days changed {{bq_is_rev}}. (`make bigquery`; query in `sql/intents_signers.sql`)

**Confidential swaps run in a private shard. Does that hide NEAR's revenue from this audit?**
No. What the private shard hides is the individual swap; the fee still reaches NEAR as NEAR or wNEAR arriving in its three revenue wallets on mainnet, which is what this audit rebuilds. Those inflows continue through {{data_to}} and still match NEAR's own dashboard within {{wallets_gap}}. Per-swap analysis is where confidential flow is out of sight, which is why the confidential fee is estimated from the wallets (REPORT section 10) and not from swaps.

**Why should I trust a Monte Carlo on a token this volatile?**
You shouldn't trust it blindly. The point is the identity, not the forecast: supply stops growing only when market cap is below {{breakeven_now}} annual captured revenue ({{breakeven_cut}} once the issuance cut approved on 2 November is phased in), and today it is {{near_captured_mult}}.

The simulation draws volume and price together in 30-day blocks (joint block bootstrap). A walk-forward backtest (`make backtest`) shows the engine was biased *upward* in 2026, so the base case ({{mc_base}} of 2027 issuance offset) is if anything optimistic. Eleven scenarios are shown, including "the incentive winds down over 6 months" ({{mc_wind}}) and the approved issuance cut ({{mc_cut}}).

**How do I know the numbers in these documents match the code?**
README.md, REPORT.md and this file are rendered from templates in `docs/templates/` by `make docs`, with every figure filled in from `data/processed/`. `make verify` renders them again, fails if a committed document differs, and re-checks the 13 findings in the README. `make check-clean` rebuilds every output from the committed snapshots and compares it with the committed one.

**Did you test the track's suggested hypothesis?**
Yes (REPORT section 8, `make leadlag`). Weekly, NEAR's price net of BTC, Intents volume and L1 activity, lags of one to four weeks, both directions: {{ll_sig}} of {{ll_tests}} tests are significant after Holm's correction. Week to week, revenue moves with both Intents volume and L1 transactions; over a year only Intents volume grew with it. Nothing here leads the price.

**Can I hold you to anything?**
Six dated predictions, frozen on 2026-11-11 with a committed sha256 and a Bitcoin timestamp (`predictions/`). Two resolve on 2026-11-15, before judging starts.

**Can I check the 1Click findings without a partner key?**
Yes, the figures the documents quote. The per-swap data from the NEAR Intents Explorer API needs a partner key and its terms do not allow archiving or redistributing it, so it is not committed. Committed instead: `data/processed/oneclick_daily.csv`, daily sums by integrator, route type, NEAR fee tier and ZEC flag (no swap, sender or address). `make oneclick-offline` recomputes from it the integrators' share of the fee pool, each integrator's share of app fees and of NEAR's revenue, the November take with and without Trust Wallet, and the fee-schedule test, and checks them against the published outputs (finding F15). Two kinds of result need the swaps themselves: sender concentration and round trips (`oneclick_quality.json`), and retention across sample weeks. For those, a partner key is free at partners.near-intents.org and `python3 -m src.ingest.intents_explorer` then `make swaps` rebuild everything. The 1Click take also has public cross-checks: NEAR's dashboard reports capture by B2B partners, and the revenue wallets are on chain.

**Why was Dune read through a browser?**
Dune's API needs a paid plan. The result tables of NEAR's public dashboard were read page by page and saved as text in `data/raw/dune/`, with each query id in the file header, so anyone can compare them with the source.

**What was added after the fact?**
The criterion "incentive activity fades" (now on confidential TVL, since the volume label changed) is marked "added after the fact" on the dashboard and in the log. It is reported separately from the pre-registered criteria. The wind-down scenario and the confidential-channel analysis were also added after the Dune data came in; the log dates each change.

**What NEAR features does this use?**
NEAR Intents (`intents.near` contract views, fee and fee collector, 1Click and confidential channels), the NEAR RPC and archival RPC (total supply, validators, contract state), and NEAR's revenue wallets on-chain.

**Are you saying the revenue DAOs misuse funds?**
No. Multisigs and DAOs are a normal way to run a treasury, and the payments listed have plausible ordinary reasons: the front-end fund's {{ct_fe_stable}} to `aurora…` accounts would fit payments to an operating partner of the front-end (and part predates the buybacks), and the 1Click fund's {{ct_oc_implicit}} NEAR of "fees accrued by mistake" would fit a refund. The point is narrower: none of the NEAR bought back is burned or locked, and {{ct_one_signer}} of it is in a fund whose policy one Admin vote can change. A holder relies on a policy, not a rule. Every payment, with its transaction, is in [REPORT's appendix](REPORT.md#appendix-every-payment-from-the-two-revenue-daos).

**Is this investment advice?**
No. It is independent research, not affiliated with NEAR Foundation.
