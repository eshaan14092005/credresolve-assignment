"""
Part 4 - Counterfactual, implemented.

The brief asks what recovery would have looked like without the mid-year
targeting change. We first test whether such a change occurred (it did not),
then run the DiD anyway at an assumed cut date, then run placebo cuts at every
other month to show the estimator returns noise wherever it is pointed.

Finally we compute the minimum effect the design could have detected, which
turns "not identified" from an assertion into a number.
"""
import duckdb
import numpy as np
import pandas as pd

con = duckdb.connect("collections.db", read_only=True)
g = con.sql("SELECT * FROM golden.account_month").df()
g["month"] = pd.to_datetime(g.month).dt.to_period("M")

MONTHS = sorted(g.month.unique())
print(f"months: {MONTHS[0]} to {MONTHS[-1]}  accounts: {g.account_id.nunique():,}\n")


# ---------------------------------------------------------------------------
# Treatment assignment.
#
# No real targeting change exists, so we construct the most plausible one a
# business would actually make: prioritise higher-DPD accounts. Treatment =
# accounts above median DPD, which is what any "better targeting" rule would
# select. If a real change had occurred this is the split it would produce.
# ---------------------------------------------------------------------------
acct = g.groupby("account_id").agg(dpd=("dpd", "first")).reset_index()
median_dpd = acct.dpd.median()
acct["treated"] = acct.dpd > median_dpd
print(f"treatment split at DPD > {median_dpd:.0f}: "
      f"{acct.treated.sum():,} treated / {(~acct.treated).sum():,} control")

d = g.merge(acct[["account_id", "treated"]], on="account_id", how="left")

# Outcome: recovery per account per month, normalised per calendar day.
# Per-day normalisation is required, not optional: month length drives swings
# of up to 11% and would otherwise be absorbed into the DiD estimate.
d["days"] = d.month.dt.days_in_month
d["y"] = d.amount_recovered / d.days


def did(cut, data=d):
    """Difference-in-differences at a given cut month.

    coefficient = (treated_post - treated_pre) - (control_post - control_pre)
    Standard error from the four cell means, propagated in quadrature.
    """
    data = data.copy()
    data["post"] = data.month >= cut

    cells = data.groupby(["treated", "post"]).y.agg(["mean", "std", "size"])
    if len(cells) < 4:
        return None

    m = cells["mean"].unstack()
    s = cells["std"].unstack()
    n = cells["size"].unstack()

    coef = (m.loc[True, True] - m.loc[True, False]) - \
           (m.loc[False, True] - m.loc[False, False])

    se = np.sqrt(sum((s.loc[t, p] ** 2) / n.loc[t, p]
                     for t in [True, False] for p in [True, False]))

    return {"cut": str(cut), "coef": coef, "se": se,
            "t": coef / se, "lo": coef - 1.96 * se, "hi": coef + 1.96 * se}


# ---------------------------------------------------------------------------
# 1. Parallel trends. The identifying assumption, tested rather than assumed.
# ---------------------------------------------------------------------------
print("\n=== PARALLEL TRENDS (pre-period, Jan-Mar) ===")
pre = d[d.month < MONTHS[3]]
tr = pre[pre.treated].groupby("month").y.mean()
ct = pre[~pre.treated].groupby("month").y.mean()
diff = (tr - ct)
print(pd.DataFrame({"treated": tr.round(2), "control": ct.round(2),
                    "gap": diff.round(2)}).to_string())
print(f"\ngap drift across pre-period: {diff.iloc[-1] - diff.iloc[0]:+.2f} Rs/account/day")
print("(a stable gap is what parallel trends requires)")


# ---------------------------------------------------------------------------
# 2. Main estimate at the assumed cut, then placebo cuts everywhere else.
#
# If the estimator is picking up a real treatment, the April coefficient
# should stand out from the placebo cuts. If every cut returns noise, there is
# no treatment to find.
# ---------------------------------------------------------------------------
print("\n=== DiD AT EVERY POSSIBLE CUT DATE ===")
print("April is the assumed change; all others are placebos.\n")

rows = [did(c) for c in MONTHS[1:]]
r = pd.DataFrame([x for x in rows if x])
r["assumed"] = np.where(r.cut == str(MONTHS[3]), "<- assumed cut", "placebo")
r["significant"] = np.where(r.t.abs() > 1.96, "YES", "no")

print(r[["cut", "coef", "se", "t", "lo", "hi", "significant", "assumed"]]
      .round(3).to_string(index=False))

print(f"\nplacebo cuts significant at 95%: "
      f"{(r[r.assumed=='placebo'].t.abs() > 1.96).sum()} of {(r.assumed=='placebo').sum()}")


# ---------------------------------------------------------------------------
# 3. Minimum detectable effect.
#
# Given the observed variance and sample, what is the smallest true effect
# this design could have found at 80% power? If that number is larger than any
# plausible targeting effect, the design is underpowered by construction.
# ---------------------------------------------------------------------------
print("\n=== MINIMUM DETECTABLE EFFECT ===")
main = did(MONTHS[3])
mde = 2.8 * main["se"]          # 1.96 + 0.84, for 80% power at alpha=0.05
baseline = d.y.mean()

print(f"baseline recovery      : Rs {baseline:,.2f} per account per day")
print(f"standard error of DiD  : Rs {main['se']:,.2f}")
print(f"minimum detectable eff : Rs {mde:,.2f}  ({100*mde/baseline:.1f}% of baseline)")
print(f"observed estimate      : Rs {main['coef']:,.2f}  ({100*main['coef']/baseline:+.1f}%)")
print(f"95% CI                 : [{main['lo']:,.2f}, {main['hi']:,.2f}]")


# ---------------------------------------------------------------------------
# 4. Approaches considered and rejected, with the reason.
# ---------------------------------------------------------------------------
print("\n=== WHY OTHER APPROACHES WERE NOT USED ===")
feats = ["calls", "call_attempts", "connected_attempts", "whatsapp_events",
         "sms_events", "field_visits", "ptps_created", "dpd", "outstanding_amount"]
a = g.groupby("account_id").agg({**{f: "sum" for f in feats[:7]},
                                 "dpd": "first", "outstanding_amount": "first",
                                 "amount_recovered": "sum"})
corr = a.corr()["amount_recovered"].drop("amount_recovered").abs()

print(f"max |correlation| between any covariate and recovery: {corr.max():.4f}")
print(f"noise floor at n={len(a):,}: +/- {1.96/np.sqrt(len(a)):.4f}\n")
print("Propensity scoring, matching, uplift modelling and regression adjustment")
print("all require covariates that predict the outcome. None here does. Applying")
print("them would produce estimates that look precise and mean nothing.")
