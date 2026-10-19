"""Select usable SC events and build the exact fetch job list."""
import json, pandas as pd, numpy as np
E = pd.read_csv("out/sc_events.csv")
idx = {r["session_key"]: r for r in json.load(open("out/race_index.json")) if r["n_laps"]>0}
PRE, POST = 8, 6          # need >=8 clean laps before, >=6 after the restart

rows = []
for sk, g in E.groupby("session_key"):
    laps = pd.DataFrame(json.load(open(f"data/laps_session_key={sk}.json")))
    maxlap = int(laps.lap_number.max())
    ev = sorted(g.lap.dropna().astype(int).tolist())
    for i, L in enumerate(ev):
        prev_ev = ev[i-1] if i > 0 else -99
        next_ev = ev[i+1] if i < len(ev)-1 else 10**6
        clean_before = L - prev_ev > PRE + 3
        room_before  = L - PRE >= 2
        room_after   = min(next_ev - 4, maxlap) - (L + 2) >= POST
        usable = clean_before and room_before and room_after
        rows.append({"circuit": idx[sk]["circuit"], "session_key": sk,
                     "kind": g[g.lap==L].kind.iloc[0], "lap": L, "maxlap": maxlap,
                     "usable": usable,
                     "why": "" if usable else
                            ("too early" if not room_before else
                             "prev event too close" if not clean_before else "no room after")})
U = pd.DataFrame(rows)
print(U.to_string(index=False))
ok = U[U.usable]
print(f"\nUSABLE: {len(ok)} of {len(U)} events, across {ok.session_key.nunique()} races")

# build time windows + job list
jobs, wins = [], []
for _, e in ok.iterrows():
    laps = pd.DataFrame(json.load(open(f"data/laps_session_key={e.session_key}.json")))
    laps["t0"] = pd.to_datetime(laps.date_start, format="ISO8601", errors="coerce")
    lo_lap, hi_lap = max(1, e.lap - PRE), min(e.maxlap, e.lap + POST + 3)
    t0 = laps[laps.lap_number == lo_lap].t0.min()
    t1 = laps[laps.lap_number == hi_lap].t0.max()
    if pd.isna(t0) or pd.isna(t1): continue
    t1 = t1 + pd.Timedelta(seconds=200)
    drivers = sorted(laps.driver_number.unique().tolist())
    wins.append({"session_key": int(e.session_key), "circuit": e.circuit, "kind": e.kind,
                 "lap": int(e.lap), "lo_lap": int(lo_lap), "hi_lap": int(hi_lap),
                 "t0": t0.strftime("%Y-%m-%dT%H:%M:%S"), "t1": t1.strftime("%Y-%m-%dT%H:%M:%S"),
                 "n_drivers": len(drivers)})
    for dn in drivers:
        jobs.append(["car_data", {"session_key": int(e.session_key), "driver_number": int(dn),
                                  "date>": t0.strftime("%Y-%m-%dT%H:%M:%S"),
                                  "date<": t1.strftime("%Y-%m-%dT%H:%M:%S")}])
json.dump(jobs, open("out/jobs_car.json","w"))
json.dump(wins, open("out/windows.json","w"), indent=1)
print(f"\ncar_data requests: {len(jobs)}")
print(f"window length: {np.mean([w['hi_lap']-w['lo_lap'] for w in wins]):.0f} laps avg")
print(f"estimated time at 26 req/min: {len(jobs)/26:.0f} min")
# intervals: whole race is small (~180 KB), one per driver per race
iv = []
for sk in ok.session_key.unique():
    laps = pd.DataFrame(json.load(open(f"data/laps_session_key={sk}.json")))
    for dn in sorted(laps.driver_number.unique().tolist()):
        iv.append(["intervals", {"session_key": int(sk), "driver_number": int(dn)}])
json.dump(iv, open("out/jobs_iv.json","w"))
print(f"intervals requests: {len(iv)}  -> total {len(jobs)+len(iv)} = {(len(jobs)+len(iv))/26:.0f} min")
