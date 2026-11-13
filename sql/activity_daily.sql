-- NEAR public dataset on BigQuery (free sandbox is enough; about 44 GB scanned).
-- Result saved as data/raw/bigquery/activity_daily_<run date>.csv
SELECT block_date, COUNT(*) AS transactions, COUNT(DISTINCT signer_account_id) AS signers,
       COUNTIF(receiver_account_id = 'intents.near') AS tx_to_intents
FROM `bigquery-public-data.crypto_near_mainnet_us.transactions`
WHERE block_date BETWEEN '2025-10-01' AND '2026-11-12'
GROUP BY 1 ORDER BY 1
