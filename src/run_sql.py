import os, duckdb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

con = duckdb.connect("collections.db")
for f in ["00_sources", "01_clean", "02_golden", "03_metrics", "04_forensics", "05_analysis"]:
    sql = open(f"sql/{f}.sql").read().replace("'data/raw/", f"'{ROOT}/data/raw/")
    con.execute(sql)
    print(f"ok  {f}")

print()
print(con.sql("SELECT * FROM golden.contract_checks").df().to_string(index=False))
print()
print(con.sql("SELECT * FROM clean.waterfall").df().to_string(index=False))
print("\n### VERDICT")
print(con.sql("SELECT * FROM analysis.verdict").df().to_string(index=False))

print("\n### CALENDAR EFFECT")
print(con.sql("SELECT * FROM analysis.calendar_effect").df().to_string(index=False))

print("\n### MONTHLY METRICS")
print(con.sql("""
  SELECT month, recovered_cr, recovered_cr_per_day, contact_rate_pct,
         rpc_rate_pct, ptp_rate_pct, recovery_per_agent_hour
  FROM metrics.monthly
""").df().to_string(index=False))