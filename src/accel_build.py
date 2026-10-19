"""Acceleration time: seconds to go from v_lo to v_hi at full throttle.
Unlike top speed (drag-dominated), this is directly power-sensitive.
Per-circuit bounds; log(t) with unit FE makes it a proportional, poolable measure."""
import json, os, numpy as np, pandas as pd, cfetch
W = pd.read_json("out/windows2.json")

# --- pass 1: per-circuit bounds ---
seg_stats = {}
cars = {}
for _, w in W.iterrows():
    sk = int(w.session_key)
    laps = pd.DataFrame(json.load(open(f"data/laps_session_key={sk}.json")))
    laps["t0"] = pd.to_datetime(laps.date_start, format="ISO8601", errors="coerce")
    laps = laps.dropna(subset=["t0","lap_duration"])
    laps["t1"] = laps.t0 + pd.to_timedelta(laps.lap_duration, unit="s")
    starts, ends = [], []
    for dn in sorted(laps.driver_number.unique()):
        k = cfetch.key_for("car_data", {"session_key": sk, "driver_number": int(dn),
                                        "date>": w.t0, "date<": w.t1})
        if not os.path.exists(k): continue
        c = pd.DataFrame(json.load(open(k)))
        if c.empty: continue
        c["t"] = pd.to_datetime(c.date, format="ISO8601"); c = c.sort_values("t")
        c["flat"] = (c.throttle >= 98) & (c.brake < 50) & (c.speed > 80)
        c["grp"] = (c.flat != c.flat.shift()).cumsum()
        cars[(sk, dn)] = (c, laps[laps.driver_number == dn])
        for g, x in c[c.flat].groupby("grp"):
            if len(x) < 15 or (x.t.iloc[-1]-x.t.iloc[0]).total_seconds() < 5: continue
            starts.append(x.speed.iloc[0]); ends.append(x.speed.max())
    if len(starts) < 30: continue
    lo = np.percentile(starts, 75) + 5
    hi = np.percentile(ends, 25) - 5
    seg_stats[w.circuit] = (lo, hi, hi - lo)

B = pd.DataFrame([{"circuit": k, "v_lo": v[0], "v_hi": v[1], "width": v[2]}
                  for k, v in seg_stats.items()]).sort_values("width")
print(B.round(0).to_string(index=False))
keep = set(B[B.width >= 40].circuit)
print(f"\ncircuits with >=40 km/h usable window: {len(keep)} of {len(B)}  -> {sorted(keep)}")

# --- pass 2: measure acceleration time per lap ---
def t_between(x, lo, hi):
    """interpolated seconds from first crossing of lo to first crossing of hi"""
    v = x.speed.values.astype(float)
    t = (x.t - x.t.iloc[0]).dt.total_seconds().values
    if v[0] > lo or v.max() < hi: return np.nan
    i = np.argmax(v >= lo); j = np.argmax(v >= hi)
    if j <= i or i == 0: return np.nan
    tl = np.interp(lo, [v[i-1], v[i]], [t[i-1], t[i]]) if v[i] != v[i-1] else t[i]
    th = np.interp(hi, [v[j-1], v[j]], [t[j-1], t[j]]) if v[j] != v[j-1] else t[j]
    return th - tl

rows = []
for _, w in W.iterrows():
    if w.circuit not in keep: continue
    lo, hi, _ = seg_stats[w.circuit]; sk = int(w.session_key)
    stints = pd.DataFrame(json.load(open(f"data/stints_session_key={sk}.json")))
    for (s2, dn), (c, dl) in cars.items():
        if s2 != sk: continue
        ds = stints[stints.driver_number == dn]
        pitted = bool(((ds.lap_start > w.lo_lap) & (ds.lap_start <= w.hi_lap)).any())
        for _, L in dl[dl.lap_number.between(w.lo_lap, w.hi_lap)].iterrows():
            g = c[(c.t >= L.t0) & (c.t <= L.t1)]
            if len(g) < 30: continue
            best = None
            for _, x in g[g.flat].groupby("grp"):
                if len(x) < 15: continue
                tt = t_between(x, lo, hi)
                if not np.isnan(tt) and (best is None or tt < best[0]):
                    best = (tt, x.t.iloc[0], x.speed.iloc[0])
            if best is None: continue
            rows.append({"circuit": w.circuit, "event": f"{w.circuit}_{w.lap}",
                         "session_key": sk, "driver": int(dn), "lap": int(L.lap_number),
                         "t_accel": best[0], "t_seg_start": best[1], "v_seg_start": best[2],
                         "dep_lap": int(w.lap), "end_lap": int(w.end_lap),
                         "sc_laps": int(w.sc_laps), "pitted_in_window": pitted,
                         "v_lo": lo, "v_hi": hi})
A = pd.DataFrame(rows)
print(f"\nlaps with a valid acceleration measurement: {len(A)}")
print(A.groupby("circuit").t_accel.agg(["size","median","std"]).round(2).to_string())
A.to_parquet("out/accel_raw.parquet")
