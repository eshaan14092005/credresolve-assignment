# Appendix: The ₹10 Cr Investment Decision

The brief asks for a single recommendation supported by seven specific elements. This appendix walks each in order. Where a figure cannot be given, it says so and states what would produce it.

**Recommendation: do not deploy the ₹10 Cr into any of the six options yet. Commit ₹50–75 lakh to a randomised test first, then deploy the remainder against the result.**

The brief explicitly permits this: *"If the data is insufficient to make a reliable recommendation, say so and explain what additional experiment/data would be required."* A section below also answers what we would pick if forced to choose today, because being asked to decide without evidence should still produce a reasoned choice.

---

## 1. Expected incremental recovery

**Not estimable, and we can quantify how far short of estimable we are.**

Correlation between collections activity and recovery across 30,000 accounts:

| Variable | Correlation with recovery |
|---|---|
| Total touches | 0.009 |
| Calls | 0.006 |
| Connected attempts | 0.008 |
| WhatsApp events | 0.008 |
| SMS events | 0.004 |
| Field visits | −0.002 |
| Promises to pay | 0.005 |
| Outstanding balance | −0.001 |
| DPD | −0.006 |

The noise floor at this sample size is ±0.011, so every one of these is indistinguishable from zero.

The difference-in-differences analysis puts a number on the detection limit. Given the observed variance and seven months of data, the minimum effect the design could have detected at 80% power is **₹20.24 per account per day, or 10.1% of baseline**. Real targeting or channel improvements move recovery by low single digits. The data cannot see an effect of the size any of these investments would plausibly produce.

So an incremental recovery estimate would not be conservative or aggressive. It would be fabricated.

---

## 2. Estimated cost

**Not computable from the data provided.**

**There is no cost, spend, rate-card, salary or vendor-pricing field in any of the seventeen source tables.** This was verified by scanning every column of every table for cost-related fields; none exists.

Costs could be assumed from market rates — agent salaries, telephony per-minute pricing, WhatsApp conversation charges, field visit costs. We have deliberately not done so. An assumed cost combined with an unestimable benefit produces an ROI figure that looks precise and carries no information, and that is precisely the failure mode this whole analysis was commissioned to uncover.

**What would fix it.** A rate card or cost-allocation table joining spend to channel, agent, campaign or vendor at monthly grain. Without it, no cost-per-rupee-recovered metric can exist, in this analysis or in production reporting.

---

## 3. Expected ROI

**Not computable.** ROI requires both an incremental benefit (element 1, not estimable) and a cost (element 2, absent from the data). Neither input exists.

We would treat any ROI figure presented for these options — from any source — as an assumption dressed as a measurement, and would ask which of the two missing inputs it invented.

---

## 4. Break-even point

**Not computable, for the same reason.**

One thing can be said about break-even that does not depend on the missing data. **Around 14% of successful payments arrive with no prior interaction at any attribution window** — 2,453 of 17,534 payments. That recovery occurs without collections contact and continues regardless of what is spent.

Any break-even calculation must be run against incremental recovery net of this self-cure baseline, not against gross recovery. A calculation that ignores it will understate the payback period substantially, because roughly one rupee in seven was arriving anyway.

---

## 5. Key assumptions

Stated explicitly, since the recommendation rests on them.

**The observation window is representative.** Seven months, January to July 2026. If the business changed materially before January, we cannot see it.

**SUCCESS is the correct definition of recovery.** We exclude FAILED, PENDING and REVERSED. Including all statuses would inflate recovery by 43%, from ₹134.15 Cr to ₹191.73 Cr. Including PENDING alone adds ₹19.49 Cr of money that has not settled.

**Absence of correlation reflects the data, not necessarily the world.** Zero predictive power is consistent with two situations: the collections programme genuinely has no measurable effect, or this dataset does not contain the causal structure needed to detect one. We cannot distinguish them, and **we do not claim the first**. This is the most important assumption in the appendix, because it is the one that could most change the recommendation.

**Costs are proportional to scale.** Any of the six options costs roughly what its volume implies. Untestable here, but standard.

**No option has a threshold effect.** We assume none of the six only works above some minimum spend that ₹10 Cr would cross. This is an assumption, not a finding, and it is the strongest argument someone could make against our position.

