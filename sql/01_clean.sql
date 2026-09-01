CREATE SCHEMA IF NOT EXISTS clean;

-- D1: account_id is the spine (borrower_id has orphans in every table)
CREATE OR REPLACE VIEW clean.accounts AS
SELECT account_id, borrower_id, dpd, risk_segment, loan_type,
       outstanding_amount, opened_at
FROM raw.accounts;

-- D14: latest updated_at wins
CREATE OR REPLACE VIEW clean.borrowers AS
SELECT * EXCLUDE (rn) FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY borrower_id ORDER BY updated_at DESC) AS rn
    FROM raw.borrowers
) WHERE rn = 1;

-- D6: agents rejected as a dimension; agent_id is an opaque key only
CREATE OR REPLACE VIEW clean.agent_keys AS
SELECT DISTINCT agent_id FROM raw.agents;

-- D7: vendor resolved via event tables, not via agents
CREATE OR REPLACE VIEW clean.vendors AS
SELECT vendor_id, vendor_name, schema_version FROM raw.vendor_telephony;

CREATE OR REPLACE VIEW clean.campaigns AS
SELECT campaign_id, campaign_name, channel, strategy_version,
       target_definition, start_at, end_at
FROM raw.campaigns;

-- D3/D5: dedup on payment_id, prefer the row with a reference
-- D4: do NOT dedup on payment_reference (collisions are random)
CREATE OR REPLACE VIEW clean.payments AS
SELECT * EXCLUDE (rn) FROM (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY payment_id
               ORDER BY CASE WHEN payment_reference IS NULL THEN 1 ELSE 0 END
           ) AS rn
    FROM raw.payments
) WHERE rn = 1;

CREATE OR REPLACE VIEW clean.payments_success AS
SELECT *, DATE_TRUNC('month', event_at) AS month
FROM clean.payments
WHERE payment_status = 'SUCCESS'
  AND event_at >= DATE '2026-01-01'
  AND event_at <  DATE '2026-08-01';

-- D8: no timezone conversion (hour-of-day is uniform; nothing to align to)
CREATE OR REPLACE VIEW clean.calls AS
SELECT DISTINCT *, DATE_TRUNC('month', event_at) AS month FROM raw.calls
WHERE event_at >= DATE '2026-01-01' AND event_at < DATE '2026-08-01';

CREATE OR REPLACE VIEW clean.call_attempts AS
SELECT DISTINCT *, DATE_TRUNC('month', event_at) AS month FROM raw.call_attempts
WHERE event_at >= DATE '2026-01-01' AND event_at < DATE '2026-08-01';

CREATE OR REPLACE VIEW clean.call_dispositions AS
SELECT DISTINCT *, DATE_TRUNC('month', event_at) AS month FROM raw.call_dispositions
WHERE event_at >= DATE '2026-01-01' AND event_at < DATE '2026-08-01';

CREATE OR REPLACE VIEW clean.whatsapp_events AS
SELECT DISTINCT *, DATE_TRUNC('month', event_at) AS month FROM raw.whatsapp_events
WHERE event_at >= DATE '2026-01-01' AND event_at < DATE '2026-08-01';

CREATE OR REPLACE VIEW clean.sms_events AS
SELECT DISTINCT *, DATE_TRUNC('month', event_at) AS month FROM raw.sms_events
WHERE event_at >= DATE '2026-01-01' AND event_at < DATE '2026-08-01';

CREATE OR REPLACE VIEW clean.field_visits AS
SELECT DISTINCT *, DATE_TRUNC('month', event_at) AS month FROM raw.field_visits
WHERE event_at >= DATE '2026-01-01' AND event_at < DATE '2026-08-01';

CREATE OR REPLACE VIEW clean.account_status_history AS
SELECT DISTINCT *, DATE_TRUNC('month', event_at) AS month FROM raw.account_status_history
WHERE event_at >= DATE '2026-01-01' AND event_at < DATE '2026-08-01';

