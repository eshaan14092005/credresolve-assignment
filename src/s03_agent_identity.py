import pandas as pd

RAW = "data/raw"
agt = pd.read_csv(f"{RAW}/agents.csv")

print(f"rows: {len(agt):,}   distinct agent_id: {agt.agent_id.nunique():,}")

g = agt.groupby("agent_id").agg(
    rows=("employee_code", "size"),
    joined=("joined_at", "nunique"),
    emp=("employee_code", "nunique"),
    name=("agent_name", "nunique"),
    team=("team", "nunique"),
    vendor=("vendor_id", "nunique"),
)

print("\nDistinct values per agent_id:")
print(g.describe().loc[["min", "50%", "max"]].round(1).to_string())

print(f"\nagents with >1 joined_at : {(g.joined > 1).sum():,} of {len(g):,}")
print(f"agents with >1 name      : {(g.name > 1).sum():,} of {len(g):,}")

print(f"\nemployee_codes spanning >1 agent_id: "
      f"{agt.groupby('employee_code').agent_id.nunique().gt(1).sum():,} "
      f"of {agt.employee_code.nunique():,}")

print("\nExample agent:")
print(agt[agt.agent_id == "AGT0000001"]
      .sort_values("updated_at")
      .head(5)[["agent_id","employee_code","agent_name","vendor_id","team","joined_at"]]
      .to_string(index=False))