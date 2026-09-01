import pandas as pd

RAW = "data/raw"
CR = 1e7

pay = pd.read_csv(f"{RAW}/payments.csv")
pay["event_at"] = pd.to_datetime(pay["event_at"])

succ = pay[pay.payment_status == "SUCCESS"]
print(f"raw payment rows : {len(pay):,}")
print(f"SUCCESS rows     : {len(succ):,}")
print(f"SUCCESS total    : Rs {succ.amount.sum()/CR:.2f} Cr")
print("=" * 62)

print("\nLEVEL 1 - same payment_id")
l1_excess = pay[pay.duplicated("payment_id", keep="first")]
l1_involved = pay[pay.duplicated("payment_id", keep=False)]
l1_money = l1_excess.loc[l1_excess.payment_status == "SUCCESS", "amount"].sum()
exact = int(pay.duplicated().sum())

print(f"  rows involved          : {len(l1_involved):,}")
print(f"  excess rows to remove  : {len(l1_excess):,}")
print(f"  distinct ids affected  : {l1_involved.payment_id.nunique():,}")
print(f"  SUCCESS money at stake : Rs {l1_money/CR:.2f} Cr")
print(f"  exact full-row dups    : {exact:,}")
print(f"  conflicting            : {len(l1_excess) - exact:,}")

print("\nLEVEL 2 - same payment_reference, different payment_id")
ref = pay[pay.payment_reference.notna()].copy()
ref = ref.drop_duplicates("payment_id", keep="first")
l2_involved = ref[ref.duplicated("payment_reference", keep=False)]
l2_excess = ref[ref.duplicated("payment_reference", keep="first")]
l2_money = l2_excess.loc[l2_excess.payment_status == "SUCCESS", "amount"].sum()

print(f"  rows with a reference  : {len(ref):,}")
print(f"  excess rows            : {len(l2_excess):,}")
print(f"  SUCCESS money at stake : Rs {l2_money/CR:.2f} Cr")

grp = l2_involved.groupby("payment_reference").agg(
    accts=("account_id", "nunique"),
    amts=("amount", "nunique"),
)
print(f"  groups w/ diff account : {(grp.accts > 1).sum():,} of {len(grp):,}")
print(f"  groups w/ diff amount  : {(grp.amts > 1).sum():,} of {len(grp):,}")

n = ref.payment_reference.str.extract(r"TXN0*(\d+)")[0].astype(int)
pool, draws = n.max(), len(ref)
expected = pool * (1 - (1 - 1 / pool) ** draws)
print(f"  TXN pool size          : {pool:,}")
print(f"  expected distinct      : {expected:,.0f}")
print(f"  observed distinct      : {ref.payment_reference.nunique():,}")
print("  VERDICT: collisions are random, not retries. Do not dedup on reference.")

print("\nLEVEL 3 - same account + amount, close in time")
clean = (pay.drop_duplicates("payment_id", keep="first")
            .sort_values(["account_id", "amount", "event_at"]))
clean["prev"] = clean.groupby(["account_id", "amount"])["event_at"].shift()
clean["gap_s"] = (clean.event_at - clean.prev).dt.total_seconds()

for window in [10, 60, 300, 3600]:
    hit = clean[clean.gap_s.notna() & (clean.gap_s <= window)]
    money = hit.loc[hit.payment_status == "SUCCESS", "amount"].sum()
    print(f"  window <= {window:>4}s : {len(hit):>5,} rows   Rs {money/CR:>6.2f} Cr")

print("\n" + "=" * 62)
print("VERDICT: L1 only")

deduped = pay.drop_duplicates("payment_id", keep="first")
before = succ.amount.sum()
after = deduped.loc[deduped.payment_status == "SUCCESS", "amount"].sum()

print(f"  rows      {len(pay):,} -> {len(deduped):,}")
print(f"  SUCCESS   Rs {before/CR:.2f} Cr -> Rs {after/CR:.2f} Cr")
print(f"  inflation Rs {(before-after)/CR:.2f} Cr ({100*(before-after)/before:.2f}%)")

ded = deduped[deduped.payment_status == "SUCCESS"]
raw_m = succ.groupby(succ.event_at.dt.to_period("M")).amount.sum() / CR
ded_m = ded.groupby(ded.event_at.dt.to_period("M")).amount.sum() / CR

t = pd.DataFrame({"raw": raw_m, "deduped": ded_m})
t["removed_pct"] = 100 * (t.raw - t.deduped) / t.raw
print("\nMonthly SUCCESS recovery (Rs Cr):")
print(t.round(2).to_string())
print("\nMoM % change after dedup (Jan-Jul):")
print((ded_m[:-1].pct_change() * 100).round(2).to_string())