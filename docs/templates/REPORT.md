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
| It does not move after the fact | The same rebuild run on each of {{rv_rb_snaps}} dated wallet snapshots ({{rv_first}} to {{rv_last}}): {{rv_rb_moved}} of {{rv_rb_pairs}} complete-day readings changed. DefiLlama's gross fees for the latest day were revised up to {{rv_fee_factor}} ({{rv_fee_day}}: {{rv_fee_first}} → {{rv_fee_latest}}) and NEAR's dashboard, fed the same way, up to {{rv_nd_factor}}; both settle after {{rv_fee_settle}} days, revenue after two (at most {{rv_rev_max}}) | log 56, `make revisions` (F16) |

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

1Click swaps, {{oc_from}} to {{oc_to}}, the last 30 days collected ({{oc_swaps_30}} swaps; {{oc_swaps}} collected in all; log 11, 18, 34, 36):

{{oc_table}}

- Integrators keep about {{oc_integrators_keep}} of the 1Click fee pool; NEAR keeps the rest.
- **ZEC** is 18.6% of 1Click volume over 76 days but about half of NEAR's 1Click revenue in the last two weeks. (log 13)
- **Users do not stay.** 3–5% of the addresses active in a given week come back in the same week three months later; at most 9–19% are seen again at any time over 2.5 months. These are lower bounds (a returning user with a new address counts as new). (log 14)
- **The volume is broad, not wash-traded** (`oneclick_quality.json`, log 36). {{q_senders}} sending addresses ({{q_with_sender}} of swaps carry one); {{q_one_swap}} swapped once. The top 10 send {{q_top10}} of volume and the top 100 {{q_top100}} (HHI {{q_hhi}}). {{q_heavy_n}} addresses with 100 swaps or more, likely bots, market makers and integrator hot wallets, send {{q_heavy_vol}} of volume and {{q_heavy_rev}} of NEAR's revenue. Round trips, where an address swaps A into B and B back into A within 24 hours, are {{q_rt_vol}} of volume and {{q_rt_rev}} of NEAR's revenue, {{q_rt_ref}} of them through one integrator (LI.FI). Self-trading does not inflate the revenue. An independent entry (Toll Road) finds about 1% round trips outside market makers on a 1.2% sample of `intents.near`; the full 1Click record agrees.
- **The freeze and the exploit cost NEAR little revenue, but large integrators pulled back** (`make incident`, F17, log 59 and 61). On 29 September 1Click blocked a $50M swap linked to the Bitget hacker; on 1 October an exploit in the Omni deposit path drained about $3.8M (returned the next day). From the swaps: no swap from {{ic_from}} to {{ic_to}} UTC on 1 October, a {{ic_hours}}-hour halt (the longest gap the week before was {{ic_gap_week}} minutes), about {{ic_vol_lost}} of volume and {{ic_rev_lost}} of NEAR revenue at the previous week's pace. The first full hour after the reopening ran at {{ic_first_hour}} of the usual volume for that hour, the first 24 hours at {{ic_first_day}}. Then the median day of the two weeks after (3–16 Oct) against the two weeks before (15–28 Sep), ranked against the same split at each of {{ic_pn}} placebo dates whose windows avoid the incident:

  | Median day, after against before | Freeze and exploit | Placebo median | p (two-sided) |
  | --- | --- | --- | --- |
  | 1Click volume | {{ic_d_volume_usd_change}} | {{ic_dm_volume_usd_change}} | {{ic_dp_volume_usd_change}} |
  | NEAR's 1Click revenue | {{ic_d_near_usd_change}} | {{ic_dm_near_usd_change}} | {{ic_dp_near_usd_change}} |
  | Sending addresses | {{ic_d_senders_change}} | {{ic_dm_senders_change}} | {{ic_dp_senders_change}} |
  | New sending addresses | {{ic_d_new_senders_change}} | {{ic_dm_new_senders_change}} | {{ic_dp_new_senders_change}} |
  | Of the {{ic_top}} largest integrators, kept at least half their volume | {{ic_d_top_kept_half}} | {{ic_dm_top_kept_half}} | {{ic_dp_top_kept_half}} |
  | Volume of those {{ic_top}} integrators | {{ic_d_top_volume_change}} | {{ic_dm_top_volume_change}} | {{ic_dp_top_volume_change}} |

  With {{ic_pn}} placebo dates the smallest possible p is 0.09: volume, the integrators who kept their volume and their combined volume all fell further than at any placebo date. Users did not leave (sending addresses, new ones included, within the usual range) and NEAR's revenue held, because its take was rising. The cost was paid by the large integrators: {{ic_cut}} of the 25 cut their volume by more than half, and {{ic_back}} of them were back above half by 31 Oct–12 Nov (the 25 together still {{ic_top_nov}} against before). A new sending address is one first seen since 14 August, when the collection starts, so that count drifts down over time; it is read against the placebo dates, which share the drift. Integrators appear in the committed aggregates under a one-way pseudonym only. Medians, because the rival venues carried a few $250M–300M days on 25–30 September.
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

