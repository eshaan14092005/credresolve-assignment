import pandas as pd, numpy as np

tgt = pd.read_csv("data/raw/daily_targeting.csv")
tgt["month"] = pd.to_datetime(tgt.target_date).dt.to_period("M")
tgt = tgt[tgt.month < "2026-08"]

acc = pd.read_csv("data/raw/accounts.csv",
                  usecols=["account_id","dpd","risk_segment","loan_type","outstanding_amount"])
t = tgt.merge(acc, on="account_id", how="left", validate="many_to_one")

print("Targeted-population composition by month:")
print(t.groupby("month").agg(
    rows=("account_id","size"),
    distinct=("account_id","nunique"),
    mean_dpd=("dpd","mean"),
    mean_out=("outstanding_amount","mean"),
).round(1).to_string())

for dim in ["risk_segment","loan_type","priority"]:
    if dim not in t.columns: continue
    x = t.groupby(["month",dim]).size().unstack(fill_value=0)
    print(f"\n{dim} share of targeted population (%):")
    print((100*x.div(x.sum(axis=1),axis=0)).round(1).to_string())

print("\nStructural break test: is any month different from the pooled mean?")
for dim in ["mean_dpd","mean_out"]:
    col = "dpd" if dim=="mean_dpd" else "outstanding_amount"
    grp = t.groupby("month")[col]
    pooled_sd = t[col].std()
    z = (grp.mean() - t[col].mean()) / (pooled_sd/np.sqrt(grp.size()))
    print(f"  {dim}: max |z| across months = {z.abs().max():.2f}")

print("\nDo targeted accounts differ from untargeted ones?")
targeted_ids = set(tgt.account_id)
acc["targeted"] = acc.account_id.isin(targeted_ids)
print(acc.groupby("targeted").agg(
    n=("account_id","size"), mean_dpd=("dpd","mean"),
    mean_out=("outstanding_amount","mean")).round(1).to_string())