"""Within-lap design: every long full-throttle straight, indexed within its lap,
plus how much braking happened in the run-up to it (= harvest opportunity).

Fuel, tyres, tyre age, driver, track evolution are all identical within a lap,
so they cannot confound a comparison between straights of the same lap.
No pit filter needed — pit stops are irrelevant to a within-lap contrast.
"""
import json, os, numpy as np, pandas as pd, cfetch
W = pd.read_json("out/windows2.json")

def segments(c):
    c = c.sort_values("t").reset_index(drop=True)
    c["flat"] = (c.throttle >= 98) & (c.brake < 50) & (c.speed > 80)
    c["grp"] = (c.flat != c.flat.shift()).cumsum()
    out = []
    for g, x in c[c.flat].groupby("grp"):
        if len(x) < 10: continue
        dur = (x.t.iloc[-1]-x.t.iloc[0]).total_seconds()
        if dur < 3.0: continue
        out.append({"t0": x.t.iloc[0], "t1": x.t.iloc[-1], "dur": dur,
                    "v0": float(x.speed.iloc[0]), "v1": float(x.speed.max()),
                    "idx": x.index[0]})
    return pd.DataFrame(out), c

def t_between(c, t0, t1, lo, hi):
    x = c[(c.t >= t0) & (c.t <= t1)]
    v = x.speed.values.astype(float)
    if len(v) < 8 or v[0] > lo or v.max() < hi: return np.nan
    t = (x.t - x.t.iloc[0]).dt.total_seconds().values
    i = np.argmax(v >= lo); j = np.argmax(v >= hi)
    if j <= i or i == 0: return np.nan
    tl = np.interp(lo, [v[i-1], v[i]], [t[i-1], t[i]]) if v[i]!=v[i-1] else t[i]
    th = np.interp(hi, [v[j-1], v[j]], [t[j-1], t[j]]) if v[j]!=v[j-1] else t[j]
    return th - tl

rows = []
for _, w in W.iterrows():
    sk = int(w.session_key)
    laps = pd.DataFrame(json.load(open(f"data/laps_session_key={sk}.json")))
    laps["t0"] = pd.to_datetime(laps.date_start, format="ISO8601", errors="coerce")
    laps = laps.dropna(subset=["t0","lap_duration"])
    laps["t1"] = laps.t0 + pd.to_timedelta(laps.lap_duration, unit="s")
    for dn in sorted(laps.driver_number.unique()):
        k = cfetch.key_for("car_data", {"session_key": sk, "driver_number": int(dn),
                                        "date>": w.t0, "date<": w.t1})
        if not os.path.exists(k): continue
        c = pd.DataFrame(json.load(open(k)))
        if c.empty: continue
        c["t"] = pd.to_datetime(c.date, format="ISO8601")
        S, c = segments(c)
        if S.empty: continue
        for _, L in laps[(laps.driver_number==dn) &
                         laps.lap_number.between(w.lo_lap, w.hi_lap)].iterrows():
            sl = S[(S.t0 >= L.t0) & (S.t1 <= L.t1)].sort_values("t0").reset_index(drop=True)
            if len(sl) < 2: continue
            for i, s in sl.iterrows():
                # braking in the run-up: from end of previous straight to start of this one
                prev_end = sl.t1.iloc[i-1] if i > 0 else L.t0
                run = c[(c.t > prev_end) & (c.t < s.t0)]
                if len(run) < 3: continue
                dt = run.t.diff().dt.total_seconds().fillna(0.24)
                brake_s = float(dt[run.brake >= 50].sum())
                rows.append({"circuit": w.circuit, "event": f"{w.circuit}_{w.lap}",
                             "session_key": sk, "driver": int(dn), "lap": int(L.lap_number),
                             "straight": i, "n_straights": len(sl),
                             "t0": s.t0, "t1": s.t1, "dur": s.dur, "v0": s.v0, "v1": s.v1,
                             "brake_before_s": brake_s,
                             "v_drop_before": float(run.speed.max()-run.speed.min()),
                             "runup_s": float((s.t0-prev_end).total_seconds()),
                             "dep_lap": int(w.lap), "end_lap": int(w.end_lap)})
R = pd.DataFrame(rows)
print(f"straight-laps: {len(R)}  circuits {R.circuit.nunique()}  drivers {R.driver.nunique()}")
print("\nstraights per lap:"); print(R.groupby("circuit").n_straights.median().to_string())
print("\nbrake-before variation (s) within circuit x straight:")
v = R.groupby(["circuit","straight"]).brake_before_s.agg(["size","mean","std"])
print(v[v["size"]>=40].round(2).head(16).to_string())
R.to_parquet("out/withinlap_raw.parquet")