- **Peers.** Tokens whose holders receive protocol revenue trade at a median **{{peers_median}}** market cap / annualised holders revenue ({{peers_n}} peers with material holders revenue, interquartile {{peers_iqr}}). NEAR trades at **{{near_holders_mult}}**. At the peer median, NEAR Intents' revenue would support about {{near_value_at_peer}} of market cap, against {{near_mcap}} (about {{price_at_peer}} a NEAR, against {{price_now}}): about {{share_not_revenue}} of NEAR's value rests on something other than this revenue (log 22). NEAR is a layer 1 and most peers are applications, so the gap is partly a category premium, not a mispricing.
- **Competitors.** Among cross-chain swap venues on DefiLlama, NEAR Intents went from 6% of volume (June 2025) to 58–79% each month from May to October 2026, while THORChain fell from 84% to 4–31%. November to date reverses it (NEAR 35%, THORChain 53%): DefiLlama shows THORChain volume above $180M a day from 4 November. That is eight days of data and may be a reporting artefact; it is flagged, not concluded. NEAR led its category on volume for six months; it has not yet turned that share into enough captured revenue.
- **Price.** Will competing routers compete NEAR's take away? A quote race (`src/ingest/quotes.py`, `make quotes`) asks 1Click, Relay, LI.FI and, on same-asset routes, Across for the same swap within the same minute, on five corridors at about $1k and $20k, and keeps every answer in `data/raw/quotes/`. Over {{qr_rounds}} rounds ({{qr_first}} to {{qr_last}} UTC, {{qr_swaps}} swaps), 1Click paid the user the most in **{{qr_best_share}}** of swaps, a median **{{qr_median}}** from the best alternative, all fees included:

  | Corridor | 1Click against the best alternative (median) |
  | --- | --- |
  | Native BTC to EVM | {{qr_c_btc}} |
  | Same asset, L2 to L2 (USDC) | {{qr_c_l2}} |
  | Cross asset, EVM (ETH to USDC) | {{qr_c_xasset}} |
  | Same asset, Ethereum to L2 (ETH) | {{qr_c_l1l2}} |
  | Solana to EVM (SOL to USDC) | {{qr_c_sol}} |

  LI.FI's public quote includes its default 0.25% fee; without it, LI.FI would beat everyone (1Click {{qr_ex_lifi_median}}), so the result depends on which front-end a user comes through. Quotes are not fills and leave out the origin-chain gas each route needs. Read with the 1Click data: NEAR keeps a few basis points inside a price that is level with the market, so its take is not what loses 1Click a swap; where 1Click loses (Ethereum to L2, Solana), the gap is a few basis points, about the size of the take itself. More rounds are added at each refresh.
- **Protocol fee.** The `intents.near` fee itself is 1 pip (about 0.01 bps), unchanged since March 2025: NEAR's revenue comes from app fees, not from the protocol fee.

### 7. The holder's view