---

## 6. Downside scenario

**The modal outcome, not the pessimistic one: ₹10 Cr spent, no measurable change in recovery.**

Given that no variable in the data predicts recovery and agent performance varies at 0.98× chance, the base case for any of the six options is no detectable effect. That is the expected result, not the tail.

The second-order cost is worse than the money. **Under current reporting, we would not be able to tell that it had failed.** The same metric that produced an 11% improvement out of a calendar artifact would produce a similar figure next year. So the downside is ₹10 Cr spent, no improvement, and no ability to establish that no improvement occurred — which means the same decision arrives again in twelve months with no more information than today.

There is also a specific downside per option worth naming:

- **More agents** — recurring cost, not one-time. A headcount decision is harder to reverse than a technology one, and agent variance is indistinguishable from chance.
- **AI voice, WhatsApp, field ops** — all increase activity volume, which shows no relationship to recovery. Risk of increasing complaint volume with no offsetting gain.
- **Better targeting** — targeting is currently random, so any rule is a change; but the target definitions that already exist move recovery by 0.81 percentage points, with `DPD>=30` and `NPA` campaigns statistically indistinguishable.
- **Telephony** — vendor connect rates span 2.3 points (19.06% to 21.38%) and no vendor is strong on both connect rate and recovery. The ceiling on this option is visible and small.

---

## 7. Confidence and range

**On the six options: no confidence in any point estimate.** We decline to give a range because a range implies a central estimate, and we do not have one. Any interval we produced would communicate false precision.

**On the recommendation to test first: high confidence.** It does not depend on any disputed measurement. It follows from two facts that are not in question — no cost data exists, and no observable predicts recovery.

**On the experiment's own power: quantified.** At the observed 43% baseline payment rate, 1,000 accounts per arm detects a 6 percentage point difference at 80% power. Detecting a 2 point difference would require roughly 9,000 accounts per arm and a longer run. We state this rather than asserting the sample is adequate, because a test that cannot detect a plausible effect is worse than no test — it produces a null result that will be read as evidence of no effect.

---

## The proposed experiment

**Design.** Six arms. One control receiving business-as-usual treatment, and one arm per investment option. 1,000 accounts per arm, 6,000 total, assigned at random from the active book.

**Duration.** Twelve weeks.

**Primary outcome.** Recovery per **assigned** account, not per worked account. This is the critical design choice: measuring per worked account allows accounts to select into the denominator, which is the same denominator problem that produced the 11% claim.

**Secondary outcomes.** Contact rate, PTP rate, PTP kept rate, complaint rate. Each computed within a single table, per the grain-mismatch finding.

**Cost.** ₹50–75 lakh, under 8% of the budget. The largest component is the incremental spend on the five treatment arms; the control arm costs nothing beyond measurement.

**Analysis.** Difference in means against control, with confidence intervals. No modelling — the sample is randomised, so a simple comparison is both sufficient and defensible.

**What it produces.** A per-option effect size with a confidence interval, and the ability to deploy the remaining ₹9.25–9.5 Cr against a measured result rather than a plausible story.

---

## If forced to choose today

The brief says to recommend one. If a decision must be made now without the experiment, we would pick **better borrower targeting**, and we would expect it to fail.

The reasoning: it is the only one of the six where the current state is *nothing* rather than *something that shows no effect*. Targeted and untargeted accounts differ by 0.4 days of DPD and 1% of outstanding balance, and targeting priority sits at 10% across all ten levels in every month. **Targeting today is random selection.** Replacing a random rule with any rule at all is a different proposition from buying more of an activity that already shows no measurable relationship to recovery.

It is also the cheapest to reverse. A targeting model that does not work can be switched off. Agents cannot, and infrastructure contracts are hard to unwind.

We state this expecting it not to work, because the existing target definitions already in the data move recovery by less than one percentage point. We give the answer because a request for a decision deserves a reasoned choice rather than a refusal, but we would not spend ₹10 Cr on it before spending ₹50 lakh finding out.

---

## The one-line version

The reporting we have today cannot tell a working programme apart from one that does nothing. Spending ₹10 Cr into that gap tells us nothing about whether it worked. Spending 8% of it first buys the ability to spend the rest with evidence.
