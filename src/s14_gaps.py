"""
Closes the remaining analysis gaps against the brief:
  Q2 dimensions : agent, campaign, telephony vendor, channel
  Part 3        : cohort effects
  Q3 metrics    : contact rate, RPC, recovery per agent-hour
"""
import pandas as pd, numpy as np

RAW, CR = "data/raw", 1e7
g = pd.read_parquet("output/golden_account_month.parquet")

acct = g.groupby("account_id").agg(
    recovered=("amount_recovered", "sum"),
    payments=("payments_success", "sum"),
).reset_index()
acct["paid"] = acct.payments > 0
BASE = acct.paid.mean()
print(f"baseline pay rate: {100*BASE:.2f}%   accounts: {len(acct):,}\n")


def spread(t, label):
    """Compare levels of a dimension against a binomial noise floor."""
    t["se_pp"] = (100 * np.sqrt(BASE * (1 - BASE) / t.accounts)).round(2)
    print(f"--- {label} ---")
    print(t.to_string())
    print(f"    spread {t.pay_rate.max()-t.pay_rate.min():.2f} pp | "
          f"2*median SE {2*t.se_pp.median():.2f} pp\n")


# ---------------------------------------------------------------- CAMPAIGN
calls = pd.read_csv(f"{RAW}/calls.csv").drop_duplicates()
calls["event_at"] = pd.to_datetime(calls.event_at)
calls = calls[(calls.event_at >= "2026-01-01") & (calls.event_at < "2026-08-01")]

camp = pd.read_csv(f"{RAW}/campaigns.csv")
print(f"campaigns: {len(camp)}  channels: {camp.channel.value_counts().to_dict()}")
print(f"strategy_versions: {camp.strategy_version.value_counts().to_dict()}")
print(f"target_definitions: {camp.target_definition.value_counts().to_dict()}\n")

ca = (calls[["account_id", "campaign_id"]].dropna().drop_duplicates()
      .merge(acct, on="account_id", how="left"))
t = ca.groupby("campaign_id").agg(accounts=("account_id", "size"),
                                  pay_rate=("paid", "mean"))
t["pay_rate"] = (100 * t.pay_rate).round(2)
print(f"--- campaign (n={len(t)}) ---")
print(f"    pay rate range {t.pay_rate.min():.2f}% to {t.pay_rate.max():.2f}% "
      f"(spread {t.pay_rate.max()-t.pay_rate.min():.2f} pp)")
print(f"    median accounts per campaign: {t.accounts.median():.0f}, "
      f"typical 2*SE {2*100*np.sqrt(BASE*(1-BASE)/t.accounts.median()):.2f} pp\n")

cc = ca.merge(camp[["campaign_id", "channel", "strategy_version", "target_definition"]],
              on="campaign_id", how="left")
for d in ["channel", "strategy_version", "target_definition"]:
    t = cc.groupby(d).agg(accounts=("account_id", "size"), pay_rate=("paid", "mean"))
    t["pay_rate"] = (100 * t.pay_rate).round(2)
    spread(t, f"campaign {d}")

# ---------------------------------------------------------------- VENDOR
vt = pd.read_csv(f"{RAW}/vendor_telephony.csv")
print(f"vendors: {len(vt)}  schema_versions: {vt.schema_version.value_counts().to_dict()}\n")

va = (calls[["account_id", "vendor_id"]].dropna().drop_duplicates()
      .merge(acct, on="account_id", how="left"))
t = va.groupby("vendor_id").agg(accounts=("account_id", "size"), pay_rate=("paid", "mean"))
t["pay_rate"] = (100 * t.pay_rate).round(2)
spread(t, "telephony vendor")

att = pd.read_csv(f"{RAW}/call_attempts.csv")
conn = (att.groupby("vendor_id").attempt_status
        .apply(lambda x: 100 * (x == "CONNECTED").mean()).round(2)
        .rename("connect_rate_%"))
print("--- vendor connect rate (independent of recovery) ---")
print(conn.to_string())
print(f"    spread {conn.max()-conn.min():.2f} pp\n")

# ---------------------------------------------------------------- AGENT
ag = (calls[["account_id", "agent_id"]].dropna().drop_duplicates()
      .merge(acct, on="account_id", how="left"))
t = ag.groupby("agent_id").agg(accounts=("account_id", "size"), pay_rate=("paid", "mean"))
t["pay_rate"] = 100 * t.pay_rate
print(f"--- agent (n={len(t)}, opaque key only) ---")
print(f"    pay rate p5={t.pay_rate.quantile(.05):.1f}%  median={t.pay_rate.median():.1f}%  "
      f"p95={t.pay_rate.quantile(.95):.1f}%")
