-- Transactions on NEAR by the weekly activity of their signer, Nov 2024 to Nov 2026 (about 71 GB scanned).
-- light = a signer with at most 50 transactions that week (at most about 7 a day: human scale);
-- heavy = more than 5,000 a week (bots, relayers, contracts that sign their own work, such as intents.near).
-- Result saved as data/raw/bigquery/signers_weekly_<run date>.csv (counts only, no account).
WITH s AS (
  SELECT DATE_TRUNC(block_date, WEEK(MONDAY)) AS week, signer_account_id AS a, COUNT(*) AS n
  FROM `bigquery-public-data.crypto_near_mainnet_us.transactions`
  WHERE block_date BETWEEN '2024-11-04' AND '2026-11-08'
  GROUP BY 1, 2)
SELECT week, COUNT(*) AS signers, SUM(n) AS txns,
  COUNTIF(n <= 50) AS light_signers, SUM(IF(n <= 50, n, 0)) AS light_txns,
  COUNTIF(n > 50 AND n <= 5000) AS mid_signers, SUM(IF(n > 50 AND n <= 5000, n, 0)) AS mid_txns,
  COUNTIF(n > 5000) AS heavy_signers, SUM(IF(n > 5000, n, 0)) AS heavy_txns,
  COUNTIF(n <= 50 AND REGEXP_CONTAINS(a, r'^[0-9a-f]{64}$')) AS light_implicit,
  COUNTIF(n <= 50 AND ENDS_WITH(a, '.tg')) AS light_tg
FROM s GROUP BY 1 ORDER BY 1
