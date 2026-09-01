# Collections Data Analyst Assignment

## Context
72-hour hiring assignment. ~7.3 months of collections data
(2026-01-01 to 2026-08-08) across 17 raw CSVs in data/raw/.
Business claims "recovery improved 11% month-on-month". We are testing that.

## Known data facts (verified, do not re-derive)
- Window is 7.3 months, NOT 12. August is partial (8 days) - exclude from MoM.
- account_id is clean across all tables. borrower_id has 761-985 orphans
  in EVERY referencing table. Use account_id as the spine.
- agents.csv is corrupt: 30,000 rows / 1,000 agent_ids, each with 14-48
  conflicting employee_codes, names, vendors, teams, joined_at.
  Never join to it without deduplicating first.
- borrowers.csv: 30,600 rows / 11,015 ids. 74% have conflicting city.
- No language, client, tenure, or cost columns exist anywhere.

## Rules
- Assert row counts before and after EVERY merge.
- Never use bare drop_duplicates(); dedup on an explicit key with an
  explicit survivor rule.
- I am learning this- I am learning this- Iri- I am learning this- I am learninitly - k. Explain and assist; don't do the thinking for me.
