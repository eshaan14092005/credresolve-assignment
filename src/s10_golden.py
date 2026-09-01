import pandas as pd
from pathlib import Path

RAW, OUT = "data/raw", Path("output")
OUT.mkdir(exist_ok=True)
Path("reports").mkdir(exist_ok=True)

MONTHS = pd.period_range("2026-01", "2026-07", freq="M")
waterfall = []

def log(table, raw_n, kept_n, reason):
    waterfall.append({"table": table, "raw": raw_n, "kept": kept_n,
                      "rejected": raw_n - kept_n, "reason": reason})

def read(name, cols=None):
    return pd.read_csv(f"{RAW}/{name}.csv", usecols=cols)

def to_month(df, col="event_at"):
    df[col] = pd.to_datetime(df[col])
    df["month"] = df[col].dt.to_period("M")
    return df[df.month.isin(MONTHS)]

# ---------- accounts: the spine (D1)
acc = read("accounts", ["account_id","dpd","risk_segment","loan_type","outstanding_amount"])
assert acc.account_id.is_unique
log("accounts", len(acc), len(acc), "spine, no cleaning required")

# ---------- payments (D3, D4, D5)
p_raw = read("payments")
p = (p_raw.sort_values("payment_reference", na_position="last")
          .drop_duplicates("payment_id", keep="first"))
log("payments", len(p_raw), len(p), "D3/D5 dedup on payment_id, prefer non-null reference")
p = to_month(p)
succ = p[p.payment_status == "SUCCESS"]
log("payments (SUCCESS, Jan-Jul)", len(p), len(succ), "D2 window + SUCCESS only")

# ---------- events
def event_counts(name, colname, extra=None):
    d_raw = read(name)
    d = d_raw.drop_duplicates()
    log(name, len(d_raw), len(d), "exact full-row dedup")
    d = to_month(d)
    g = d.groupby(["account_id","month"]).size().rename(colname)
    return d, g

calls_df, c_calls = event_counts("calls", "calls")
att_df,   c_att   = event_counts("call_attempts", "call_attempts")
disp_df,  c_disp  = event_counts("call_dispositions", "dispositions")
wa_df,    c_wa    = event_counts("whatsapp_events", "whatsapp_events")
sms_df,   c_sms   = event_counts("sms_events", "sms_events")
fv_df,    c_fv    = event_counts("field_visits", "field_visits")

c_conn = (att_df[att_df.attempt_status == "CONNECTED"]
          .groupby(["account_id","month"]).size().rename("connected_attempts"))

# ---------- PTPs (D11: both codes count)
ptp_raw = read("promises_to_pay")
ptp = to_month(ptp_raw.drop_duplicates())
c_ptp = ptp.groupby(["account_id","month"]).size().rename("ptps_created")
c_kept = (ptp[ptp.status == "KEPT"].groupby(["account_id","month"])
          .size().rename("ptps_kept"))

# ---------- targeting
tgt_raw = read("daily_targeting")
tgt = tgt_raw.drop_duplicates()
tgt["month"] = pd.to_datetime(tgt.target_date).dt.to_period("M")
tgt = tgt[tgt.month.isin(MONTHS)]
log("daily_targeting", len(tgt_raw), len(tgt), "dedup + window")
c_tgt = tgt.groupby(["account_id","month"]).size().rename("targeted")
c_tgt_c = (tgt[tgt.status=="CONTACTED"].groupby(["account_id","month"])
           .size().rename("targeted_contacted"))
c_tgt_s = (tgt[tgt.status=="SKIPPED"].groupby(["account_id","month"])
           .size().rename("targeted_skipped"))

# ---------- payments aggregated
c_pay = succ.groupby(["account_id","month"]).agg(
    payments_success=("payment_id","size"),
    amount_recovered=("amount","sum"))

# ---------- exits
hist = to_month(read("account_status_history", ["account_id","event_at","status"]))
exits = (hist[hist.status.isin(["CLOSED","WRITEOFF","NPA"])]
         .groupby("account_id").month.min().rename("exit_month"))

# ---------- build the frame
idx = pd.MultiIndex.from_product([acc.account_id, MONTHS],
                                 names=["account_id","month"])
g = pd.DataFrame(index=idx)
for s in [c_calls, c_att, c_conn, c_disp, c_wa, c_sms, c_fv,
          c_ptp, c_kept, c_tgt, c_tgt_c, c_tgt_s, c_pay]:
    g = g.join(s)
g = g.fillna(0).reset_index()

g = g.merge(acc, on="account_id", how="left", validate="many_to_one")
g = g.merge(exits, on="account_id", how="left")

g["was_worked"] = (g[["calls","whatsapp_events","sms_events","field_visits"]].sum(axis=1) > 0)
g["was_targeted"] = g.targeted > 0
g["has_exited"] = g.exit_month.notna() & (g.month >= g.exit_month)

assert len(g) == 30000 * 7, f"expected 210000 rows, got {len(g)}"
assert g.duplicated(["account_id","month"]).sum() == 0

g.to_parquet(OUT / "golden_account_month.parquet", index=False)

wf = pd.DataFrame(waterfall)
wf.to_csv("reports/waterfall.csv", index=False)
print("RAW -> GOLDEN WATERFALL\n")
print(wf.to_string(index=False))

print(f"\ngolden rows: {len(g):,}   accounts: {g.account_id.nunique():,}   months: {g.month.nunique()}")
print(f"total recovered: Rs {g.amount_recovered.sum()/1e7:.2f} Cr")
print("\nmonthly summary:")
print(g.groupby("month").agg(
    worked=("was_worked","sum"),
    targeted=("was_targeted","sum"),
    payers=("payments_success", lambda x: (x>0).sum()),
    recovered_cr=("amount_recovered", lambda x: x.sum()/1e7),
).round(2).to_string())