# Collections Recovery Analysis

Testing the claim: *"Recovery has improved by 11% month-on-month."*

## The finding

**Recovery has not improved. It has been flat for seven months.**

₹18.72 Cr in January, ₹18.72 Cr in July. Across twelve combinations of numerator and denominator, mean month-on-month change falls between −0.30% and +0.39%.

The 11% is real arithmetic describing one month pair. It compares February to March. February has 28 days and March has 31, so March had 10.7% more calling days. Measured per calling day, that same comparison is +0.29%.

Two things worth knowing up front. The data covers **seven complete months, not twelve** — every event table runs 1 January to 8 August 2026, and August holds only eight days. And **nothing in this dataset predicts recovery**: correlations with collections activity run between −0.002 and +0.009 across 30,000 accounts, which is why the ₹10 Cr recommendation is to run an experiment rather than pick an option.

## Reproducing it

```bash
pip install -r requirements.txt
unzip collections_30k_dataset.zip -d data/raw
python src/run_sql.py
```

That rebuilds the entire pipeline from raw CSVs in about ten seconds and prints the contract checks, the cleaning waterfall, and the verdict. Everything else in this repository reads from the database it produces.

Expected output ends with:

```
recovery_reconciles_to_source   PASS 126.85 Cr
```

## Where things are

| Deliverable | Location |
|---|---|
| Executive memo | `executive_memo.md` |
| Executive dashboard | `executive_dashboard.html` (open in a browser) |
| Data quality report | `data_quality_report.md` |
| Analysis notebook | `notebooks/collections_analysis.ipynb` |
| SQL repository | `sql/` |
| Golden dataset | `golden_account_month.parquet`, built by `sql/02_golden.sql` |
| Architecture diagram and production design | `architecture_and_production_design.md` |
| Decision log | `decisions_log.md` |

## Repository layout

```
sql/
  00_sources.sql      views over the raw CSVs
  01_clean.sql        dedup, entity resolution, exclusions
  02_golden.sql       account × month table, 210,000 rows
  03_metrics.sql      the nine metric definitions
  04_forensics.sql    the seven data-quality suspects
  05_analysis.sql     the 11% reconstruction

src/
  run_sql.py          builds the pipeline end to end
  s00_window_check.py    how much data is actually here
  s00b_window_audit.py   exhaustive scan of every date column
  s02_dup_payments.py    duplicate payment forensics
  s03_agent_identity.py  agent dimension validity test
  s04_timezones.py       hour-of-day distribution
  s05_disposition_drift.py
  s06_portfolio_mix.py
  s07_denominator.py
  s08_attribution.py     last-touch attribution vs volume share
  s12_drivers.py         driver dimensions and correlations
  s13_counterfactual.py  did a targeting change occur?
  s14_gaps.py            campaign, agent, vendor, channel, cohort
  s15_did.py             difference-in-differences with placebo cuts

notebooks/              the reasoning narrative

README.md
executive_memo.md
executive_dashboard.html
data_quality_report.md
architecture_and_production_design.md
decisions_log.md
golden_account_month.parquet
data/raw/               source CSVs (not committed)
```

## How the analysis is structured

The SQL repository is the source of truth. The Python scripts are the forensic investigations that justify each cleaning rule, and the notebook is the narrative that connects them. The golden dataset was originally built in pandas and later migrated to SQL; the two implementations were verified identical across all 210,000 rows and 13 measures before the pandas version was retired.

Every cleaning rule in `01_clean.sql` carries a decision ID in a comment. Those resolve to `decisions_log.md`, which records the rule, the evidence behind it, and its measured impact. To trace an unexpected number: metric → golden column → clean rule → decision ID → the forensic test that produced it.

## Things worth reading first

If you have five minutes, read the memo and open the dashboard.

If you have twenty, read section 2 of the data quality report. It documents a ₹20.54 Cr duplication signal that turned out to be a false positive — the payment reference field collides at exactly the rate random assignment from a 70,000-value pool predicts. Acting on it without testing would have understated recovery by 15%. Three of the eight data-quality findings in that report are rejections, and they took as much work as the confirmations.

## Notes and caveats

The dataset is synthetic and ships with a README listing twelve intentionally injected defect classes. Each was tested independently rather than accepted. **Two of the twelve do not survive measurement**, including the duplicate references above. Documentation describing what should be wrong with a dataset is a hypothesis to test, not a finding to report.

Four dimensions the brief requires have no source column: language, client, agent tenure, and any cost or rate-card field. The missing cost data means cost per rupee recovered, ROI and break-even cannot be computed for any of the six investment options. This is stated in the memo rather than worked around.

Two of the nine required metrics are reported as unmeasurable, with evidence: cost per rupee recovered (no cost field exists) and channel conversion (last-touch attribution reproduces channel volume share at a ratio of 0.98–1.01).