- **Risk** (daily prices, Nov 2024 to Nov 2026): NEAR's volatility is about **{{near_vol}} a year** against {{btc_vol}} for BTC; its worst drawdown was **{{near_maxdd}}** (Dec 2024 to Feb 2026), with {{near_underwater}} days under water; beta to BTC about 1.3–1.5. Revenue has not dampened the token's swings.
- **Dilution**: issuance adds {{issuance}} of supply a year; buybacks at the last 30 days' pace remove {{buyback_rate}}. Supply still grows about **{{net_growth}} a year**. A holder who does not stake loses about 2% of their share of the network each year; stakers ({{staked}} of supply) earn about {{staker_reward}} gross, before validator commission. Today, staking, not buybacks, is what protects a holder from dilution.
- **What NEAR earns on** (1Click, {{oc_from}} to {{oc_to}}): swaps whose volatile leg is BTC bring {{asset_btc}} of NEAR's revenue, ETH {{asset_eth}}, ZEC {{asset_zec}}. Stablecoin-to-stablecoin swaps are {{asset_stable_vol}} of volume but {{asset_stable_near}} of revenue, at {{asset_stable_bps}} bps.
- **What changed in November** (1Click, 16–29 Oct against 1–10 Nov; log 34): NEAR's take fell from {{oc_bps_oct}} to {{oc_bps_nov}} bps while volume rose ({{oc_vol_oct}} to {{oc_vol_nov}} a day). Most of the gap is one flow: Trust Wallet routed {{trust_burst_vol}} of swaps ({{trust_burst_zec}} ZEC) at 20 bps between 23 and 28 October, {{trust_share_oct}} of NEAR's 1Click revenue in the second half of October, then stopped. Without Trust Wallet the take went from {{oc_bps_oct_ex}} to {{oc_bps_nov_ex}} bps. ZEC fell from {{zec_vol_oct}} to {{zec_vol_nov}} of volume and from {{zec_near_oct}} to {{zec_near_nov}} of NEAR's revenue. What held: NEAR's revenue from swaps without an integrator, its own front-end and direct users ({{noref_day_oct}} then {{noref_day_nov}} a day), now {{noref_share_nov}} of NEAR's 1Click revenue. The fall in late-October pricing was one integrator's burst, not a broad repricing; the part NEAR controls did not fall.

### 8. The track's own hypothesis: does usage lead the price?

The track suggests testing whether cross-chain volume through NEAR Intents is a better signal of real usage than the token price. Weekly data, {{ll_weeks}} complete weeks, NEAR's price taken net of BTC (beta {{ll_beta}}) so that a market-wide move does not count as a NEAR signal (log 33, `make leadlag`):

- **Usage does not lead the price, and the price does not lead usage.** Intents volume, L1 transactions and L1 active accounts, lags of one to four weeks, both directions: {{ll_sig}} of {{ll_tests}} correlations are significant after Holm's correction. The strongest before correction is {{ll_best}}. How strong a lead could this miss? With these weeks, a correlation needs to reach about {{rob_f13_single}} to be found 80% of the time in a single test, and {{rob_f13_holm}} at the strictest step of Holm's correction; a weaker lead could exist and go undetected. The finding is that no lead strong enough to trade on shows up, not that none exists (`make robustness`).
- **The two kinds of usage have parted ways.** Over the last 30 days against the same window a year earlier, Intents volume is {{yoy_vol}} while L1 transactions are {{yoy_txns}} and L1 active accounts {{yoy_active}}. Counting transactions says NEAR is shrinking; counting settled volume says it is growing.
- **What tracks NEAR's revenue.** Weekly changes in captured revenue since March correlate {{ll_rev_vol}} with Intents volume, {{ll_rev_txns}} with L1 transactions, {{ll_rev_active}} with active accounts and {{ll_rev_price}} with the BTC-adjusted price ({{ll_rev_weeks}} weeks).
- **Reading.** Week to week, NEAR's revenue moves with both Intents volume and L1 transactions (the two move together within a week), but over a year they part ways and only Intents volume grew with revenue. Neither says anything about next month's price. That fits the valuation finding: the market does not price NEAR on this revenue.

### 9. Public claims, checked

