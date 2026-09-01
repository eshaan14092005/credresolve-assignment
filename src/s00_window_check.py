import pandas as pd
import os

RAW = "data/raw"

ts_cols = {
    "accounts": ["opened_at"],
    "agents": ["joined_at", "updated_at"],
    "borrowers": ["created_at", "updated_at"],
    "agent_sessions": ["login_at", "logout_at"],
    "campaigns": ["start_at", "end_at"],
    "calls": ["event_at"],
    "call_attempts": ["event_at"],
    "call_dispositions": ["event_at"],
    "payments": ["event_at"],
    "promises_to_pay": ["event_at", "promised_date"],
    "field_visits": ["event_at", "scheduled_at"],
    "whatsapp_events": ["event_at"],
    "sms_events": ["event_at"],
    "complaints": ["event_at", "resolution_at"],
    "account_status_history": ["event_at", "recorded_at"],
    "daily_targeting": ["target_date"],
}

print(f"{'table':24} {'column':16} {'min':20} {'max':20} {'days':>6} {'months':>7}")
print("-" * 100)

for t, cols in ts_cols.items():
    df = pd.read_csv(f"{RAW}/{t}.csv", usecols=cols)
    for c in cols:
        s = pd.to_datetime(df[c], errors="coerce")
        if s.notna().sum() == 0:
            continue
        days = (s.max() - s.min()).days
        print(f"{t:24} {c:16} {str(s.min())[:19]:20} {str(s.max())[:19]:20} "
              f"{days:>6} {days/30.44:>7.1f}")

print("\n" + "=" * 60)
print("EVENT TABLES ONLY (the actual observation window)")

ev = ["calls","call_attempts","call_dispositions","payments","promises_to_pay",
      "field_visits","whatsapp_events","sms_events","complaints",
      "account_status_history"]

allmins, allmaxs = [], []
for t in ev:
    s = pd.to_datetime(pd.read_csv(f"{RAW}/{t}.csv", usecols=["event_at"]).event_at)
    allmins.append(s.min()); allmaxs.append(s.max())

lo, hi = min(allmins), max(allmaxs)
print(f"earliest event across all tables : {lo}")
print(f"latest   event across all tables : {hi}")
print(f"span                             : {(hi-lo).days} days = {(hi-lo).days/30.44:.1f} months")

print("\nRow counts per calendar month (are any months partial?):")
counts = {}
for t in ev:
    s = pd.to_datetime(pd.read_csv(f"{RAW}/{t}.csv", usecols=["event_at"]).event_at)
    counts[t] = s.dt.to_period("M").value_counts().sort_index()
cm = pd.DataFrame(counts).fillna(0).astype(int)
cm["TOTAL"] = cm.sum(axis=1)
print(cm.to_string())

print("\nDistinct calendar DAYS present per month (28-31 = complete):")
days_per_month = {}
for t in ev:
    s = pd.to_datetime(pd.read_csv(f"{RAW}/{t}.csv", usecols=["event_at"]).event_at)
    days_per_month[t] = s.dt.to_period("M").groupby(s.dt.date).first().value_counts().sort_index()
s_all = pd.concat([pd.to_datetime(pd.read_csv(f"{RAW}/{t}.csv", usecols=["event_at"]).event_at) for t in ev])
dd = s_all.dt.normalize().drop_duplicates().dt.to_period("M").value_counts().sort_index()
print(dd.to_string())