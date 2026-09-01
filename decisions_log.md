# Decision Log

Every cleaning rule, source-of-truth choice and metric definition used in this analysis, with the evidence behind it and its measured impact.

Decision IDs appear as comments in `sql/01_clean.sql` and `sql/03_metrics.sql` at the point where each rule is applied. To trace a number: metric → golden column → clean rule → decision ID → the script listed here.

---

## D1 — Accounts are the analytical spine

**Rule.** Use `account_id` as the join key throughout. Do not build metrics on `borrower_id`.

**Evidence.** Referential integrity tested on every foreign key in all 17 tables (`src/p1b_integrity.py`). `account_id` has zero orphans across all twelve referencing tables. `borrower_id` has 761–985 orphan IDs in every one of the nine tables that reference it, affecting up to 9,778 rows. Additionally 455 accounts (1.52%) have a null `borrower_id`, and 897 of 10,943 account-level borrower IDs do not exist in `borrowers`.

**Impact.** Any borrower-level metric would carry a 7–8% orphan rate. Geography results, which unavoidably route through borrowers, inherit this and are reported with the caveat.

---

## D2 — Analysis window is January to July 2026

**Rule.** Restrict all analysis to 2026-01-01 through 2026-07-31. Seven complete months, six month-on-month transitions.

**Evidence.** `src/s00_window_check.py` and `src/s00b_window_audit.py`. All ten event tables run 2026-01-01 to 2026-08-08. January through July each have 28–31 distinct days with zero missing days (220 expected, 220 present). August has 8 real days: row volume runs ~2,150/day through 8 August, then drops to 1.

**Impact.** Including August produces a −74.5% month-on-month reading in July→August, entirely an artifact of the partial period.

---

## D2a — The brief's "approximately 12 months" is incorrect

**Rule.** Report the true window rather than the stated one.

**Evidence.** Every date-like column in all 17 tables was scanned. The longest span anywhere is 699 days (`accounts.opened_at` and `agents.joined_at`), which are entity creation dates, not observation windows. Next longest is 579 days (`borrowers.created_at`). All `event_at` columns span 219–226 days. No field spans twelve months.

**Impact.** 11% monthly over the 6 transitions that exist implies +87% cumulative growth. Over 11 transitions it would imply +215%. Actual January-to-July change is +0.01%.

---

## D3 — Deduplicate payments on `payment_id`

**Rule.** One row per `payment_id`.

**Evidence.** `src/s02_dup_payments.py`. 500 excess rows share a `payment_id`: 486 exact full-row duplicates and 14 differing only in `payment_reference`.

**Impact.** ₹2.59 Cr removed from reported SUCCESS recovery, 1.93% of the total. Inflation is stable at 1.50–2.27% in every month, so this changes the level and creates no trend.

---

## D4 — Do NOT deduplicate on `payment_reference`

**Rule.** Treat `payment_reference` as a non-unique label. Never use it as an identity key.

**Evidence.** Two independent tests. First, in all 3,407 collision groups both `account_id` and `amount` differ, which no gateway retry would. Second, references run TXN0000009 to TXN0069996, a pool of 69,996; drawing 24,632 at random predicts 20,765 distinct values and 20,821 are observed, a 0.3% difference. The collisions match the birthday paradox exactly.

**Impact.** Deduplicating on reference would have removed 3,811 legitimate payments worth ₹20.54 Cr and understated true recovery by 15%. This is the largest error avoided in the analysis.

---

## D5 — Survivor rule for duplicate `payment_id`

**Rule.** Where rows share a `payment_id`, keep the one with a non-null `payment_reference`.

**Evidence.** All 14 conflicting cases are identical except that one copy has a reference populated and the other is null. The populated row is the more complete record.

**Impact.** Immaterial to totals (n=14), but the rule is stated so the code and the documentation agree. An arbitrary `keep='first'` would have been indefensible under questioning.

---

## D6 — Reject `agents.csv` as a dimension

**Rule.** Never join to `agents` for attributes. Use `agent_id` as an opaque key only.

**Evidence.** `src/s03_agent_identity.py`. If this were a valid slowly-changing dimension, `joined_at` would be immutable. All 1,000 `agent_id` values carry 14–48 conflicting `joined_at` values, one distinct value per row. All 1,099 `employee_code` values span multiple `agent_id` values. Each agent ID also carries 6–10 names and 7–15 vendors. The relationship is many-to-many in both directions.

**Impact.** Three required dimensions cannot be analysed: agent tenure, agent team, and vendor attributed via agent. Reported as a limitation rather than reconstructed, because any reconstruction would be arbitrary. Per-agent aggregation remains valid since `agent_id` has zero orphans across the six tables referencing it.

---

## D7 — Recover vendor through the event tables

**Rule.** Use `calls.vendor_id` and `payments.provider_id` for vendor analysis, not `agents.vendor_id`.

**Evidence.** Both resolve against `vendor_telephony` with zero orphans, unlike the agent table's vendor field.

**Impact.** The vendor dimension is preserved despite D6.

---

## D8 — No timezone conversion

**Rule.** Leave `event_at` as stored. Do not convert between UTC, Asia/Kolkata and Asia/Dubai.

**Evidence.** `src/s04_timezones.py`. Hour-of-day distribution is uniform in all three timezone groups: 3.92%–4.58% against a 4.17% expectation. Day-of-week is also uniform: 13.98%–14.68% against 14.29%. With no diurnal or weekly signal there is nothing to align the three clocks against.

**Impact.** None on any metric. Conversion is both impossible to calibrate and immaterial to results.

---

