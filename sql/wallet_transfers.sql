-- Every NEAR transfer into the three revenue wallets since the fee switch, by day and sender.
-- Heavy: about 852 GB scanned (the args column), most of the sandbox's free monthly terabyte.
-- Result saved as data/raw/bigquery/wallet_transfers_<run date>.csv
SELECT block_date, receipt_receiver_account_id AS wallet, receipt_predecessor_account_id AS sender,
       COUNT(*) AS transfers,
       SUM(SAFE_CAST(JSON_VALUE(args, '$.deposit') AS BIGNUMERIC)) / 1e24 AS near_in
FROM `bigquery-public-data.crypto_near_mainnet_us.receipt_actions`
WHERE block_date BETWEEN '2026-02-23' AND '2026-11-12'
  AND action_kind = 'TRANSFER'
  AND receipt_receiver_account_id IN ('buybacks.multisignature.near', 'fefundsadmin.sputnik-dao.near',
                                      '1csfundsadmin.sputnik-dao.near')
GROUP BY 1, 2, 3 ORDER BY 1, 2, 3
