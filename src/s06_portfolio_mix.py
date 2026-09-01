import pandas as pd

RAW = "data/raw"
acc = pd.read_csv(f"{RAW}/accounts.csv")
acc["opened_at"] = pd.to_datetime(acc["opened_at"])

calls = pd.read_csv(f"{RAW}/calls.csv", usecols=["account_id", "event_at"])
calls["month"] = pd.to_datetime(calls.event_at).dt.to_period("M")

touched = calls[["account_id", "month"]].drop_duplicates()
before = len(touched)
touched = touched.merge(acc[["account_id","dpd","risk_segment","loan_type","outstanding_amount"]],
                        on="account_id", how="left")
assert len(touched) == before, f"join exploded: {before} -> {len(touched)}"

print(f"account-months worked: {len(touched):,}")

for dim in ["risk_segment", "loan_type"]:
    m = touched.groupby(["month", dim]).size().unstack(fill_value=0)
    print(f"\n{dim} mix by month (%):")
    print((100 * m.div(m.sum(axis=1), axis=0)).round(1).to_string())

print("\nDPD mix by month (%):")
m = touched.groupby(["month", "dpd"]).size().unstack(fill_value=0)
print((100 * m.div(m.sum(axis=1), axis=0)).round(1).to_string())

print("\nMean DPD and outstanding of worked accounts, by month:")
print(touched.groupby("month").agg(
    accounts=("account_id", "size"),
    mean_dpd=("dpd", "mean"),
    mean_outstanding=("outstanding_amount", "mean"),
).round(1).to_string())

print("\nAcquisition cohorts (accounts by opened_at month):")
print(acc.opened_at.dt.to_period("M").value_counts().sort_index().to_string())