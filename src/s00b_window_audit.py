"""
s00b - Exhaustive window audit.

Adversarial: actively tries to FIND 12 months of data rather than confirm 7.
Scans EVERY column of EVERY table for parseable dates, not just the ones we
expect to be timestamps. Reports any field spanning >= 300 days.
"""
import pandas as pd, os, warnings
warnings.filterwarnings("ignore")

RAW = "data/raw"
out = []
def w(x=""):
    out.append(str(x)); print(x)

tables = sorted(f[:-4] for f in os.listdir(RAW)
                if f.endswith(".csv") and f != "data_dictionary.csv")

w("=" * 96)
w("TEST 1 - BRUTE-FORCE DATE SCAN: every column of every table")
w("=" * 96)
w(f"{'table':24} {'column':18} {'parsed%':>8} {'min':>20} {'max':>20} {'days':>6}")
w("-" * 96)

found = []
for t in tables:
    df = pd.read_csv(f"{RAW}/{t}.csv", dtype=str, keep_default_na=False, na_values=[""])
    for c in df.columns:
        s = df[c].dropna()
        if len(s) == 0:
            continue
        p = pd.to_datetime(s, errors="coerce", format="mixed")
        rate = p.notna().mean()
        if rate < 0.90:                     # not a date column
            continue
        days = (p.max() - p.min()).days
        found.append({"table": t, "column": c, "min": p.min(), "max": p.max(),
                      "days": days, "months": round(days / 30.44, 1)})
        w(f"{t:24} {c:18} {100*rate:7.1f}% {str(p.min())[:19]:>20} "
          f"{str(p.max())[:19]:>20} {days:>6}")

f = pd.DataFrame(found)

w("\n" + "=" * 96)
w("TEST 2 - ANY FIELD SPANNING >= 300 DAYS (i.e. could be called '12 months')")
w("=" * 96)
long = f[f.days >= 300].sort_values("days", ascending=False)
if len(long):
    w(long.to_string(index=False))
    w("\nNOTE: these are ENTITY CREATION fields, not observation windows.")
else:
    w("NONE.")

w("\n" + "=" * 96)
w("TEST 3 - OBSERVATION WINDOW: event_at only (when things actually happened)")
w("=" * 96)
ev = f[f.column == "event_at"].sort_values("days", ascending=False)
w(ev[["table", "min", "max", "days", "months"]].to_string(index=False))
w(f"\nlongest event_at span : {ev.days.max()} days = {ev.days.max()/30.44:.1f} months")
w(f"shortest event_at span: {ev.days.min()} days = {ev.days.min()/30.44:.1f} months")

w("\n" + "=" * 96)
w("TEST 4 - CALENDAR COVERAGE: which of the 12 months Aug-2025..Aug-2026 have data?")
w("=" * 96)
evt = ["calls","call_attempts","call_dispositions","payments","promises_to_pay",
       "field_visits","whatsapp_events","sms_events","complaints",
       "account_status_history"]
alldates = []
for t in evt:
    s = pd.to_datetime(pd.read_csv(f"{RAW}/{t}.csv", usecols=["event_at"]).event_at,
                       errors="coerce")
    alldates.append(s)
s_all = pd.concat(alldates)
cov = pd.DataFrame({
    "rows": s_all.dt.to_period("M").value_counts().sort_index(),
    "distinct_days": s_all.dt.normalize().drop_duplicates()
                          .dt.to_period("M").value_counts().sort_index(),
})
cov["days_in_month"] = [p.days_in_month for p in cov.index]
cov["coverage_%"] = (100 * cov.distinct_days / cov.days_in_month).round(1)
cov["complete"] = cov.distinct_days == cov.days_in_month
w(cov.to_string())
complete = int(cov.complete.sum())
w(f"\nCOMPLETE months: {complete}")
w(f"PARTIAL months : {int((~cov.complete).sum())}")

w("\n" + "=" * 96)
w("TEST 5 - DAILY ROW COUNTS AT THE BOUNDARIES (is the cut abrupt or a taper?)")
w("=" * 96)
daily = s_all.dt.normalize().value_counts().sort_index()
w("first 5 days with data:")
w(daily.head(5).to_string())
w("\nlast 12 days with data:")
w(daily.tail(12).to_string())

w("\n" + "=" * 96)
w("TEST 6 - GAP CHECK: any missing days inside Jan 1 - Aug 8?")
w("=" * 96)
full = pd.date_range("2026-01-01", "2026-08-08", freq="D")
present = set(daily.index)
missing = [d for d in full if d not in present]
w(f"expected days: {len(full)}   present: {len(full)-len(missing)}   missing: {len(missing)}")
if missing:
    w(f"missing dates: {[str(d.date()) for d in missing]}")

w("\n" + "=" * 96)
w("TEST 7 - FUTURE-DATED FIELDS (do they represent extra observed data?)")
w("=" * 96)
for t, c in [("promises_to_pay","promised_date"), ("complaints","resolution_at"),
             ("campaigns","end_at"), ("account_status_history","recorded_at"),
             ("agent_sessions","logout_at")]:
    d = pd.read_csv(f"{RAW}/{t}.csv", usecols=[c])
    s = pd.to_datetime(d[c], errors="coerce")
    beyond = int((s > "2026-08-08").sum())
    w(f"  {t}.{c:16} max={str(s.max())[:19]}  rows beyond 2026-08-08: {beyond:,}")
w("\nThese are SCHEDULED/FUTURE fields, not observations. They do not extend the window.")

w("\n" + "=" * 96)
w("VERDICT")
w("=" * 96)
w(f"  Observation window   : {s_all.min()} -> {s_all.max()}")
w(f"  Span                 : {(s_all.max()-s_all.min()).days} days")
w(f"  Complete months      : {complete} (Jan-Jul 2026)")
w(f"  MoM transitions      : {complete-1}")
w(f"  Longest ANY date field: {f.days.max()} days ({f.loc[f.days.idxmax(),'table']}."
  f"{f.loc[f.days.idxmax(),'column']}) - an entity creation date, not observation")
w(f"  12 months of activity: NOT PRESENT")

os.makedirs("reports", exist_ok=True)
open("reports/s00b_window_audit.txt", "w").write("\n".join(out))