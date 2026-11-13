-- Transactions to intents.near: who signs them, over three 12-day windows.
-- NEAR public dataset on BigQuery. Result saved as data/raw/bigquery/intents_signers_<run date>.csv
-- (aggregates only: no account is saved).
SELECT CASE WHEN block_date BETWEEN '2026-10-01' AND '2026-10-12' THEN 'oct01_12'
            WHEN block_date BETWEEN '2026-10-20' AND '2026-10-31' THEN 'oct20_31'
            ELSE 'nov01_12' END AS period,
       COUNT(*) AS txns,
       COUNTIF(signer_account_id = 'intents.near') AS by_intents_near,
       COUNTIF(signer_account_id = 'escrow.ai.near') AS by_escrow_ai,
       COUNT(DISTINCT signer_account_id) AS signers,
       COUNT(DISTINCT IF(signer_account_id NOT IN ('intents.near', 'escrow.ai.near'), signer_account_id, NULL)) AS other_signers,
       COUNTIF(signer_account_id NOT IN ('intents.near', 'escrow.ai.near')) AS by_others
FROM `bigquery-public-data.crypto_near_mainnet_us.transactions`
WHERE receiver_account_id = 'intents.near'
  AND (block_date BETWEEN '2026-10-01' AND '2026-10-12' OR block_date BETWEEN '2026-10-20' AND '2026-10-31'
       OR block_date BETWEEN '2026-11-01' AND '2026-11-12')
GROUP BY 1 ORDER BY 1
