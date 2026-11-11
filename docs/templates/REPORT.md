# NEAR Revenue Audit: the thesis

*Data to {{data_to}} (first draft 2026-10-30). Every figure in this file is rendered from `data/processed/` by `make docs`. Live figures: [near-revenue-audit.vercel.app](https://near-revenue-audit.vercel.app). Working notes, dead ends and corrections: [`RESEARCH_LOG.md`](RESEARCH_LOG.md). Hypotheses, written before the tests: [`HYPOTHESES.md`](HYPOTHESES.md). Not investment advice.*

## The question

NEAR Intents now earns protocol revenue, and since 2026-02-23 that revenue buys NEAR. The public story is that this will make NEAR scarce. We asked three things:

1. Is the revenue **real**: does what is reported actually reach NEAR's wallets?
2. Is it **durable**: who pays it, how concentrated is it, and does it depend on incentives?
3. Does it **matter for the token**: does it offset the NEAR that is issued every day, now or by end-2027?

## The answer in five lines

- **Real.** Rebuilt from the chain, captured revenue matches DefiLlama within {{rev_gap}} ({{rev_rebuilt}} since the fee switch), and NEAR's own revenue dashboard, published after this rebuild, agrees within {{wallets_gap}} on the NEAR received by the three wallets. Almost nothing has left the wallets ({{near_out_all}} NEAR, {{near_out_share}} of what they received, traced to corrections returned to the bridge operator).
- **Growing, but partly bought.** NEAR's cut of volume more than doubled between August and October ({{take_aug}} to {{take_oct}} bps). The largest identified driver is **confidential swaps**, which went from {{conf_share_aug}} of Intents volume to {{conf_share_oct}} and pay NEAR more than public swaps: about {{premium_range}} bps against {{public_range}}, depending on the method. That surge coincides with an airdrop campaign (NEAR@3.33) that rewards confidential balances and swaps; the timing fits, but the data cannot prove the campaign caused it. Its first drop cost about {{drop1_usd}} in NEAR, a third to a half of the revenue the channel brought. In the first full week of November, with confidential TVL {{tvl_from_peak}} below its peak, the take fell back to {{take_last_week}} bps.
- **Not owned.** On 1Click, integrators keep about {{oc_integrators_keep}} of the fee pool. The largest one (SwapKit, {{sk_vol}} of volume, {{sk_fees}} of app fees) pays NEAR {{sk_near}} of its revenue. {{noref_near}} of NEAR's 1Click revenue comes from users without an integrator.
- **Too small for the supply story.** Buybacks offset about **one sixth** of issuance: {{offset_per100}} NEAR bought back for every 100 issued since February on this audit's count, {{offset_per100_official}} on NEAR's own. Market cap is **{{near_captured_mult}}** annual captured revenue; break-even needs **{{breakeven_now}}**, or **{{breakeven_cut}}** once the issuance cut approved on 2 November is fully phased in.
- **Still true at end-2027 in the base case.** In 10,000 simulated paths, buybacks offset a median {{mc_base}} of 2027 issuance ({{mc_cut}} with the issuance cut); there is a {{mc_base_p}} chance that 2027 is net deflationary ({{mc_cut_p}} with the cut). Break-even needs about {{be_vol_now}} of daily volume at today's take, against about {{volume0}} now.

## Evidence

### 1. The revenue is real

| Check | Result | Where |
| --- | --- | --- |
| Reported revenue reaches NEAR's wallets | {{rev_rebuilt_exact}} rebuilt from NearBlocks vs {{rev_llama_exact}} on DefiLlama (ratio {{rev_ratio}}, 2026-02-23 to {{rev_end}}); each complete month within {{rev_month_band}} | log 2, `make revenue` |
| Scope | Three wallets, not one: buyback multisig ({{share_buyback_wallet}}), front-end fund ({{share_fefunds}}), 1Click fund ({{share_1cs}}) | log 2 |
| NEAR's own dashboard agrees | All-time NEAR received by the same three wallets: {{wallets_rebuilt}} rebuilt vs {{wallets_official}} on revenue.near.org ({{wallets_gap}} apart) | log 29, `make official` |
| Bought NEAR stays put | {{near_out_all}} NEAR ({{near_out_share}} of all NEAR received) left; both outflows forwarded to `bridge-mng.near` the same day, one DAO proposal titled "Fees accrued by mistake" | log 3, 9 |
| Executed at market | Front-end fund conversions: +0.04% vs market, volume-weighted | log 4 |

Two caveats. First, NEAR's dashboard also publishes a monthly revenue series, and it runs about **{{series_over_wallets}} above** the NEAR that reaches the three wallets it lists (ratio {{series_ratio_min}} to {{series_ratio_max}} each month since July; {{series_over_wallets}} more in dollars over March–October). The ratio is stable, so trends agree, but where the difference goes is not visible on-chain from these wallets; the question has been put to NEAR (log 32). This audit counts only what reaches the wallets.

Second, the reading of "buyback". The front-end fund holds about {{fefunds_near}} NEAR ({{fefunds_share}} of all NEAR captured to date). It is a Sputnik DAO run by accounts that appear to belong to Aurora's finance team. It has not sold, but nothing on-chain commits it not to, and it paid four 50,000 USDC invoices from revenue. **Bought is not retired.**

### 2. The revenue grew, with confidential swaps as the largest identified driver, under an incentive

Source: NEAR's own Dune dashboard (@near, "NEAR Intents"), read from its public result tables (log 24).

| | Aug 2026 | Sep 2026 | Oct 2026 |
| --- | --- | --- | --- |
| Confidential share of Intents volume | {{conf_share_aug}} | {{conf_share_sep}} | {{conf_share_oct}} |
| Confidential volume | $0.43B | $1.35B | $1.63B |
| Captured revenue, bps of all volume | {{take_aug}} | {{take_sep}} | {{take_oct}} |

- **The fit.** Weekly, Aug–Oct ({{fit_weeks}} complete weeks): captured revenue ≈ **{{fit_pub}} bps × public volume + {{fit_conf}} bps × confidential volume** (R² {{fit_r2}}; bootstrap 90% interval on the confidential coefficient {{fit_ci}} bps; {{loo}} when any one week is left out; a daily fit gives {{daily_fit_conf}}). Confidential volume tracks inflows to the buyback wallet (correlation {{corr_conf_buyback}}; public volume {{corr_pub_buyback}}).
- **How far to trust it.** Thirteen points, and both series rise over the window, so a fit in levels can pick up a shared trend. The same fit on **week-to-week changes** gives {{fd_conf}} bps on confidential volume (90% interval {{fd_ci}}) and {{fd_pub}} on public. Dune's own fee table puts all confidential fees at {{dune_fee_bps}} bps of confidential volume, all time, inside that interval. So confidential swaps do pay NEAR more, but the premium is somewhere between about 3 and 10 bps (log 32).
- **How much of the jump it explains.** NEAR's take rose {{jump_rise}} bps between August and October while the confidential share rose {{jump_share_change}} points. The move to confidential swaps accounts for about **{{jump_levels}}** of the rise with the levels fit, **{{jump_dune}}** with Dune's fee table and **{{jump_fd}}** with the fit on changes. "Most of it" holds only on the first; the rest is repricing on public flows (see 1Click below).
- **What NEAR's own page shows.** NEAR captured {{cap_total_all}} of gross fees all-time and {{cap_total_d30}} over the last 30 days. All three of its collection mechanisms rose: front-end fees from {{cap_fe_all}} to {{cap_fe_d30}} of gross fees, partner revenue-sharing from {{cap_b2b_all}} to {{cap_b2b_d30}}, quote improvement from {{cap_qi_all}} to {{cap_qi_d30}} (revenue.near.org, 2026-11-11). The rise is broad, with NEAR's own front-end the largest part.
- **Why it grew**: NEAR@3.33 (NEAR Foundation, announced 2026-06-15) rewards users who keep a confidential balance on near.com and swap confidentially. Drop 1, 333,333 NEAR, was triggered when confidential TVL reached $70M (mid-September) and converts to NEAR once NEAR holds $3.33 for three days, which happened around 2026-09-21 (about **{{drop1_usd}}** at that price). Later rounds require more activity, which is consistent with TVL still growing after the snapshot. This is timing, not proof: near.com also launched new products over the same months, and there is no control group.
- **Cost against revenue**: confidential volume from the launch to October ≈ {{conf_vol_since_launch}}, i.e. **{{conf_rev_range}}** of revenue at {{dune_fee_bps}}–{{fit_conf}} bps. Drop 1 alone cost **a third to a half** of it, paid in NEAR that enters circulation, against about 1M NEAR captured by the revenue wallets in September and October.
- **Did it pay for itself?** At the May–Aug take rate, Sep–Oct volume would have produced {{sepoct_at_old}}; NEAR captured {{sepoct_actual}}. The {{uplift}} uplift is about {{uplift_over_drop1}} Drop 1's cost. In NEAR terms: the uplift bought about {{uplift_near}} NEAR while Drop 1 released 333k NEAR into circulation, a net {{net_near}} NEAR, or 0.01% of supply (log 25, 32). This credits the whole uplift to the incentive and counts only Drop 1 as its cost, so it is the favourable reading. Even so, the incentive moved revenue a lot and net supply hardly at all.
- **If the incentive ends** and the take rate falls back to its May–Aug level, the Monte Carlo puts the 2027 offset at a median {{mc_mayaug}} of issuance, half the base case; if it winds down over six months instead, {{mc_wind}} (log 26).
- **H4.1 is rejected**: confidential TVL did not leave after the snapshot. It was {{tvl_snap}} on 2026-09-16, {{tvl_snap_30d}} thirty days later, peaked at {{tvl_peak}} on {{tvl_peak_date}}, and was {{tvl_last}} on {{tvl_last_date}} (NEAR's revenue dashboard): still about twice the snapshot level, but {{tvl_from_peak}} below the peak.

#### Since November: the first out-of-sample test fails

- **The fit overshoots.** For the week of 2026-11-02, the levels fit predicted {{oos_pred}} of revenue and the fit on changes {{oos_pred_fd}}; NEAR captured **{{oos_actual}}** (log 30, 32). Part of the miss is the label change below; part is a real fall.
- **The fall is in three sources.** The take on all Intents volume was {{take_last_week}} bps in the week of 2 November ({{take_oct}} in October) while gross fees stayed at {{gross_last_week}} bps: NEAR kept {{capture_last_week}} of fees instead of {{capture_oct}}. DefiLlama's holders revenue gives {{take_nov_llama}} bps. NEAR's own monthly series stays about the same multiple of the wallets, so it implies about {{series_take_nov}} bps against {{series_take_oct}} in October: the same fall of about 30%.
- **The label changed.** From 2026-11-03, NEAR's Dune dataset labels almost all volume confidential ({{oos_conf_share}}), while the Explorer API still shows at least $20M of public 1Click swaps in half a day. The confidential share of volume can no longer be tracked, so the weekly fit is reported for Aug–Oct only, and the post-hoc criterion now watches confidential TVL.
- **Reading.** The September premium is real in the data through October. Ten days of November are not a trend, but they are the first data after TVL started falling, and they point down.

#### On 1Click (public swaps)


- Captured revenue / volume, 14-day rolling: about 2.2 bps in mid-August, 3.0 in mid-September, 5.4 in mid-October. Gross fees stayed at 14–16 bps, so NEAR's share of fees rose from about 15–20% to 35%. (log 7, 10)
- On 1Click (2.42M swaps collected from the Explorer API), NEAR's take went from 2.23 to 4.64 bps between the four weeks before the NEAR@3.33 snapshot and the last two weeks. Shift-share of the +2.4 bps (log 12):
  - +1.2 bps from a **new flow**: Trust Wallet's ZEC swaps at 20 bps to NEAR, from October;
  - about +1.4 bps from **higher fees in existing segments**: swaps without integrator 3.0 → 7.0 bps, Rango 0.6 → 4.2;
  - about −0.7 bps from a source that disappeared.
- The modal fee did not change (1 bp). The slice paying NEAR 11–20 bps went from 1% to 15% of volume and now brings 64% of NEAR's 1Click revenue.

### 3. NEAR does not own the customer

1Click swaps, {{oc_from}} to {{oc_to}}, the last 30 days collected ({{oc_swaps}} swaps in all; log 11, 18, 34):

{{oc_table}}

- NEAR keeps about 9% of the 1Click fee pool; integrators keep the rest.
- **ZEC** is 18.6% of 1Click volume over 76 days but about half of NEAR's 1Click revenue in the last two weeks. (log 13)
- **Users do not stay.** 3–5% of the addresses active in a given week come back in the same week three months later; at most 9–19% are seen again at any time over 2.5 months. These are lower bounds (a returning user with a new address counts as new). (log 14)
- Reading: NEAR's 1Click revenue rests on unattributed users, a few direct deals and one asset. Distribution partners own the flow, and could route it elsewhere.

Coverage limit: 1Click is about 28% of Intents volume, and confidential swaps were not visible in the Explorer API over the period collected. These results describe 1Click, not all of Intents.

### 4. It does not offset issuance

- Net issuance measured from archival-RPC total supply: **{{issuance}} a year**, 2.4–2.7M NEAR a month. (log 5)
- NEAR captured, Feb–Oct 2026: {{captured_feb_oct}} NEAR vs {{issued_feb_oct}} issued = **{{offset_rebuilt}}**. Monthly: {{offset_month_min}} to {{offset_month_max}}. NEAR's own dashboard gives {{offset_official}} over the same months: it counts {{emissions_gap}} more emissions and, as noted above, more revenue than reaches the wallets. Same order of magnitude. (log 5, 27, 29)
- **Issuance cut (HSP-029).** House of Stake's vote closed on 2026-11-02 with {{hsp_for}} of veNEAR cast in favour ({{hsp_voters}} voters, {{hsp_turnout}} turnout, read on-chain from `vote.dao`). It lowers maximum issuance from 2.5% to 1.6% a year over 24 months. Status on {{data_to}}: {{hsp_status}}, ending {{hsp_timelock_end}}; then a 90-day grace period and a protocol upgrade validators must adopt, so the ramp cannot start before {{hsp_earliest}}. Fully phased in, it lifts break-even from {{breakeven_now}} to {{breakeven_cut}} annual captured revenue. It narrows the gap by about a third. (log 31)
- Buybacks are reflexive: NEAR captured per month stayed in a 0.2–0.6M range with no upward trend while the price rose more than 4x from February to October. More dollars did not buy more NEAR.
- The invariant that matters, independent of volume: NEAR is net deflationary when **market cap / annual captured revenue < 1 / issuance rate ≈ {{breakeven_now}}**. Today: {{near_captured_mult}}. (log 6)
- The often-quoted "about $177M of daily volume makes NEAR deflationary" assumes 100% of fees buy NEAR. With the share that is actually captured, the threshold is about {{be_vol_now}} a day at today's price and take ({{take_now}} bps). (log 6, 17)

### 5. End-2027

Monte Carlo, 10,000 paths, volume and price drawn jointly in 30-day blocks from history (log 17, `make montecarlo`):

| Scenario | Share of 2027 issuance offset, median (p10–p90) | P(2027 net deflationary) |
| --- | --- | --- |
| Base: last 365 days, take at {{mc_base_take}} bps (last 30 days), no price drift | {{mc_base}} ({{mc_base_band}}) | {{mc_base_p}} |
| Base + approved issuance cut (HSP-029, from {{hsp_earliest}}) | {{mc_cut}} ({{mc_cut_band}}) | {{mc_cut_p}} |
| Take falls back to May–Aug ({{mc_mayaug_take}} bps) | {{mc_mayaug}} ({{mc_mayaug_band}}) | {{mc_mayaug_p}} |
| Incentive winds down over 6 months | {{mc_wind}} ({{mc_wind_band}}) | {{mc_wind_p}} |
| Wind-down + issuance cut | {{mc_windcut}} ({{mc_windcut_band}}) | {{mc_windcut_p}} |
| Only the buyback wallet counts as retired | {{mc_bbonly}} ({{mc_bbonly_band}}) | {{mc_bbonly_p}} |
| Take doubles again ({{mc_double_take}} bps) | {{mc_double}} ({{mc_double_band}}) | {{mc_double_p}} |
| Last 180 days (volume ~{{mc_bull_vol_mult}} by Dec 2027) | {{mc_bull}} ({{mc_bull_band}}) | {{mc_bull_p}} |

Break-even at today's price: about {{be_vol_now}}/day at {{take_now}} bps, {{be_vol_8}}/day at 8 bps, {{be_vol_15}}/day at 15 bps. The dashboard recomputes these daily.

What the simulation assumes, and what that does to the result:

- **The take rate is fixed** at its last-30-day value in each scenario (or follows the stated ramp). It is a policy choice, not a random variable, which is why it is varied by scenario.
- **Volume and price are redrawn from the past**, together, in 30-day blocks. A regime that has not happened yet (a second product, a collapse) is outside the fan.
- **Issuance** is the measured rate applied to today's supply; the HSP-029 scenarios scale it by the approved schedule from the earliest start the chain allows ({{hsp_earliest}}).
- **Track record.** In a walk-forward test the engine was too optimistic in 2026 (log 21), so the percentages above are more likely too high than too low.

### 6. Against peers and competitors

- **Peers.** Tokens whose holders receive protocol revenue trade at a median **{{peers_median}}** market cap / annualised holders revenue ({{peers_n}} peers with material holders revenue, interquartile {{peers_iqr}}). NEAR trades at **{{near_holders_mult}}**. At the peer median, NEAR Intents' revenue would support about {{near_value_at_peer}} of market cap, against {{near_mcap}}: about {{share_not_revenue}} of NEAR's value rests on something other than this revenue (log 22). NEAR is a layer 1 and most peers are applications, so the gap is partly a category premium, not a mispricing.
- **Competitors.** Among cross-chain swap venues on DefiLlama, NEAR Intents went from 6% of volume (June 2025) to 58–79% each month from May to October 2026, while THORChain fell from 84% to 4–31%. November to date reverses it (NEAR 35%, THORChain 53%): DefiLlama shows THORChain volume above $180M a day from 4 November. That is eight days of data and may be a reporting artefact; it is flagged, not concluded. NEAR led its category on volume for six months; it has not yet turned that share into enough captured revenue.
- **Protocol fee.** The `intents.near` fee itself is 1 pip (about 0.01 bps), unchanged since March 2025: NEAR's revenue comes from app fees, not from the protocol fee.

### 7. The holder's view

- **Risk** (daily prices, Nov 2024 to Nov 2026): NEAR's volatility is about **{{near_vol}} a year** against {{btc_vol}} for BTC; its worst drawdown was **{{near_maxdd}}** (Dec 2024 to Feb 2026), with {{near_underwater}} days under water; beta to BTC about 1.3–1.5. Revenue has not dampened the token's swings.
- **Dilution**: issuance adds {{issuance}} of supply a year; buybacks at the last 30 days' pace remove {{buyback_rate}}. Supply still grows about **{{net_growth}} a year**. A holder who does not stake loses about 2% of their share of the network each year; stakers ({{staked}} of supply) earn about {{staker_reward}} gross, before validator commission. Today, staking, not buybacks, is what protects a holder from dilution.
- **What NEAR earns on** (1Click, {{oc_from}} to {{oc_to}}): swaps whose volatile leg is BTC bring {{asset_btc}} of NEAR's revenue, ETH {{asset_eth}}, ZEC {{asset_zec}}. Stablecoin-to-stablecoin swaps are {{asset_stable_vol}} of volume but {{asset_stable_near}} of revenue, at {{asset_stable_bps}} bps.
- **What changed in November** (1Click, 16–29 Oct against 1–10 Nov; log 34): NEAR's take fell from {{oc_bps_oct}} to {{oc_bps_nov}} bps while volume rose ({{oc_vol_oct}} to {{oc_vol_nov}} a day). Most of the gap is one flow: Trust Wallet routed {{trust_burst_vol}} of swaps ({{trust_burst_zec}} ZEC) at 20 bps between 23 and 28 October, {{trust_share_oct}} of NEAR's 1Click revenue in the second half of October, then stopped. Without Trust Wallet the take went from {{oc_bps_oct_ex}} to {{oc_bps_nov_ex}} bps. ZEC fell from {{zec_vol_oct}} to {{zec_vol_nov}} of volume and from {{zec_near_oct}} to {{zec_near_nov}} of NEAR's revenue. What held: NEAR's revenue from swaps without an integrator, its own front-end and direct users ({{noref_day_oct}} then {{noref_day_nov}} a day), now {{noref_share_nov}} of NEAR's 1Click revenue. The fall in late-October pricing was one integrator's burst, not a broad repricing; the part NEAR controls did not fall.

### 8. The track's own hypothesis: does usage lead the price?

The track suggests testing whether cross-chain volume through NEAR Intents is a better signal of real usage than the token price. Weekly data, {{ll_weeks}} complete weeks, NEAR's price taken net of BTC (beta {{ll_beta}}) so that a market-wide move does not count as a NEAR signal (log 33, `make leadlag`):

- **Usage does not lead the price, and the price does not lead usage.** Intents volume, L1 transactions and L1 active accounts, lags of one to four weeks, both directions: {{ll_sig}} of {{ll_tests}} correlations are significant after Holm's correction. The strongest before correction is {{ll_best}}.
- **The two kinds of usage have parted ways.** Over the last 30 days against the same window a year earlier, Intents volume is {{yoy_vol}} while L1 transactions are {{yoy_txns}} and L1 active accounts {{yoy_active}}. Counting transactions says NEAR is shrinking; counting settled volume says it is growing.
- **What tracks NEAR's revenue.** Weekly changes in captured revenue since March correlate {{ll_rev_vol}} with Intents volume, {{ll_rev_txns}} with L1 transactions, {{ll_rev_active}} with active accounts and {{ll_rev_price}} with the BTC-adjusted price ({{ll_rev_weeks}} weeks).
- **Reading.** Intents volume is the better measure of what NEAR earns, but neither it nor L1 activity says anything about next month's price. That fits the valuation finding: the market does not price NEAR on this revenue.

### 9. Public claims, checked

Statements made in public about NEAR's buybacks and issuance, set against this audit's data (rendered by `make docs` from the same outputs):

{{public_claims_table}}

## Bull case and bear case

**Bull.** Confidential swaps are a product NEAR monetises better than public swaps (about {{premium_range}} bps against {{public_range}}), and they reached {{conf_share_oct}} of volume. If a part of that use outlives the airdrop, the take rate stays well above its old level. The take rate is a lever NEAR can still pull: it doubled in two months and the sensitivity table shows that 8–15 bps with 2–4x today's volume reaches break-even. A single deal with the largest integrator, which now pays NEAR almost nothing, would add more revenue than any volume growth. The revenue is clean, reconciles to the chain and is not being sold.

**Bear.** The rise came mostly from confidential swaps whose growth coincides with an airdrop (Drop 1 cost about three quarters of the revenue uplift over its two best months), with each parked dollar swapped every 2–3 days. On 1Click, it came from pricing on flows NEAR controls (users without integrator, ZEC), the flows most exposed to competition. Integrators own the users, users do not stay, and half the 1Click revenue rides on one asset. If the take falls back to its May–Aug level, buybacks offset a tenth of issuance. Nearly half of what is called "buyback" sits in a treasury with no commitment not to sell.

## What would change our mind

Kill criteria were registered before the analysis and are monitored live on the dashboard. They are tripwires on the quality of the revenue: each one, if it holds for 30 consecutive days, would make the picture worse than this report describes. What would change the conclusion in NEAR's favour is listed under the catalysts below.

| Criterion | Status, data to {{data_to}} |
| --- | --- |
| 30-day revenue below 50% of its trailing 180-day average | Not triggered: {{kill1}} of the average |
| Buyback inflows stop for more than 14 days while fees continue | Not triggered: inflow yesterday |
| Top integrator above 60% of fees | **Triggered on 1Click** (SwapKit, 65–75% of app fees, all year), though SwapKit brings NEAR {{sk_near}} of its 1Click revenue. The criterion did not say whose fees; we report it as written. All-Intents measure pending. |
| *Added after the fact, reported separately:* confidential TVL back below its level on the NEAR@3.33 snapshot day ($71M) | Not triggered: {{tvl_last}}, but {{tvl_from_peak}} below the peak |

The third result is a lesson as much as a finding: a kill criterion should measure the quantity the thesis depends on, NEAR's captured revenue, not a proxy.

## Dated predictions

Six predictions were frozen on 2026-11-11 in [`predictions/PREDICTIONS.csv`](predictions/PREDICTIONS.csv) (sha256 committed and checked by a test; Bitcoin timestamp in `PREDICTIONS.csv.ots`). P1 and P2 resolve on 2026-11-15, before judging starts; P3 on 2026-11-17; the rest by April 2027. `make predictions` resolves them from the data; results in [`predictions/RESULTS.md`](predictions/RESULTS.md).

## Catalysts to watch

- Whether the take rate holds above 5 bps through Q4: the first full week of November ({{take_last_week}} bps) says it may not (prediction P1 resolves on 2026-11-15).
- HSP-029 leaving its timelock on {{hsp_timelock_end}} (prediction P3), then the validator upgrade that starts the ramp.
- A revenue-sharing deal with SwapKit or other large integrators.
- An on-chain commitment (or a sale) by the front-end fund.
- ZEC flows: their share of NEAR's revenue, and whether Trust Wallet's deal lasts.
- Confidential TVL and NEAR's take once NEAR@3.33 rounds stop (further drops are "tba", per NEAR's moderators): the test of whether the take-rate jump is durable.

## Conviction and limits

- **High** on "real" and on "too small to offset issuance today": both follow from on-chain data and an identity.
- **Medium-low** on durability: the September jump is partly explained (confidential swaps account for a fifth to five sixths of it depending on the method, log 24, 32), and that channel grew under an incentive whose causal role is plausible but unproven. The fee NEAR earns on confidential swaps is estimated (about 5–11 bps), not published, and early November fell below every version of the fit.
- **Low** on end-2027 paths: the bootstrap can only replay the past, and the take rate is a policy choice.
- A walk-forward check of the simulation engine (log 21) shows it **overestimated** buyback capacity in 2026: realised outcomes fell below the 10th percentile in a third of 90-day forecasts. If anything, the {{mc_base}} base case is too generous, which makes "net inflationary through 2027" a conservative conclusion.

Questions sent to the NEAR team (Discord ticket 2026-11-04, then near.com support, forwarded internally, no answer yet): the fee on confidential intents and who receives it, further NEAR@3.33 drops (answer: "tba"), and whether the front-end fund's NEAR is ever sold. One more is open since 2026-11-11: why NEAR's revenue series is about 20% above what the three wallets receive. Confidential TVL now has a public source (revenue.near.org).

## Reproduce

```bash
pip install -r requirements.txt
make check-clean   # every offline step on the committed snapshots, the tests, and a comparison of every output with the committed one
make verify        # renders README/REPORT/FAQ from the outputs and re-checks the 13 findings
make refresh       # optional, with network: fresh snapshots, then everything again
```

Swap-level data (pillar 3) needs a NEAR Intents partner key (`INTENTS_JWT`); its aggregated outputs are committed in `data/processed/`.
