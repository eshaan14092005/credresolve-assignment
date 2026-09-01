CREATE SCHEMA IF NOT EXISTS raw;

CREATE OR REPLACE VIEW raw.accounts               AS SELECT * FROM read_csv_auto('data/raw/accounts.csv');
CREATE OR REPLACE VIEW raw.borrowers              AS SELECT * FROM read_csv_auto('data/raw/borrowers.csv');
CREATE OR REPLACE VIEW raw.agents                 AS SELECT * FROM read_csv_auto('data/raw/agents.csv');
CREATE OR REPLACE VIEW raw.agent_sessions         AS SELECT * FROM read_csv_auto('data/raw/agent_sessions.csv');
CREATE OR REPLACE VIEW raw.campaigns              AS SELECT * FROM read_csv_auto('data/raw/campaigns.csv');
CREATE OR REPLACE VIEW raw.daily_targeting        AS SELECT * FROM read_csv_auto('data/raw/daily_targeting.csv');
CREATE OR REPLACE VIEW raw.calls                  AS SELECT * FROM read_csv_auto('data/raw/calls.csv');
CREATE OR REPLACE VIEW raw.call_attempts          AS SELECT * FROM read_csv_auto('data/raw/call_attempts.csv');
CREATE OR REPLACE VIEW raw.call_dispositions      AS SELECT * FROM read_csv_auto('data/raw/call_dispositions.csv');
CREATE OR REPLACE VIEW raw.whatsapp_events        AS SELECT * FROM read_csv_auto('data/raw/whatsapp_events.csv');
CREATE OR REPLACE VIEW raw.sms_events             AS SELECT * FROM read_csv_auto('data/raw/sms_events.csv');
CREATE OR REPLACE VIEW raw.field_visits           AS SELECT * FROM read_csv_auto('data/raw/field_visits.csv');
CREATE OR REPLACE VIEW raw.promises_to_pay        AS SELECT * FROM read_csv_auto('data/raw/promises_to_pay.csv');
CREATE OR REPLACE VIEW raw.payments               AS SELECT * FROM read_csv_auto('data/raw/payments.csv');
CREATE OR REPLACE VIEW raw.vendor_telephony       AS SELECT * FROM read_csv_auto('data/raw/vendor_telephony.csv');
CREATE OR REPLACE VIEW raw.complaints             AS SELECT * FROM read_csv_auto('data/raw/complaints.csv');
CREATE OR REPLACE VIEW raw.account_status_history AS SELECT * FROM read_csv_auto('data/raw/account_status_history.csv');

-- D2: window is Jan-Jul 2026 (7 complete months, 6 MoM transitions)
CREATE OR REPLACE VIEW raw.analysis_window AS
SELECT DATE '2026-01-01' AS window_start,
       DATE '2026-08-01' AS window_end_exclusive,
       7 AS complete_months,
       6 AS mom_transitions;

CREATE OR REPLACE VIEW raw.month_spine AS
SELECT DISTINCT DATE_TRUNC('month', d) AS month
FROM (SELECT UNNEST(GENERATE_SERIES(DATE '2026-01-01', DATE '2026-07-31', INTERVAL 1 DAY)) AS d);