## D9 — "Calling time" declared unanalysable

**Rule.** Report calling time as a null finding. Do not model hour-of-day effects.

**Evidence.** Same as D8.

**Impact.** One of the thirteen required dimensions cannot be analysed. Stated positively: any regression of contact rate on hour-of-day in this dataset returns noise and could be misreported as a result.

---

## D10 — Ignore `disposition_version`

**Rule.** Do not treat `legacy`, `v1` and `v2` as meaningful. No version-based filtering or reconciliation.

**Evidence.** `src/s05_disposition_drift.py`. Version share is approximately 33% each in every month, so no migration occurred. All nine disposition codes appear in all three versions at roughly 1,300 each, so the versions carry no vocabulary difference.

**Impact.** None. Suspect D from the brief is rejected.

---

## D11 — PTP counts both code variants

**Rule.** PTP rate = (`PTP` + `PROMISE_TO_PAY`) ÷ dispositions.

**Evidence.** Counts are near-identical (3,904 and 3,926), both appear in all three disposition versions, and both are semantically a promise to pay.

**Impact.** The narrow single-code definition understates PTP rate by 10.7–11.8 percentage points in every month: 11.2% against 22.4%.

---

## D12 — Reject last-touch attribution

**Rule.** Do not report channel-attributed recovery as a performance measure.

**Evidence.** `src/s08_attribution.py`. Attribution share matches event volume share at a ratio of 0.98–1.01 for all four channels: voice 41.2% against 41.2%, WhatsApp 27.2% against 27.3%, SMS 20.5% against 20.3%, field 11.1% against 11.3%. Widening the attribution window from 1 day to 90 days moves the unattributed share from 96.8% to 16.2% while channel shares stay fixed.

**Impact.** Channel conversion, one of the nine required metrics, cannot be measured observationally. Establishing channel effectiveness would require randomised assignment.

---

## D13 — Self-cure segment identified

**Rule.** Net self-cure recovery out of any incremental investment case.

**Evidence.** 2,453 of 17,534 SUCCESS payments (14.0%) have no prior interaction at any attribution window, found via backward `merge_asof` with no match.

**Impact.** This recovery occurs without collections contact and cannot be attributed to spend. Material to the ₹10 Cr ROI question.

---

## D14 — Borrower conflicts resolved by latest `updated_at`

**Rule.** One row per `borrower_id`, taking the most recently updated.

**Evidence.** 30,600 rows for 11,015 distinct IDs, including 600 exact duplicates. 8,159 IDs (74%) have a conflicting `city` and 8,185 a conflicting `name`. There is no way to recover the true value, so a rule is required.

**Impact.** 64% of borrower rows rejected, 30,600 down to 11,015 — the largest single cleaning impact in the pipeline. This is a rule, not a truth: geography results inherit both this assumption and the D1 orphan rate.

---

## D15 — RPC computed within `call_dispositions` only

**Rule.** RPC = (`PTP` + `PROMISE_TO_PAY` + `PAID` + `REFUSED` + `DISPUTE` + `PTP_BROKEN`) ÷ all dispositions. `CALLBACK` excluded as ambiguous, since it can be logged by an IVR or a wrong party. Contact rate computed within `call_attempts` only.

**Evidence.** Cross-table RPC yields impossible values above 100% (112.5% in January). Reconciliation shows three incompatible definitions of contact: 21,109 calls with a CONNECTED attempt, 17,896 marked ANSWERED, 28,971 with any disposition. Decisively, only 8,056 of 35,000 dispositions (23%) sit on a call that had a CONNECTED attempt — the other 77%, including `PROMISE_TO_PAY` and `PAID`, are recorded against calls that never connected.

**Impact.** RPC resolves to 65.51%–66.84% and contact rate to 19.66%–20.56%. The two are reported separately and explicitly cannot be reconciled. This is an eighth data-quality finding not listed in the brief.

---

## D16 — Recovery rate uses the all-channel worked denominator

**Rule.** `was_worked` is true if an account received any call, WhatsApp, SMS or field visit in the month. Recovery rate per worked account uses this denominator.

**Evidence.** An earlier Python implementation used a voice-only denominator (~10,324 accounts/month), giving 22.99%. The golden dataset's all-channel flag gives ~19,292 accounts/month and 12.06%. The brief treats all seven channels as the collections platform, so the all-channel definition is correct.

**Impact.** The reported level changes from ~23% to ~12%. The verdict does not change: January-to-July movement is −2.03% under the all-channel definition and −0.32% under voice-only. Both are flat. This decision supersedes any figure in earlier working papers.

---

## Decisions not taken

Recorded so the omissions are visible rather than accidental.

**No imputation of missing values.** Null rates run 1–3% and are suspiciously round (`calls.agent_id` exactly 2.00%, `field_visits.scheduled_at` exactly 1.00%). Missing values are excluded from the relevant denominator. Imputing would fabricate activity that did not occur.

**No reconstruction of the agent dimension.** Taking the maximum `updated_at` row per `agent_id` would produce a clean-looking one-row-per-agent table, but D6 shows there is no signal to recover, so the result would be arbitrary and would look authoritative.

**No propensity scoring, matching or uplift modelling.** All require covariates that predict the outcome. The maximum absolute correlation between any covariate and recovery is 0.0083, against a noise floor of ±0.0113 at n=30,000. These methods would produce estimates that look precise and mean nothing.

**No treatment of DPD as time-varying.** `accounts.dpd` is a static snapshot with one value per account and no history, and `account_status_history` carries status but not DPD. DPD is treated as a fixed attribute, which carries its own bias since the measurement date is unknown.
