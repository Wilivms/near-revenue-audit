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

-- 3) Every recurring destination of the 1Click settlement account (51e8f94d...), 6-12 Nov 2026.
--    Its balance (RPC view intents.near mt_tokens_for_owner + mt_batch_balance_of, 13 Nov 2026): about $136M over
--    205 tokens, the size of NEAR's confidential TVL ($137.9M on 12 Nov, revenue.near.org): the confidential pool.
WITH l AS (
  SELECT block_date, l.element AS log
  FROM `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes`, UNNEST(logs.list) l
  WHERE block_date BETWEEN '2026-11-06' AND '2026-11-12' AND executor_account_id = 'intents.near'
    AND l.element LIKE '%mt_transfer%' AND l.element LIKE '%51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe%'
)
SELECT JSON_VALUE(d, '$.new_owner_id') AS destination, COUNT(*) AS n, COUNT(DISTINCT block_date) AS days
FROM l, UNNEST(JSON_QUERY_ARRAY(SUBSTR(log, 12), '$.data')) d
WHERE JSON_VALUE(d, '$.old_owner_id') = '51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe'
GROUP BY 1 HAVING n >= 5 ORDER BY n DESC;

-- 4) Of the NEAR withdrawn to the two wallets, how much came through accounts the confidential pool funded? 1 Oct - 12 Nov 2026.
--    Result: buyback multisig 258,645 of 421,748 NEAR (734 accounts); front-end fund 200,869 of 202,120 (525): 74% overall.
WITH l AS (
  SELECT block_date, l.element AS log
  FROM `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes`, UNNEST(logs.list) l
  WHERE block_date BETWEEN '2026-10-01' AND '2026-11-12' AND executor_account_id = 'intents.near'
    AND (l.element LIKE '%native_withdraw%' OR l.element LIKE '%51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe%')
), w AS (
  SELECT JSON_VALUE(d, '$.account_id') AS acct, JSON_VALUE(d, '$.receiver_id') AS wallet, CAST(JSON_VALUE(d, '$.amount') AS BIGNUMERIC) / 1e24 AS near
  FROM l, UNNEST(JSON_QUERY_ARRAY(SUBSTR(log, 12), '$.data')) d
  WHERE JSON_VALUE(SUBSTR(log, 12), '$.event') = 'native_withdraw'
    AND JSON_VALUE(d, '$.receiver_id') IN ('buybacks.multisignature.near', 'fefundsadmin.sputnik-dao.near')
), fp AS (
  SELECT DISTINCT JSON_VALUE(d, '$.new_owner_id') AS acct
  FROM l, UNNEST(JSON_QUERY_ARRAY(SUBSTR(log, 12), '$.data')) d
  WHERE JSON_VALUE(SUBSTR(log, 12), '$.event') = 'mt_transfer'
    AND JSON_VALUE(d, '$.old_owner_id') = '51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe'
)
SELECT wallet, fp.acct IS NOT NULL AS funded_by_pool, COUNT(DISTINCT w.acct) AS accounts, COUNT(*) AS withdrawals, SUM(near) AS near
FROM w LEFT JOIN fp USING (acct) GROUP BY 1, 2 ORDER BY 1, 2;
