import json, time, urllib.request, os
B = "https://api.jolpi.ca/ergast/f1/2026/results.json"
rows, off = [], 0
while True:
    time.sleep(0.8)
    with urllib.request.urlopen(f"{B}?limit=100&offset={off}", timeout=60) as r:
        d = json.load(r)
    M = d["MRData"]; races = M["RaceTable"]["Races"]
    for rc in races:
        for res in rc["Results"]:
            rows.append({
                "round": int(rc["round"]), "raceName": rc["raceName"],
                "circuitId": rc["Circuit"]["circuitId"],
                "driverId": res["Driver"]["driverId"],
                "code": res["Driver"].get("code"),
                "number": int(res["Driver"].get("permanentNumber", 0)),
                "family": res["Driver"]["familyName"],
                "team": res["Constructor"]["name"],
                "grid": int(res["grid"]), "position": int(res["position"]),
                "points": float(res["points"]), "status": res["status"],
                "laps": int(res["laps"])})
    off += 100
    if off >= int(M["total"]): break
    print(f"  fetched {off}/{M['total']}", flush=True)
R = json.dumps(rows)
open("data/jolpica_results.json","w").write(R)
import pandas as pd
D = pd.DataFrame(rows)
print(f"\nresult rows: {len(D)}  races: {D['round'].nunique()}  drivers: {D.driverId.nunique()}")
print("\nteams and their drivers:")
for t, g in D.groupby("team"):
    print(f"  {t[:20].ljust(20)} {sorted(g.family.unique())}")
print("\nnon-finish statuses:")
print(D[~D.status.str.contains('Finished|\\+')].status.value_counts().head(10).to_string())
