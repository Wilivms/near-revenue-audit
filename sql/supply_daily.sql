-- Total supply at the last block of each day (about 1.3 GB scanned).
-- Result saved as data/raw/bigquery/supply_daily_<run date>.csv
SELECT block_date, MAX(block_height) AS last_block,
       ARRAY_AGG(total_supply ORDER BY block_height DESC LIMIT 1)[OFFSET(0)] / 1e24 AS total_supply_near
FROM `bigquery-public-data.crypto_near_mainnet_us.blocks`
WHERE block_date BETWEEN '2025-10-01' AND '2026-11-12'
GROUP BY 1 ORDER BY 1
