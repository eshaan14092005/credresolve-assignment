import pandas as pd

RAW = "data/raw"

hist = pd.read_csv(f"{RAW}/account_status_history.csv")
hist["month"] = pd.to_datetime(hist.event_at).dt.to_period("M")

print("Status transitions by month (counts):")
sm = hist.groupby(["month", "status"]).size().unstack(fill_value=0)
print(sm.to_string())

print("\nExit statuses as % of that month's transitions:")
exits = ["CLOSED", "WRITEOFF", "NPA"]
pct = 100 * sm[exits].sum(axis=1) / sm.sum(axis=1)
print(pct.round(2).to_string())

print("\nCumulative distinct accounts that have EVER exited, by month:")
ex = hist[hist.status.isin(exits)].sort_values("event_at")
first_exit = ex.groupby("account_id").month.min()
print(first_exit.value_counts().sort_index().cumsum().to_string())

tgt = pd.read_csv(f"{RAW}/daily_targeting.csv")
tgt["month"] = pd.to_datetime(tgt.target_date).dt.to_period("M")

print("\nTargeting volume and status mix by month:")
tm = tgt.groupby(["month", "status"]).size().unstack(fill_value=0)
tm["total_rows"] = tm.sum(axis=1)
tm["distinct_accts"] = tgt.groupby("month").account_id.nunique()
print(tm.to_string())

print("\nTargeting status mix (%):")
cols = [c for c in tm.columns if c not in ("total_rows", "distinct_accts")]
print((100 * tm[cols].div(tm.total_rows, axis=0)).round(1).to_string())

pay = pd.read_csv(f"{RAW}/payments.csv").drop_duplicates("payment_id", keep="first")
pay["month"] = pd.to_datetime(pay.event_at).dt.to_period("M")
succ = pay[pay.payment_status == "SUCCESS"]

calls = pd.read_csv(f"{RAW}/calls.csv", usecols=["account_id", "event_at"])
calls["month"] = pd.to_datetime(calls.event_at).dt.to_period("M")

print("\nRecovery RATE under three candidate denominators (%):")
num = succ.groupby("month").account_id.nunique()
d_worked = calls.groupby("month").account_id.nunique()
d_targeted = tgt.groupby("month").account_id.nunique()
d_total = 30000

out = pd.DataFrame({
    "paying_accts": num,
    "per_worked": (100 * num / d_worked).round(2),
    "per_targeted": (100 * num / d_targeted).round(2),
    "per_total_book": (100 * num / d_total).round(2),
})
print(out.to_string())
print("\nMoM % change in each rate:")
print(out[["per_worked","per_targeted","per_total_book"]][:-1].pct_change().mul(100).round(2).to_string())
