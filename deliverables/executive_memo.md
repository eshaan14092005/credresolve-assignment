# Recovery Performance Review: January to July 2026

To: Leadership Team
From: [Your name]
Date: [Date]

## What happened

**Recovery has not improved. It has been flat for seven months.**

We recovered ₹18.72 Cr in January and ₹18.72 Cr in July. In between it moved up and down by a crore or two each month and ended exactly where it started.

Rather than simply assert a different number, we tested whether any reasonable definition of recovery supports the claim. Three numerators against four denominators gives twelve definitions, applied across all six month-on-month transitions. Across all twelve, mean month-on-month change falls between −0.30% and +0.39%, and total January-to-July change falls between −1.97% and +1.17%. Nothing supports 11% as a sustained rate.

One correction to the framing. The data covers seven complete months, not twelve. Every event table runs from 1 January to 8 August 2026 with no gaps, and August holds only eight days. Over the six transitions that actually exist, 11% monthly would compound to 87% growth. We saw 0.01%.

## Why it happened

The 11% is real arithmetic describing one month pair. It compares February to March. February has 28 days and March has 31, so March had 10.7% more calling days. Measured per calling day, that same comparison is +0.29%.

Denominator choice made it worse. A fixed denominator such as the full 30,000-account book absorbs none of the variation in activity, so every wobble in the numerator passes through amplified. The same data swings ±2% per worked account and ±11% against a constant. The reported figure used the constant.

Separately, 500 duplicate payment records inflate reported recovery by ₹2.59 Cr, or 1.93%. That inflation is stable in every month, so it lifts the level without creating a trend.

This is not fraud and not a broken pipeline. It is what happens when a metric is never normalised for month length and then gets quoted from the best available comparison.

## How confident we are

Confident on the verdict. It does not depend on our preferred definition, because it holds across all twelve we tested, including those most favourable to the original claim. Confident on the mechanism, because per-day normalisation takes February-to-March from +11.03% to +0.29%.

We also tested and ruled out the four explanations that would otherwise account for a false improvement: portfolio mix change, disposition code migration, account attrition from the denominator, and a mid-year targeting change. None occurred. Detail is in the data quality report.

One limitation needs stating plainly. **Nothing in this dataset predicts recovery.** Correlations with collections activity run from −0.002 to +0.009 across 30,000 accounts, covering calls, attempts, connections, WhatsApp, SMS, field visits and promises, as well as DPD, outstanding balance and risk grade. Agent performance varies 0.98 times what chance alone would produce.

Two very different situations would produce this: the programme genuinely has no measurable effect, or this dataset lacks the causal structure needed to detect one. We cannot tell which, and we are not claiming the first.

## What we should do

Fix the metric definition. Report recovery per calling day, name the denominator every time, and count both PTP code variants as promises — the narrow definition currently understates PTP rate by about 11 percentage points.

Stop reporting channel-attributed recovery. Last-touch attribution gives each channel almost exactly its share of event volume: voice takes 41.2% of the credit and generates 41.2% of the events. It measures how much a channel talks, not how well it works.

**Do not deploy the ₹10 Cr into any of the six options yet.**

## Financial impact

Reported recovery is overstated by ₹2.59 Cr through duplicate records. That is a one-line pipeline fix.

We cannot give you an ROI figure for any of the six options, and we would be cautious about accepting one from anywhere else. **There is no cost, spend or rate-card field in any of the seventeen source systems.** Without cost there is no cost per rupee recovered, and without that there is no ROI and no break-even.

We also have direct evidence against three options. Agent variance is indistinguishable from chance, so more agents buys nothing measurable. Campaign target definition moves recovery by 0.81 percentage points, and campaigns aimed at DPD over 30 perform the same as those aimed at NPA accounts, so there is no targeting logic to improve on. Telephony vendors differ by 2.3 points on connect rate with none strong on both connect rate and recovery. The remaining three — AI voice, WhatsApp, field operations — all buy more activity, and activity has no measurable relationship to recovery.

One baseline nobody is accounting for: **around 14% of successful payments arrive with no prior interaction at any attribution window.** That money comes in without collections contact and must be netted out of any incremental case.

Our recommendation is to commit **₹50 to 75 lakh, under 8% of the budget, to a randomised test.** Six arms of 1,000 accounts, one control and one per option, assigned at random and measured over twelve weeks on recovery per assigned account. At the 43% baseline this detects a 6 percentage point difference at 80% power; detecting 2 points would need roughly 9,000 per arm. Deploy the remaining ₹9.25 to 9.5 Cr against the result.

The reporting we have today cannot tell a working programme apart from one that does nothing. Spending ₹10 Cr into that gap tells us nothing. Spending 8% of it first buys the ability to spend the rest with evidence.

If the business defines recovery in a way we did not test, we would want to see that definition — our search was wide but not exhaustive. We would also revisit this given cost data, or any past period where channel or targeting was assigned at random.

---

Supporting material in the accompanying repository: data quality report, golden dataset pipeline, and full analysis notebook. Every figure rebuilds from raw files in about ten seconds.
