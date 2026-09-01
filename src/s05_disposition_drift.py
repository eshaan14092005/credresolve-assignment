import pandas as pd

RAW = "data/raw"
d = pd.read_csv(f"{RAW}/call_dispositions.csv")
d["event_at"] = pd.to_datetime(d["event_at"])
d["month"] = d.event_at.dt.to_period("M")

print("Version share by month (%):")
vm = d.groupby(["month", "disposition_version"]).size().unstack(fill_value=0)
print((100 * vm.div(vm.sum(axis=1), axis=0)).round(1).to_string())

print("\nCode vocabulary by version (counts):")
cv = d.groupby(["disposition_version", "disposition_code"]).size().unstack(fill_value=0)
print(cv.to_string())

print("\nPTP-family codes by month:")
ptp = d[d.disposition_code.isin(["PTP", "PROMISE_TO_PAY"])]
pm = ptp.groupby(["month", "disposition_code"]).size().unstack(fill_value=0)
pm["total"] = pm.sum(axis=1)
pm["pct_of_all_disp"] = (100 * pm.total / d.groupby("month").size()).round(2)
print(pm.to_string())

print("\nIMPACT: PTP rate if you count only 'PTP' vs both codes (%):")
allm = d.groupby("month").size()
narrow = 100 * d[d.disposition_code == "PTP"].groupby("month").size() / allm
broad = 100 * ptp.groupby("month").size() / allm
print(pd.DataFrame({"narrow_PTP_only": narrow.round(2),
                    "broad_both_codes": broad.round(2),
                    "understatement_pp": (broad - narrow).round(2)}).to_string())