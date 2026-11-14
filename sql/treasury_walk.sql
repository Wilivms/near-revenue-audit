-- Where the protocol treasury's NEAR went in 2026 (run 14 Nov 2026; about 1.2 TB scanned per statement).
-- 1) Moves out of treasury.near in 2026 (transfers and calls carrying a deposit):
SELECT FORMAT_DATE('%Y-%m', block_date) AS month, receipt_receiver_account_id AS destination, COUNT(*) AS n,
  SUM(SAFE_CAST(JSON_VALUE(args, '$.deposit') AS BIGNUMERIC)) / 1e24 AS near
FROM `bigquery-public-data.crypto_near_mainnet_us.receipt_actions`
WHERE block_date BETWEEN '2026-01-01' AND '2026-11-12' AND action_kind IN ('TRANSFER', 'FUNCTION_CALL')
  AND receipt_predecessor_account_id = 'treasury.near'
GROUP BY 1, 2 HAVING near > 0 ORDER BY 1, near DESC;
-- Result: April, 4.9M NEAR each to ecotreasury4 and ecotreasury5.multisignature.near; May, 20.37M NEAR to dcc79d2c...

-- 2) Hop by hop through every move of 100,000 NEAR or more (saved as data/raw/bigquery/treasury_walk_<run date>.csv, main
--    paths; the last hop, 7875aef7... to the cnear pools on 6-7 Oct, read from NearBlocks because the walk stops at 6 hops).
CREATE TEMP TABLE big AS
SELECT block_date, receipt_predecessor_account_id AS sender, receipt_receiver_account_id AS destination,
  JSON_VALUE(args, '$.method_name') AS method, SAFE_CAST(JSON_VALUE(args, '$.deposit') AS BIGNUMERIC) / 1e24 AS near
FROM `bigquery-public-data.crypto_near_mainnet_us.receipt_actions`
WHERE block_date BETWEEN '2026-04-01' AND '2026-11-12' AND action_kind IN ('TRANSFER', 'FUNCTION_CALL')
  AND SAFE_CAST(JSON_VALUE(args, '$.deposit') AS BIGNUMERIC) >= 100000 * 1e24;
WITH RECURSIVE walk AS (
  SELECT 1 AS hop, sender, destination, block_date, near, method FROM big
  WHERE sender IN ('ecotreasury4.multisignature.near', 'ecotreasury5.multisignature.near',
                   'dcc79d2cbd9dcfd6159793a987619b5d7b7446d594aba451318a84b6acb40058')
  UNION ALL
  SELECT w.hop + 1, b.sender, b.destination, b.block_date, b.near, b.method
  FROM walk w JOIN big b ON b.sender = w.destination AND b.block_date >= w.block_date
  WHERE w.hop < 6)
SELECT hop, sender, destination, method, COUNT(*) AS n, SUM(near) AS near, MIN(block_date) AS first_day, MAX(block_date) AS last_day
FROM (SELECT DISTINCT * FROM walk) GROUP BY 1, 2, 3, 4 ORDER BY hop, near DESC;
