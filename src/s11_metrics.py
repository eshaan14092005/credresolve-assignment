import pandas as pd, itertools

g = pd.read_parquet("output/golden_account_month.parquet")
g["month"] = g.month.astype("period[M]")
CR = 1e7

days = g.month.drop_duplicates().sort_values().dt.days_in_month.values
m = g.groupby("month").agg(
    recovered=("amount_recovered","sum"),
    payers=("payments_success", lambda x: (x>0).sum()),
    worked=("was_worked","sum"),
    targeted=("was_targeted","sum"),
    calls=("calls","sum"),
    ptps=("ptps_created","sum"),
    kept=("ptps_kept","sum"),
)
m["days"] = days
m["book"] = g.account_id.nunique()

print("PER-DAY NORMALISED (removes calendar artifact):")
norm = pd.DataFrame({
    "recovered_cr": (m.recovered/CR).round(2),
    "per_day_cr": (m.recovered/m.days/CR).round(3),
    "payers_per_day": (m.payers/m.days).round(1),
})
norm["per_day_mom_%"] = (m.recovered/m.days).pct_change().mul(100).round(2)
print(norm.to_string())

print("\nPTP kept rate (cohort by creation month):")
print((100*m.kept/m.ptps).round(2).to_string())

print("\n" + "="*70)
print("RECONSTRUCTION: which metric definitions produce +11%?")

numerators = {
    "recovered_rs": m.recovered,
    "payers": m.payers,
    "recovered_per_day": m.recovered/m.days,
}
denominators = {
    "none_absolute": 1,
    "per_worked": m.worked,
    "per_targeted": m.targeted,
    "per_total_book": m.book,
}

hits = []
for (nn, nv), (dn, dv) in itertools.product(numerators.items(), denominators.items()):
    series = nv/dv
    mom = series.pct_change().mul(100)
    for month, val in mom.dropna().items():
        hits.append({"numerator": nn, "denominator": dn, "transition": str(month),
                     "mom_%": round(val,2)})

h = pd.DataFrame(hits)
print(f"\ntotal definition x transition combinations: {len(h)}")
print(f"combinations yielding >= +10%: {(h['mom_%']>=10).sum()}")
print("\nAll combinations producing >= +10%:")
print(h[h["mom_%"]>=10].sort_values("mom_%", ascending=False).to_string(index=False))

print("\nMean MoM across all 6 transitions, by definition:")
summary = h.groupby(["numerator","denominator"])["mom_%"].agg(["mean","min","max"]).round(2)
print(summary.to_string())

print("\nJan -> Jul total change by definition (%):")
for (nn, nv), (dn, dv) in itertools.product(numerators.items(), denominators.items()):
    s = nv/dv
    print(f"  {nn:20} / {dn:16} {100*(s.iloc[-1]/s.iloc[0]-1):+7.2f}%")