CREATE SCHEMA IF NOT EXISTS golden;

-- Grain: account_id x month. 30,000 x 7 = 210,000 rows.
-- Built from a cross join so untouched accounts still appear, making the
-- denominator an explicit filter downstream rather than an implicit join.
CREATE OR REPLACE TABLE golden.account_month AS

WITH spine AS (
    SELECT a.account_id, m.month
    FROM clean.accounts a
    CROSS JOIN raw.month_spine m
),
calls AS (
    SELECT account_id, month, COUNT(*) AS calls
    FROM clean.calls GROUP BY 1, 2
),
attempts AS (
    SELECT account_id, month,
           COUNT(*) AS call_attempts,
           COUNT(*) FILTER (WHERE attempt_status = 'CONNECTED') AS connected_attempts
    FROM clean.call_attempts GROUP BY 1, 2
),
dispositions AS (
    SELECT account_id, month,
           COUNT(*) AS dispositions,
           COUNT(*) FILTER (WHERE disposition_code IN ('PTP','PROMISE_TO_PAY')) AS ptp_dispositions
    FROM clean.call_dispositions GROUP BY 1, 2
),
whatsapp AS (
    SELECT account_id, month, COUNT(*) AS whatsapp_events
    FROM clean.whatsapp_events GROUP BY 1, 2
),
sms AS (
    SELECT account_id, month, COUNT(*) AS sms_events
    FROM clean.sms_events GROUP BY 1, 2
),
field AS (
    SELECT account_id, month, COUNT(*) AS field_visits
    FROM clean.field_visits GROUP BY 1, 2
),
ptp AS (
    SELECT account_id, month,
           COUNT(*) AS ptps_created,
           COUNT(*) FILTER (WHERE status = 'KEPT') AS ptps_kept
    FROM clean.promises_to_pay GROUP BY 1, 2
),
targeting AS (
    SELECT account_id, month,
           COUNT(*) AS targeted,
           COUNT(*) FILTER (WHERE status = 'CONTACTED') AS targeted_contacted,
           COUNT(*) FILTER (WHERE status = 'SKIPPED')   AS targeted_skipped
    FROM clean.daily_targeting GROUP BY 1, 2
),
pay AS (
    SELECT account_id, month,
           COUNT(*)    AS payments_success,
           SUM(amount) AS amount_recovered
    FROM clean.payments_success GROUP BY 1, 2
),
exits AS (
    SELECT account_id, MIN(month) AS exit_month
    FROM clean.account_status_history
    WHERE status IN ('CLOSED', 'WRITEOFF', 'NPA')
    GROUP BY 1
)

SELECT
    s.account_id,
    s.month,
    a.dpd,
    a.risk_segment,
    a.loan_type,
    a.outstanding_amount,
    COALESCE(c.calls, 0)              AS calls,
    COALESCE(t.call_attempts, 0)      AS call_attempts,
    COALESCE(t.connected_attempts, 0) AS connected_attempts,
    COALESCE(d.dispositions, 0)       AS dispositions,
    COALESCE(d.ptp_dispositions, 0)   AS ptp_dispositions,
    COALESCE(w.whatsapp_events, 0)    AS whatsapp_events,
    COALESCE(sm.sms_events, 0)        AS sms_events,
    COALESCE(f.field_visits, 0)       AS field_visits,
    COALESCE(p.ptps_created, 0)       AS ptps_created,
    COALESCE(p.ptps_kept, 0)          AS ptps_kept,
    COALESCE(g.targeted, 0)           AS targeted,
    COALESCE(g.targeted_contacted, 0) AS targeted_contacted,
    COALESCE(g.targeted_skipped, 0)   AS targeted_skipped,
    COALESCE(pm.payments_success, 0)  AS payments_success,
    COALESCE(pm.amount_recovered, 0)  AS amount_recovered,
    (COALESCE(c.calls,0) + COALESCE(w.whatsapp_events,0)
     + COALESCE(sm.sms_events,0) + COALESCE(f.field_visits,0)) > 0 AS was_worked,
    COALESCE(g.targeted, 0) > 0                                     AS was_targeted,
    e.exit_month,
    (e.exit_month IS NOT NULL AND s.month >= e.exit_month)          AS has_exited

FROM spine s
LEFT JOIN clean.accounts a ON a.account_id = s.account_id
LEFT JOIN calls        c  ON c.account_id  = s.account_id AND c.month  = s.month
LEFT JOIN attempts     t  ON t.account_id  = s.account_id AND t.month  = s.month
LEFT JOIN dispositions d  ON d.account_id  = s.account_id AND d.month  = s.month
LEFT JOIN whatsapp     w  ON w.account_id  = s.account_id AND w.month  = s.month
LEFT JOIN sms          sm ON sm.account_id = s.account_id AND sm.month = s.month
LEFT JOIN field        f  ON f.account_id  = s.account_id AND f.month  = s.month
LEFT JOIN ptp          p  ON p.account_id  = s.account_id AND p.month  = s.month
LEFT JOIN targeting    g  ON g.account_id  = s.account_id AND g.month  = s.month
LEFT JOIN pay          pm ON pm.account_id = s.account_id AND pm.month = s.month
LEFT JOIN exits        e  ON e.account_id  = s.account_id;

-- Build-time data contracts. Any FAIL is a build failure.
CREATE OR REPLACE VIEW golden.contract_checks AS
SELECT 'row_count_is_210000' AS check_name,
       CASE WHEN COUNT(*) = 210000 THEN 'PASS' ELSE 'FAIL' END AS status,
       COUNT(*)::VARCHAR AS observed
FROM golden.account_month
UNION ALL
SELECT 'primary_key_unique',
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END, COUNT(*)::VARCHAR
FROM (SELECT account_id, month FROM golden.account_month
      GROUP BY 1,2 HAVING COUNT(*) > 1)
UNION ALL
SELECT 'all_accounts_present',
       CASE WHEN COUNT(DISTINCT account_id) = 30000 THEN 'PASS' ELSE 'FAIL' END,
       COUNT(DISTINCT account_id)::VARCHAR
FROM golden.account_month
UNION ALL
SELECT 'seven_months_present',
       CASE WHEN COUNT(DISTINCT month) = 7 THEN 'PASS' ELSE 'FAIL' END,
       COUNT(DISTINCT month)::VARCHAR
FROM golden.account_month
UNION ALL
SELECT 'no_negative_amounts',
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END, COUNT(*)::VARCHAR
FROM golden.account_month WHERE amount_recovered < 0
UNION ALL
SELECT 'no_null_attributes',
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END, COUNT(*)::VARCHAR
FROM golden.account_month WHERE dpd IS NULL OR risk_segment IS NULL
UNION ALL
SELECT 'recovery_reconciles_to_source',
       CASE WHEN ABS((SELECT SUM(amount_recovered) FROM golden.account_month)
                   - (SELECT SUM(amount) FROM clean.payments_success)) < 1
            THEN 'PASS' ELSE 'FAIL' END,
       ROUND((SELECT SUM(amount_recovered) FROM golden.account_month) / 1e7, 2)::VARCHAR || ' Cr';
