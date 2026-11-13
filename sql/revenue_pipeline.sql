-- How NEAR's revenue reaches its three revenue wallets from inside intents.near (exploratory, not part of make).
-- 1) Who withdraws NEAR to the wallets (native_withdraw intents), Aug-Nov 2026.
WITH l AS (
  SELECT block_date, l.element AS log
  FROM `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes`, UNNEST(logs.list) l
  WHERE block_date BETWEEN '2026-08-01' AND '2026-11-12' AND executor_account_id = 'intents.near'
    AND l.element LIKE '%withdraw%'
    AND (l.element LIKE '%buybacks.multisignature.near%' OR l.element LIKE '%fefundsadmin.sputnik-dao.near%'
         OR l.element LIKE '%1csfundsadmin.sputnik-dao.near%')
)
SELECT JSON_VALUE(d, '$.account_id') AS account, JSON_VALUE(d, '$.receiver_id') AS wallet, COUNT(*) AS n,
       SUM(CAST(JSON_VALUE(d, '$.amount') AS BIGNUMERIC)) / 1e24 AS near, MIN(block_date) AS first_day, MAX(block_date) AS last_day
FROM l, UNNEST(JSON_QUERY_ARRAY(SUBSTR(log, 12), '$.data')) d
WHERE JSON_VALUE(d, '$.receiver_id') IN ('buybacks.multisignature.near', 'fefundsadmin.sputnik-dao.near', '1csfundsadmin.sputnik-dao.near')
GROUP BY 1, 2 ORDER BY near DESC;

-- 2) What the main accrual account (5880ad...) receives, 6-12 Nov 2026, by token (priced afterwards with the 1Click token list).
WITH l AS (
  SELECT l.element AS log
  FROM `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes`, UNNEST(logs.list) l
  WHERE block_date BETWEEN '2026-11-06' AND '2026-11-12' AND executor_account_id = 'intents.near'
    AND l.element LIKE '%mt_transfer%' AND l.element LIKE '%5880ad2b362620fadf759cbceb1cd5737ce8c6ed7fb8e9942881e6731f9247dd%'
)
SELECT JSON_VALUE_ARRAY(d, '$.token_ids')[OFFSET(0)] AS token, COUNT(*) AS n,
       SUM(CAST(JSON_VALUE_ARRAY(d, '$.amounts')[OFFSET(0)] AS BIGNUMERIC)) AS amount
FROM l, UNNEST(JSON_QUERY_ARRAY(SUBSTR(log, 12), '$.data')) d
WHERE JSON_VALUE(d, '$.new_owner_id') = '5880ad2b362620fadf759cbceb1cd5737ce8c6ed7fb8e9942881e6731f9247dd'
GROUP BY 1 ORDER BY n DESC;
