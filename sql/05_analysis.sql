CREATE SCHEMA IF NOT EXISTS analysis;

-- Reconstruction of the 11% claim: every numerator x denominator x transition.
CREATE OR REPLACE VIEW analysis.definition_space AS
WITH defs AS (
    SELECT month, 'recovered_rs'      AS numerator, recovered_cr          AS num FROM metrics.monthly
    UNION ALL SELECT month, 'payers',              paying_accounts        FROM metrics.monthly
    UNION ALL SELECT month, 'recovered_per_day',   recovered_cr_per_day   FROM metrics.monthly
),
dens AS (
    SELECT month, 'none_absolute'  AS denominator, 1.0                    AS den FROM metrics.monthly
    UNION ALL SELECT month, 'per_worked',    worked_accounts::DOUBLE      FROM metrics.monthly
    UNION ALL SELECT month, 'per_targeted',  targeted_accounts::DOUBLE    FROM metrics.monthly
    UNION ALL SELECT month, 'per_total_book', 30000.0                     FROM metrics.monthly
),
combos AS (
    SELECT d.month, d.numerator, n.denominator, d.num / n.den AS value
    FROM defs d JOIN dens n ON n.month = d.month
)
SELECT numerator, denominator, month,
       ROUND(100.0 * (value / LAG(value) OVER (PARTITION BY numerator, denominator ORDER BY month) - 1), 2)
           AS mom_pct
FROM combos ORDER BY 1, 2, 3;

-- Which definitions reach the claimed +11%?
CREATE OR REPLACE VIEW analysis.combinations_hitting_11pct AS
SELECT * FROM analysis.definition_space
WHERE mom_pct >= 10 ORDER BY mom_pct DESC;

-- Does any definition sustain 11% as an average?
CREATE OR REPLACE VIEW analysis.mean_mom_by_definition AS
SELECT numerator, denominator,
       ROUND(AVG(mom_pct), 2) AS mean_mom_pct,
       ROUND(MIN(mom_pct), 2) AS min_mom_pct,
       ROUND(MAX(mom_pct), 2) AS max_mom_pct
FROM analysis.definition_space WHERE mom_pct IS NOT NULL
GROUP BY 1, 2 ORDER BY 3 DESC;

-- The verdict, stated as arithmetic.
CREATE OR REPLACE VIEW analysis.verdict AS
SELECT
    (SELECT COUNT(*) FROM analysis.definition_space WHERE mom_pct IS NOT NULL) AS combinations_tested,
    (SELECT COUNT(*) FROM analysis.combinations_hitting_11pct)                 AS combinations_over_10pct,
    (SELECT ROUND(MIN(mean_mom_pct), 2) FROM analysis.mean_mom_by_definition)  AS worst_mean_mom_pct,
    (SELECT ROUND(MAX(mean_mom_pct), 2) FROM analysis.mean_mom_by_definition)  AS best_mean_mom_pct,
    ROUND(100 * (POWER(1.11, 6) - 1), 0)                                       AS claimed_11pct_implies_pct,
    (SELECT pct_change FROM metrics.jan_to_jul_change WHERE metric='recovered_cr') AS actual_jan_to_jul_pct;

-- Calendar-length explanation for the Feb->Mar jump.
CREATE OR REPLACE VIEW analysis.calendar_effect AS
SELECT month, days_in_month, recovered_cr, recovered_cr_per_day,
       ROUND(100.0 * (recovered_cr / LAG(recovered_cr) OVER (ORDER BY month) - 1), 2)
           AS absolute_mom_pct,
       ROUND(100.0 * (recovered_cr_per_day / LAG(recovered_cr_per_day) OVER (ORDER BY month) - 1), 2)
           AS per_day_mom_pct,
       ROUND(100.0 * (days_in_month::DOUBLE / LAG(days_in_month) OVER (ORDER BY month) - 1), 2)
           AS days_mom_pct
FROM metrics.monthly ORDER BY 1;

-- Driver dimensions vs a binomial noise floor.
CREATE OR REPLACE VIEW analysis.driver_dimensions AS
WITH acct AS (
    SELECT account_id, ANY_VALUE(dpd) AS dpd, ANY_VALUE(risk_segment) AS risk_segment,
           ANY_VALUE(loan_type) AS loan_type,
           SUM(payments_success) > 0 AS paid
    FROM golden.account_month GROUP BY 1
),
base AS (SELECT AVG(CASE WHEN paid THEN 1.0 ELSE 0.0 END) AS p FROM acct)
SELECT 'risk_segment' AS dimension,
       ROUND(MAX(pay_rate) - MIN(pay_rate), 2) AS spread_pp,
       ROUND(2 * 100 * SQRT((SELECT p FROM base) * (1-(SELECT p FROM base)) / MEDIAN(n)), 2) AS noise_floor_pp
FROM (SELECT risk_segment, COUNT(*) AS n,
             100.0*AVG(CASE WHEN paid THEN 1.0 ELSE 0.0 END) AS pay_rate
      FROM acct GROUP BY 1)
UNION ALL
SELECT 'loan_type',
       ROUND(MAX(pay_rate) - MIN(pay_rate), 2),
       ROUND(2 * 100 * SQRT((SELECT p FROM base) * (1-(SELECT p FROM base)) / MEDIAN(n)), 2)
FROM (SELECT loan_type, COUNT(*) AS n,
             100.0*AVG(CASE WHEN paid THEN 1.0 ELSE 0.0 END) AS pay_rate
      FROM acct GROUP BY 1)
UNION ALL
SELECT 'dpd',
       ROUND(MAX(pay_rate) - MIN(pay_rate), 2),
       ROUND(2 * 100 * SQRT((SELECT p FROM base) * (1-(SELECT p FROM base)) / MEDIAN(n)), 2)
FROM (SELECT dpd, COUNT(*) AS n,
             100.0*AVG(CASE WHEN paid THEN 1.0 ELSE 0.0 END) AS pay_rate
      FROM acct GROUP BY 1);

-- Part 4 counterfactual: was there a targeting change to estimate against?
CREATE OR REPLACE VIEW analysis.targeting_change_test AS
SELECT t.month,
       COUNT(DISTINCT t.account_id) AS targeted_accounts,
       ROUND(AVG(a.dpd), 1) AS mean_dpd,
       ROUND(AVG(a.outstanding_amount), 0) AS mean_outstanding,
       ROUND(100.0 * COUNT(*) FILTER (WHERE t.priority <= 3) / COUNT(*), 1) AS top3_priority_share_pct
FROM clean.daily_targeting t
JOIN clean.accounts a ON a.account_id = t.account_id
GROUP BY 1 ORDER BY 1;