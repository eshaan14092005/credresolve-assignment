import pandas as pd

RAW = "data/raw"
pay = pd.read_csv(f"{RAW}/payments.csv")

print("rows:", len(pay))
print("distinct payment_id:", pay.payment_id.nunique())
print(pay.payment_status.value_counts())
print("SUCCESS total: Rs",
      round(pay.loc[pay.payment_status == "SUCCESS", "amount"].sum() / 1e7, 2), "Cr")