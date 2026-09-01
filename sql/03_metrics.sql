CREATE SCHEMA IF NOT EXISTS metrics;

-- Monthly base. Denominators are named explicitly because denominator choice
-- alone swings MoM change from +/-2% to +/-11% (see 04_forensics suspect G).
CREATE OR REPLACE VIEW metrics.monthly AS
WITH base AS (
    SELECT
        month,
        DATE_DIFF('day', month, month + INTERVAL 1 MONTH)   AS days_in_month,
        SUM(amount_recovered)                               AS recovered,
        COUNT(*) FILTER (WHERE payments_success > 0)         AS paying_accounts,
        COUNT(*) FILTER (WHERE was_worked)                   AS worked_accounts,
        COUNT(*) FILTER (WHERE was_targeted)                 AS targeted_accounts,
        COUNT(DISTINCT account_id)                           AS total_book,
        SUM(call_attempts)                                   AS attempts,
        SUM(connected_attempts)                              AS connected,
        SUM(dispositions)                                    AS dispositions,
        SUM(ptp_dispositions)                                AS ptp_dispositions,
        SUM(ptps_created)                                    AS ptps_created,
        SUM(ptps_kept)                                       AS ptps_kept
    FROM golden.account_month
    GROUP BY 1
),
sessions AS (
    SELECT month, SUM(session_hours) AS agent_hours
    FROM clean.agent_sessions GROUP BY 1
),
-- RPC computed inside call_dispositions only. Cross-table RPC exceeds 100%
-- because only 23% of dispositions sit on a call with a CONNECTED attempt.
rpc AS (
    SELECT month,
           COUNT(*) FILTER (WHERE disposition_code IN
               ('PTP','PROMISE_TO_PAY','PAID','REFUSED','DISPUTE','PTP_BROKEN')) AS rpc_dispositions,
           COUNT(*) AS all_dispositions
    FROM clean.call_dispositions GROUP BY 1
)
SELECT
    b.month,
    b.days_in_month,
    ROUND(b.recovered / 1e7, 2)                                   AS recovered_cr,
    ROUND(b.recovered / b.days_in_month / 1e7, 4)                 AS recovered_cr_per_day,
    b.paying_accounts,
    b.worked_accounts,
    b.targeted_accounts,
    ROUND(100.0 * b.connected / b.attempts, 2)                    AS contact_rate_pct,
    ROUND(100.0 * r.rpc_dispositions / r.all_dispositions, 2)     AS rpc_rate_pct,
    ROUND(100.0 * b.ptp_dispositions / b.dispositions, 2)         AS ptp_rate_pct,
    ROUND(100.0 * b.ptps_kept / b.ptps_created, 2)                AS ptp_kept_rate_pct,
    ROUND(100.0 * b.paying_accounts / b.worked_accounts, 2)       AS recovery_rate_per_worked_pct,
    ROUND(100.0 * b.paying_accounts / b.targeted_accounts, 2)     AS recovery_rate_per_targeted_pct,
    ROUND(100.0 * b.paying_accounts / b.total_book, 2)            AS recovery_rate_per_book_pct,
    ROUND(b.recovered / b.worked_accounts, 0)                     AS recovery_per_worked_account,
    ROUND(b.recovered / s.agent_hours, 0)                         AS recovery_per_agent_hour,
    NULL                                                          AS cost_per_rupee_recovered,
    NULL                                                          AS channel_conversion
FROM base b
LEFT JOIN sessions s ON s.month = b.month
LEFT JOIN rpc      r ON r.month = b.month
ORDER BY 1;

-- cost_per_rupee_recovered and channel_conversion are NULL by design:
--   no cost/spend/rate column exists in any of the 17 source tables
--   last-touch attribution reproduces channel volume share at ratio 0.98-1.01

CREATE OR REPLACE VIEW metrics.monthly_mom AS
SELECT
    month,
    ROUND(100.0 * (recovered_cr / LAG(recovered_cr) OVER (ORDER BY month) - 1), 2)
        AS recovered_mom_pct,
    ROUND(100.0 * (recovered_cr_per_day / LAG(recovered_cr_per_day) OVER (ORDER BY month) - 1), 2)
        AS recovered_per_day_mom_pct,
    ROUND(100.0 * (recovery_rate_per_worked_pct / LAG(recovery_rate_per_worked_pct) OVER (ORDER BY month) - 1), 2)
        AS rate_per_worked_mom_pct,
    ROUND(100.0 * (recovery_rate_per_book_pct / LAG(recovery_rate_per_book_pct) OVER (ORDER BY month) - 1), 2)
        AS rate_per_book_mom_pct,
    ROUND(100.0 * (recovery_per_agent_hour / LAG(recovery_per_agent_hour) OVER (ORDER BY month) - 1), 2)
        AS agent_hour_mom_pct
FROM metrics.monthly
ORDER BY 1;

CREATE OR REPLACE VIEW metrics.jan_to_jul_change AS
SELECT
    'recovered_cr' AS metric,
    ROUND(100.0 * (LAST(recovered_cr ORDER BY month) / FIRST(recovered_cr ORDER BY month) - 1), 2) AS pct_change
FROM metrics.monthly
UNION ALL SELECT 'recovered_per_day',
    ROUND(100.0 * (LAST(recovered_cr_per_day ORDER BY month) / FIRST(recovered_cr_per_day ORDER BY month) - 1), 2)
FROM metrics.monthly
UNION ALL SELECT 'contact_rate',
    ROUND(100.0 * (LAST(contact_rate_pct ORDER BY month) / FIRST(contact_rate_pct ORDER BY month) - 1), 2)
FROM metrics.monthly
UNION ALL SELECT 'rpc_rate',
    ROUND(100.0 * (LAST(rpc_rate_pct ORDER BY month) / FIRST(rpc_rate_pct ORDER BY month) - 1), 2)
FROM metrics.monthly
UNION ALL SELECT 'ptp_rate',
    ROUND(100.0 * (LAST(ptp_rate_pct ORDER BY month) / FIRST(ptp_rate_pct ORDER BY month) - 1), 2)
FROM metrics.monthly
UNION ALL SELECT 'ptp_kept_rate',
    ROUND(100.0 * (LAST(ptp_kept_rate_pct ORDER BY month) / FIRST(ptp_kept_rate_pct ORDER BY month) - 1), 2)
FROM metrics.monthly
UNION ALL SELECT 'recovery_rate_per_worked',
    ROUND(100.0 * (LAST(recovery_rate_per_worked_pct ORDER BY month) / FIRST(recovery_rate_per_worked_pct ORDER BY month) - 1), 2)
FROM metrics.monthly
UNION ALL SELECT 'recovery_per_agent_hour',
    ROUND(100.0 * (LAST(recovery_per_agent_hour ORDER BY month) / FIRST(recovery_per_agent_hour ORDER BY month) - 1), 2)
FROM metrics.monthly;