CREATE OR REPLACE VIEW clean.daily_targeting AS
SELECT DISTINCT *, DATE_TRUNC('month', target_date) AS month FROM raw.daily_targeting
WHERE target_date >= DATE '2026-01-01' AND target_date < DATE '2026-08-01';

CREATE OR REPLACE VIEW clean.agent_sessions AS
SELECT DISTINCT *,
       DATE_TRUNC('month', login_at) AS month,
       DATE_DIFF('second', login_at, logout_at) / 3600.0 AS session_hours
FROM raw.agent_sessions
WHERE login_at >= DATE '2026-01-01' AND login_at < DATE '2026-08-01';

CREATE OR REPLACE VIEW clean.promises_to_pay AS
SELECT DISTINCT *, DATE_TRUNC('month', event_at) AS month FROM raw.promises_to_pay
WHERE event_at >= DATE '2026-01-01' AND event_at < DATE '2026-08-01';

-- D11: PTP and PROMISE_TO_PAY are the same concept
CREATE OR REPLACE VIEW clean.ptp_dispositions AS
SELECT * FROM clean.call_dispositions
WHERE disposition_code IN ('PTP', 'PROMISE_TO_PAY');

CREATE OR REPLACE VIEW clean.waterfall AS
SELECT 'accounts' AS table_name, (SELECT COUNT(*) FROM raw.accounts) AS raw_rows,
       (SELECT COUNT(*) FROM clean.accounts) AS kept_rows, 'D1' AS rule
UNION ALL SELECT 'borrowers', (SELECT COUNT(*) FROM raw.borrowers),
       (SELECT COUNT(*) FROM clean.borrowers), 'D14'
UNION ALL SELECT 'payments (dedup)', (SELECT COUNT(*) FROM raw.payments),
       (SELECT COUNT(*) FROM clean.payments), 'D3/D5'
UNION ALL SELECT 'payments (window)', (SELECT COUNT(*) FROM clean.payments),
       (SELECT COUNT(*) FROM clean.payments WHERE event_at >= DATE '2026-01-01' AND event_at < DATE '2026-08-01'), 'D2'
UNION ALL SELECT 'payments (SUCCESS)',
       (SELECT COUNT(*) FROM clean.payments WHERE event_at >= DATE '2026-01-01' AND event_at < DATE '2026-08-01'),
       (SELECT COUNT(*) FROM clean.payments_success), 'SUCCESS only'
UNION ALL SELECT 'calls', (SELECT COUNT(*) FROM raw.calls),
       (SELECT COUNT(*) FROM clean.calls), 'dedup + D2'
UNION ALL SELECT 'call_attempts', (SELECT COUNT(*) FROM raw.call_attempts),
       (SELECT COUNT(*) FROM clean.call_attempts), 'dedup + D2'
UNION ALL SELECT 'call_dispositions', (SELECT COUNT(*) FROM raw.call_dispositions),
       (SELECT COUNT(*) FROM clean.call_dispositions), 'dedup + D2'
UNION ALL SELECT 'whatsapp_events', (SELECT COUNT(*) FROM raw.whatsapp_events),
       (SELECT COUNT(*) FROM clean.whatsapp_events), 'dedup + D2'
UNION ALL SELECT 'sms_events', (SELECT COUNT(*) FROM raw.sms_events),
       (SELECT COUNT(*) FROM clean.sms_events), 'dedup + D2'
UNION ALL SELECT 'field_visits', (SELECT COUNT(*) FROM raw.field_visits),
       (SELECT COUNT(*) FROM clean.field_visits), 'dedup + D2'
UNION ALL SELECT 'daily_targeting', (SELECT COUNT(*) FROM raw.daily_targeting),
       (SELECT COUNT(*) FROM clean.daily_targeting), 'dedup + D2'
UNION ALL SELECT 'promises_to_pay', (SELECT COUNT(*) FROM raw.promises_to_pay),
       (SELECT COUNT(*) FROM clean.promises_to_pay), 'dedup + D2';