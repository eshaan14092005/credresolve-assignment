import pandas as pd, numpy as np

g = pd.read_parquet("golden_account_month.parquet")
CR = 1e7

acct = g.groupby("account_id").agg(
    recovered=("amount_recovered","sum"),
    payments=("payments_success","sum"),
    calls=("calls","sum"),
    attempts=("call_attempts","sum"),
    connected=("connected_attempts","sum"),
    wa=("whatsapp_events","sum"),
    sms=("sms_events","sum"),
    fv=("field_visits","sum"),
    ptps=("ptps_created","sum"),
    dpd=("dpd","first"),
    risk=("risk_segment","first"),
    loan=("loan_type","first"),
    outstanding=("outstanding_amount","first"),
).reset_index()
acct["paid"] = acct.payments > 0
acct["touches"] = acct[["calls","wa","sms","fv"]].sum(axis=1)

def compare(dim, label=None):
    t = acct.groupby(dim).agg(
        accounts=("account_id","size"),
        pay_rate=("paid","mean"),
        mean_recovered=("recovered","mean"),
    )
    t["pay_rate"] = (100*t.pay_rate).round(2)
    t["mean_recovered"] = t.mean_recovered.round(0)
    # binomial SE on the pooled rate, for a noise floor
    p = acct.paid.mean(); n = t.accounts
    t["se_pp"] = (100*np.sqrt(p*(1-p)/n)).round(2)
    print(f"\n--- {label or dim} ---")
    print(t.to_string())
    print(f"    spread: {t.pay_rate.max()-t.pay_rate.min():.2f} pp | "
          f"typical 2*SE: {2*t.se_pp.median():.2f} pp")

for d in ["risk", "loan", "dpd"]:
    compare(d)

acct["touch_band"] = pd.cut(acct.touches, [-1,0,5,10,20,50,1000],
                            labels=["0","1-5","6-10","11-20","21-50","50+"])
compare("touch_band", "attempt frequency (total touches)")

acct["out_band"] = pd.qcut(acct.outstanding, 5, labels=["Q1 low","Q2","Q3","Q4","Q5 high"])
compare("out_band", "borrower segment (outstanding quintile)")

print("\n--- correlation of activity with recovery (account level) ---")
print(acct[["touches","calls","attempts","connected","wa","sms","fv","ptps",
            "recovered","outstanding","dpd"]].corr()["recovered"].round(3).to_string())

# geography and vendor need joins outside the golden table
brw = pd.read_csv("data/raw/borrowers.csv")
brw = brw.sort_values("updated_at").drop_duplicates("borrower_id", keep="last")
a2b = pd.read_csv("data/raw/accounts.csv", usecols=["account_id","borrower_id"])
geo = acct.merge(a2b, on="account_id", how="left").merge(
      brw[["borrower_id","state"]], on="borrower_id", how="left")
print("\n--- geography (state) ---")
t = geo.groupby("state").agg(accounts=("account_id","size"), pay_rate=("paid","mean"))
t["pay_rate"] = (100*t.pay_rate).round(2)
print(t.to_string())
print(f"    spread: {t.pay_rate.max()-t.pay_rate.min():.2f} pp")