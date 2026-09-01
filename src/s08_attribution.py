import pandas as pd

RAW = "data/raw"
CR = 1e7

pay = pd.read_csv(f"{RAW}/payments.csv").drop_duplicates("payment_id", keep="first")
pay["event_at"] = pd.to_datetime(pay.event_at)
succ = pay[pay.payment_status == "SUCCESS"][["account_id","event_at","amount"]].copy()

def load(name, chan):
    d = pd.read_csv(f"{RAW}/{name}.csv", usecols=["account_id","event_at"])
    d["event_at"] = pd.to_datetime(d.event_at)
    d["channel"] = chan
    return d

events = pd.concat([
    load("calls", "VOICE"),
    load("whatsapp_events", "WHATSAPP"),
    load("sms_events", "SMS"),
    load("field_visits", "FIELD"),
]).sort_values("event_at")

print("Event volume by channel:")
vol = events.channel.value_counts()
print(pd.DataFrame({"events": vol, "share_%": (100*vol/len(events)).round(1)}).to_string())

succ = succ.sort_values("event_at")
m = pd.merge_asof(succ, events, on="event_at", by="account_id",
                  direction="backward", suffixes=("", "_ev"))

print(f"\npayments with a prior interaction: {m.channel.notna().sum():,} of {len(m):,}")

att = m.groupby("channel").agg(payments=("amount","size"), rs_cr=("amount", lambda x: x.sum()/CR))
att["att_share_%"] = (100*att.payments/att.payments.sum()).round(1)
att["vol_share_%"] = (100*vol/len(events)).round(1)
att["ratio"] = (att["att_share_%"]/att["vol_share_%"]).round(2)
print("\nLAST-TOUCH attribution vs volume share:")
print(att.round(2).to_string())

for w in [1, 3, 7, 30]:
    mw = m[(m.event_at - m.event_at_ev).dt.days <= w] if "event_at_ev" in m else None
print("\nAttribution window sensitivity (share of payments credited to each channel, %):")
m["gap_d"] = (m.event_at - m.groupby("account_id").event_at.transform("min")).dt.days
print("\nAttribution window sensitivity:")
rows = {}
for w in [1, 3, 7, 30, 90]:
    mw = pd.merge_asof(succ, events, on="event_at", by="account_id",
                       direction="backward", tolerance=pd.Timedelta(days=w))
    share = mw.channel.value_counts(normalize=True).mul(100).round(1)
    share["_unattributed_%"] = round(100 * mw.channel.isna().mean(), 1)
    rows[f"{w}d"] = share
print(pd.DataFrame(rows).to_string())