obs_sd = t.pay_rate.std()
exp_sd = (100 * np.sqrt(BASE * (1 - BASE) / t.accounts.median()))
print(f"    observed SD across agents : {obs_sd:.2f} pp")
print(f"    SD expected if random     : {exp_sd:.2f} pp")
print(f"    ratio observed/expected   : {obs_sd/exp_sd:.2f}"
      "   (>1.2 = real agent differences)\n")

# ---------------------------------------------------------------- CHANNEL
print("--- channel: reach and volume (attribution rejected, see D12) ---")
ch = {}
for name, label in [("calls", "VOICE"), ("whatsapp_events", "WHATSAPP"),
                    ("sms_events", "SMS"), ("field_visits", "FIELD")]:
    d = pd.read_csv(f"{RAW}/{name}.csv", usecols=["account_id", "event_at"]).drop_duplicates()
    d["event_at"] = pd.to_datetime(d.event_at)
    d = d[(d.event_at >= "2026-01-01") & (d.event_at < "2026-08-01")]
    reach = d.account_id.nunique()
    pr = acct[acct.account_id.isin(d.account_id)].paid.mean()
    ch[label] = {"events": len(d), "accounts_reached": reach,
                 "pay_rate_%": round(100 * pr, 2)}
print(pd.DataFrame(ch).T.to_string(), "\n")

# ---------------------------------------------------------------- COHORT
accs = pd.read_csv(f"{RAW}/accounts.csv", usecols=["account_id", "opened_at"])
accs["cohort"] = pd.to_datetime(accs.opened_at).dt.to_period("Q")
co = accs.merge(acct, on="account_id", how="left")
t = co.groupby("cohort").agg(accounts=("account_id", "size"), pay_rate=("paid", "mean"))
t["pay_rate"] = (100 * t.pay_rate).round(2)
spread(t, "acquisition cohort (opened_at quarter)")

print("\n--- GRAIN MISMATCH: three incompatible definitions of 'contact' ---")
c_all = pd.read_csv(f"{RAW}/calls.csv").drop_duplicates()
d_all = pd.read_csv(f"{RAW}/call_dispositions.csv")
cid_conn = set(att[att.attempt_status == "CONNECTED"].call_id)
print(f"  calls with a CONNECTED attempt      : {len(cid_conn):,}")
print(f"  calls with call_status = ANSWERED   : {(c_all.call_status=='ANSWERED').sum():,}")
print(f"  calls with any disposition          : {d_all.call_id.nunique():,}")
print(f"  dispositions on a CONNECTED call    : {d_all.call_id.isin(cid_conn).sum():,} "
      f"of {len(d_all):,} ({100*d_all.call_id.isin(cid_conn).mean():.1f}%)")
print("  -> RPC and contact rate cannot be computed across these tables.")

# ---------------------------------------------------------------- METRICS
print("=" * 60)
print("PREVIOUSLY UNCOMPUTED METRICS")
att["event_at"] = pd.to_datetime(att.event_at)
att["month"] = att.event_at.dt.to_period("M")
att = att[att.month < "2026-08"]

m = att.groupby("month").agg(attempts=("attempt_id", "size"),
                             connected=("attempt_status", lambda x: (x == "CONNECTED").sum()))
m["contact_rate_%"] = (100 * m.connected / m.attempts).round(2)

disp = pd.read_csv(f"{RAW}/call_dispositions.csv")
disp["month"] = pd.to_datetime(disp.event_at).dt.to_period("M")
disp = disp[disp.month < "2026-08"]
RPC_CODES = ["PTP", "PROMISE_TO_PAY", "PAID", "REFUSED", "DISPUTE", "PTP_BROKEN"]
m["dispositions"] = disp.groupby("month").size()
m["rpc"] = disp[disp.disposition_code.isin(RPC_CODES)].groupby("month").size()
m["rpc_rate_%"] = (100 * m.rpc / m.dispositions).round(2)

ses = pd.read_csv(f"{RAW}/agent_sessions.csv")
ses["login_at"] = pd.to_datetime(ses.login_at)
ses["logout_at"] = pd.to_datetime(ses.logout_at)
ses["hours"] = (ses.logout_at - ses.login_at).dt.total_seconds() / 3600
ses["month"] = ses.login_at.dt.to_period("M")
ses = ses[ses.month < "2026-08"]
m["agent_hours"] = ses.groupby("month").hours.sum().round(0)
m["recovered_cr"] = g.groupby("month").amount_recovered.sum().values / CR
m["rs_per_agent_hour"] = (m.recovered_cr * CR / m.agent_hours).round(0)

print(m[["attempts", "contact_rate_%", "dispositions", "rpc_rate_%",
         "agent_hours", "rs_per_agent_hour"]].to_string())
print("\nMoM % change:")
print(m[["contact_rate_%", "rpc_rate_%", "rs_per_agent_hour"]]
      .pct_change().mul(100).round(2).to_string())
