import pandas as pd

RAW = "data/raw"
calls = pd.read_csv(f"{RAW}/calls.csv")
calls["event_at"] = pd.to_datetime(calls["event_at"])
calls["hour"] = calls.event_at.dt.hour

print(calls.timezone.value_counts().to_string())

pivot = (calls.groupby(["hour", "timezone"]).size()
              .unstack(fill_value=0))
pivot_pct = 100 * pivot / pivot.sum()

print("\nShare of each timezone's calls by hour (%):")
print(pivot_pct.round(2).to_string())

print("\nPeak hour per timezone:", pivot_pct.idxmax().to_dict())
print("Min/max share per tz (flat if these are close):")
print(pivot_pct.agg(["min", "max"]).round(2).to_string())

calls["dow"] = calls.event_at.dt.dayofweek
print("\nShare by day of week (%):")
print((100 * calls.dow.value_counts(normalize=True).sort_index()).round(2).to_string())