{{public_claims_n}} statements made in public about NEAR's revenue, buybacks, issuance and usage, by NEAR, analysts, treasury companies and the press, each tested on the committed snapshots at the claim's own date where it has one (rendered by `make docs` from the same outputs; `public_claims()` in `src/figures.py`). {{public_claims_survive}} survive, {{public_claims_close}} are close (within about 10%, or within definitions), {{public_claims_fail}} do not hold as stated. The pattern: volume and usage figures quoted in public are accurate; claims about value reaching holders (deflation, NEAR staked or permanently removed, buyback totals on NEAR's own series, price reflexivity) are the ones that fail. NEAR's own fee schedule fails in the same place: the 20 bps that 1Click is meant to keep on integrator swaps is paid on a small part of that volume; custom deals are the norm.

{{public_claims_table}}

### 10. The two questions NEAR did not answer, and what the data says

Both were asked on three channels (Discord support ticket, near.com support, the NearBuilders Telegram) without an answer from the team by the deadline. The data narrows each to one testable hypothesis (`make open-questions`, `open_questions.json`, log 42).

**H-A. Confidential swaps pay NEAR about {{oq_bb_conf}} bps, and it lands in the buyback multisig.** Run per wallet instead of on total revenue, the weekly fit splits cleanly ({{oq_weeks}} weeks, Aug–Oct):
- the **buyback multisig** follows confidential volume (correlation {{oq_bb_corr}}, against {{oq_bb_corr_pub}} with public volume): **{{oq_bb_conf}} bps** on confidential volume (bootstrap 90% interval {{oq_bb_band}}, leaving out any one week {{oq_bb_loo}}, {{oq_bb_fd}} on week-to-week changes) and {{oq_bb_pub}} bps on public volume;
- the **front-end fund** adds {{oq_fe_conf}} bps in levels but {{oq_fe_fd}} on week-to-week changes: a shared trend, not a fee on confidential swaps.

*Measured directly, without a fit* (NEAR's BigQuery dataset, `make bigquery`, log 55): the NEAR that reaches the two wallets through accounts funded by the confidential pool went from {{pool_share_jun}} of their inflow in June to {{pool_share_aug}} in August and {{pool_share_oct}} in October. Valued at the week's NEAR price and divided by NEAR's own confidential volume, that payout is **{{pool_bps}} bps** over the fit's weeks (10 August–1 November), against {{pool_rest_bps}} bps for the rest of the revenue on public volume: the same premium, from the money rather than from a regression.

So the 11 bps of the total-revenue fit was 7.6 bps of confidential fee plus a front-end trend, and the confidential rate sits where NEAR's Dune fee table puts it (7.4 bps). *What would confirm it:* NEAR publishing the confidential rate, or a confidential swap's fee transfer to `buybacks.multisignature.near` read on chain. *What would refute it:* a published rate outside 5–9 bps.

**H-B. Most of the gap between NEAR's revenue series and its wallets is quote-improvement revenue that does not reach the three wallets.** NEAR's dashboard splits what it captures into front-end fees, B2B partner fees and quote improvement (its half of execution better than quoted), for four windows. Its revenue series is that capture times gross fees (they agree to the dollar over all time). Against what the three wallets received over the same windows:

| Window | Reported over wallets | Without quote improvement |
| --- | --- | --- |
| last 7 days | +{{oq_gap_d7}} | +{{oq_gap_d7_ex}} |
| last 30 days | +{{oq_gap_d30}} | {{oq_gap_d30_ex}} |
| year to date | +{{oq_gap_ytd}} | +{{oq_gap_ytd_ex}} |
| all time | +{{oq_gap_all}} | +{{oq_gap_all_ex}} |

Quote improvement is {{oq_qi_share}} of NEAR's reported revenue ({{oq_qi_ytd_usd}} this year). Taking it out brings the series within a few percent of the wallets on every window longer than a week; what remains is timing (sweeps lag fees by days) and, all time, the 2025 USDC period. *Reading:* about a tenth of the revenue NEAR reports never reaches the wallets that buy NEAR; the offset that matters for supply is the wallet-based {{offset_rebuilt}}, not {{offset_official}}. *What would confirm it:* the account that receives the protocol's quote-improvement share, or NEAR stating that its revenue series counts it. *What would refute it:* quote-improvement fees arriving in one of the three wallets.

*Followed on-chain* (NEAR's BigQuery dataset, queries in [`sql/revenue_pipeline.sql`](sql/revenue_pipeline.sql), log 49). Every NEAR the buyback multisig and the front-end fund received from `intents.near` since August arrived through a `native_withdraw` intent: 1.10M and 0.49M NEAR, within 0.5% of the wallet histories this audit rebuilds. About half of the buyback inflow comes from two accounts inside `intents.near` that collect fees in some 170 tokens and convert them to NEAR (751 and 320 withdrawals); the rest, and almost all of the front-end fund's, comes from about 2,350 accounts that each withdrew once. On 13 November the three collecting accounts held about $14k of unconverted fees, under 1% of a month's revenue, so fees waiting to be converted do not explain the gap. Tracing the swaps further shows why NEAR's half of quote improvement cannot be found on the public chain. The account through which the 1Click swaps we traced on 13 November settle (`51e8f94d…`) held about $136M of tokens inside `intents.near` on 13 November, the size of NEAR's confidential TVL ($137.9M on 12 November): it is the confidential pool's account, the bridge to the private shard. The fee arithmetic of these swaps (the confidential fee, and very likely the protocol's half of quote improvement) happens inside the private shard; what the public chain shows is the payout. From 1 October to 12 November, 459,514 of the 623,868 NEAR withdrawn to the buyback multisig and the front-end fund (74%) came through one-off accounts that the pool had funded. Most of NEAR's revenue now leaves the confidential pool, and the swaps that earned it cannot be seen. The other recurring recipients were a market maker and the protocol fee collector (`7066024d…`, $0.4k). H-B remains the best explanation, not a proof; NEAR naming the account would settle it.

### 11. What moved NEAR: {{ev_n}} events tested the same way

The incident method, applied to every major NEAR event of the last year (`make events`, log 61). For each event: the median day of two weeks after against two weeks before (two-day gaps), on NEAR Intents volume, the revenue rebuilt from the wallets, the take, Intents' share of cross-chain swap volume against THORChain, Chainflip and Maya, and NEAR's return against Bitcoin (abnormal log return, beta from the 120 days before). Each change is ranked against the same split at {{ev_placebo}} dates of the last year at least three weeks from any event; **bold** = outside the placebo range at p ≤ 0.10.

{{ev_table}}

- **The market paid for the airdrop, not for the supply cuts.** The NEAR@3.33 snapshot is the only event that moved revenue ({{ev_snap_rev}}) and the price ({{ev_snap_px3}} against Bitcoin in three days, {{ev_snap_px14}} in two weeks). The issuance halving left the price flat ({{ev_halv_px3}} in three days), and the approval of HSP-029's further cut was followed by {{ev_hsp_px3}}. The fee switch drew {{ev_fs_px3}} in three days, not outside the usual range.
- **The exploit did not move the price** ({{ev_exp_px3}} in three days, within the usual range) and Intents-wide revenue held; the take rose, as it was rising anyway.
- **Coincidences named, not explained.** The volume and share jumps after the halving coincide with the Zcash boom of late 2025, and the share fall after HSP-029 with THORChain's November lead; neither is plausibly caused by the event.
- {{ev_unusual}} of {{ev_tests}} tests come out at p ≤ 0.10, against about {{ev_expected}} expected by chance: some of these are noise, so read each one with its own story and not as proof.

### 12. How fragile is each finding?

Every finding rests on choices: a window, a source, a denominator, a price. `make robustness` (log 62) recomputes each one under the alternatives a careful reader would try first, from the committed outputs, and records whether it still holds. **{{rob_alt_hold}} of {{rob_alt}} alternatives hold; fragile: {{rob_fragile}}.** A *stress* test asks for more than the finding claims and shows where it would break.

{{rob_table}}

- **F5 is the fragile one.** On whole months the take rose 2.2x to 2.5x from August to October, but on the last two weeks of each month it rose 1.8x: the rise is real (the take more than doubled from its May–August level by any window), "more than double" depends on the window, so F5 now says "doubled" and gives the range.
- **F4 would break only at a NEAR price near ${{rob_be}}**, {{rob_be_drop}} below today's: at today's revenue, that is where the market cap would meet the post-HSP-029 break-even multiple.
- **F8 holds for any pre-campaign baseline**, but if Drop 1's tokens are valued at 1.5x the conversion price, the airdrop cost more than it brought.
- Stress results are not hidden by the tests: they mark the edge of each claim.

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

Questions sent to the NEAR team (Discord ticket 2026-11-04, near.com support, then the NearBuilders Telegram on 2026-11-13; the support assistants pointed to the fee schedule, which publishes no confidential rate, and had no rule for the revenue series; no answer from the team by the submission deadline): the fee on confidential intents and who receives it, further NEAR@3.33 drops (answer: "tba"), and whether the front-end fund's NEAR is ever sold. One more is open since 2026-11-11: why NEAR's revenue series is about {{series_over_wallets}} above what the three wallets receive. Confidential TVL now has a public source (revenue.near.org).

## Reproduce

```bash
pip install -r requirements.txt
make check-clean   # every offline step on the committed snapshots, the tests, and a comparison of every output with the committed one
make verify        # renders README/REPORT/FAQ from the outputs and re-checks the {{claims_n}} findings
make refresh       # optional, with network: fresh snapshots, then everything again
```

Swap-level data (pillar 3) needs a NEAR Intents partner key (`INTENTS_JWT`); its aggregated outputs are committed in `data/processed/`.
