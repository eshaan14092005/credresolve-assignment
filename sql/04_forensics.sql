CREATE SCHEMA IF NOT EXISTS forensics;

-- Suspect A: duplicate payments. Three mechanisms tested independently.
CREATE OR REPLACE VIEW forensics.a_duplicate_payments AS
SELECT 'L1 same payment_id' AS test,
       COUNT(*) AS excess_rows,
       ROUND(SUM(CASE WHEN payment_status='SUCCESS' THEN amount ELSE 0 END)/1e7, 2) AS success_cr,
       'CONFIRMED' AS verdict
FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY payment_id
        ORDER BY CASE WHEN payment_reference IS NULL THEN 1 ELSE 0 END) AS rn
      FROM raw.payments) WHERE rn > 1
UNION ALL
SELECT 'L2 same payment_reference',
       COUNT(*),
       ROUND(SUM(CASE WHEN payment_status='SUCCESS' THEN amount ELSE 0 END)/1e7, 2),
       'REJECTED - random collision'
FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY payment_reference ORDER BY payment_id) AS rn
      FROM clean.payments WHERE payment_reference IS NOT NULL) WHERE rn > 1;

-- L2 rejection evidence: if these were gateway retries, account and amount
-- would match within a reference group. They never do.
CREATE OR REPLACE VIEW forensics.a_reference_is_not_a_key AS
SELECT COUNT(*) AS collision_groups,
       COUNT(*) FILTER (WHERE n_accounts > 1) AS groups_with_differing_account,
       COUNT(*) FILTER (WHERE n_amounts  > 1) AS groups_with_differing_amount
FROM (SELECT payment_reference,
             COUNT(DISTINCT account_id) AS n_accounts,
             COUNT(DISTINCT amount)     AS n_amounts
      FROM clean.payments WHERE payment_reference IS NOT NULL
      GROUP BY 1 HAVING COUNT(*) > 1);

-- Birthday-paradox test: observed distinct references vs expected under
-- random draws from the TXN pool.
CREATE OR REPLACE VIEW forensics.a_birthday_test AS
WITH p AS (
    SELECT COUNT(*) AS draws,
           COUNT(DISTINCT payment_reference) AS observed_distinct,
           MAX(CAST(REGEXP_EXTRACT(payment_reference, '\d+') AS BIGINT)) AS pool
    FROM clean.payments WHERE payment_reference IS NOT NULL
)
SELECT draws, pool, observed_distinct,
       ROUND(pool * (1 - POWER(1 - 1.0/pool, draws)), 0) AS expected_distinct
FROM p;

-- Suspect C: timezone. Hour-of-day distribution per timezone label.
CREATE OR REPLACE VIEW forensics.c_hour_distribution AS
SELECT timezone,
       ROUND(MIN(pct), 2) AS min_hour_share_pct,
       ROUND(MAX(pct), 2) AS max_hour_share_pct,
       ROUND(4.1667, 2)   AS uniform_expectation_pct
FROM (SELECT timezone, EXTRACT(hour FROM event_at) AS hr,
             100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY timezone) AS pct
      FROM clean.calls GROUP BY 1, 2)
GROUP BY 1;

-- Suspect D: disposition code drift across schema versions.
CREATE OR REPLACE VIEW forensics.d_version_share_by_month AS
SELECT month, disposition_version,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY month), 1) AS share_pct
FROM clean.call_dispositions GROUP BY 1, 2 ORDER BY 1, 2;

CREATE OR REPLACE VIEW forensics.d_code_vocabulary_by_version AS
SELECT disposition_version, disposition_code, COUNT(*) AS n
FROM clean.call_dispositions GROUP BY 1, 2 ORDER BY 1, 2;

-- Suspect E: agent identity. joined_at must be immutable for a valid SCD.
CREATE OR REPLACE VIEW forensics.e_agent_identity AS
SELECT COUNT(*) AS agent_ids,
       COUNT(*) FILTER (WHERE n_joined > 1) AS with_conflicting_joined_at,
       ROUND(AVG(n_rows), 1) AS avg_rows_per_agent,
       ROUND(AVG(n_emp), 1)  AS avg_employee_codes_per_agent
FROM (SELECT agent_id, COUNT(*) AS n_rows,
             COUNT(DISTINCT joined_at) AS n_joined,
             COUNT(DISTINCT employee_code) AS n_emp
      FROM raw.agents GROUP BY 1);

-- Suspect F: portfolio mix of the worked population.
CREATE OR REPLACE VIEW forensics.f_portfolio_mix AS
SELECT month,
       COUNT(*) FILTER (WHERE was_worked) AS worked_accounts,
       ROUND(AVG(dpd) FILTER (WHERE was_worked), 1) AS mean_dpd,
       ROUND(AVG(outstanding_amount) FILTER (WHERE was_worked), 0) AS mean_outstanding
FROM golden.account_month GROUP BY 1 ORDER BY 1;

CREATE OR REPLACE VIEW forensics.f_risk_mix AS
SELECT month, risk_segment,
       ROUND(100.0 * COUNT(*) FILTER (WHERE was_worked)
             / SUM(COUNT(*) FILTER (WHERE was_worked)) OVER (PARTITION BY month), 1) AS share_pct
FROM golden.account_month GROUP BY 1, 2 ORDER BY 1, 2;

-- Suspect G: denominator manipulation via account attrition.
CREATE OR REPLACE VIEW forensics.g_exit_rate AS
SELECT month,
       COUNT(*) AS transitions,
       ROUND(100.0 * COUNT(*) FILTER (WHERE status IN ('CLOSED','WRITEOFF','NPA')) / COUNT(*), 2)
           AS exit_share_pct
FROM clean.account_status_history GROUP BY 1 ORDER BY 1;

-- Grain mismatch: three incompatible definitions of "contact".
CREATE OR REPLACE VIEW forensics.h_contact_grain_mismatch AS
SELECT
    (SELECT COUNT(DISTINCT call_id) FROM raw.call_attempts WHERE attempt_status='CONNECTED')
        AS calls_with_connected_attempt,
    (SELECT COUNT(*) FROM (SELECT DISTINCT * FROM raw.calls) WHERE call_status='ANSWERED')
        AS calls_marked_answered,
    (SELECT COUNT(DISTINCT call_id) FROM raw.call_dispositions)
        AS calls_with_a_disposition,
    (SELECT COUNT(*) FROM raw.call_dispositions d
     WHERE d.call_id IN (SELECT call_id FROM raw.call_attempts WHERE attempt_status='CONNECTED'))
        AS dispositions_on_a_connected_call,
    (SELECT COUNT(*) FROM raw.call_dispositions) AS total_dispositions;