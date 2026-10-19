"""Honesty check #1: quali has a full battery and no saving.
If the plateau is DRAG, quali tops out the same. If it's the BATTERY, quali goes faster."""
import json, numpy as np, pandas as pd

def load(sk, dn, lo, hi):
    d = pd.DataFrame(json.load(open(f"data/car_data_driver_number={dn}&session_key={sk}.json")))
    d["t"] = pd.to_datetime(d.date, format="ISO8601")
    d = d.sort_values("t")
    d = d[(d.t >= lo) & (d.t <= hi)]
    d["flat"] = (d.throttle >= 98) & (d.brake < 50) & (d.speed > 100)
    d["grp"] = (d.flat != d.flat.shift()).cumsum()
    return d

def segs(d, min_dur=4):
    s = (d[d.flat].groupby("grp").agg(t0=("t","min"), t1=("t","max"),
         n=("speed","size"), vmax=("speed","max"))
         .assign(dur=lambda x: (x.t1-x.t0).dt.total_seconds()))
    return s[(s.dur >= min_dur) & (s.n >= 12)]

rows = []
for dn in [1, 16, 63]:
    q = segs(load(11357, dn, "2026-09-05 14:00", "2026-09-05 15:10"))
    r = segs(load(11361, dn, "2026-09-06 13:00", "2026-09-06 15:05"))
    rows.append({"driver": dn,
                 "quali_runs": len(q), "quali_vmax": q.vmax.max(), "quali_vmax_med": q.vmax.median(),
                 "race_runs": len(r), "race_vmax": r.vmax.max(), "race_vmax_med": r.vmax.median()})
t = pd.DataFrame(rows)
t["delta_median_kmh"] = t.quali_vmax_med - t.race_vmax_med
t["delta_best_kmh"]   = t.quali_vmax - t.race_vmax
print(t.to_string(index=False))
print("\nmean median-to-median delta: %+.1f km/h" % t.delta_median_kmh.mean())

# fraction of race straight-time spent at ~zero accel while flat out
d = load(11361, 1, "2026-09-06 13:00", "2026-09-06 15:05")
s = segs(d)
tot = held = 0
for _, x in s.iterrows():
    g = d[(d.t >= x.t0) & (d.t <= x.t1)]
    v = g.speed.values/3.6; te = (g.t - x.t0).dt.total_seconds().values
    if len(v) < 12: continue
    a = np.gradient(v, te)
    k = (te > 1) & (te < x.dur - .6)
    tot += k.sum(); held += ((np.abs(a) < 0.25) & k).sum()
print(f"\nVER race: {held/tot:.1%} of full-throttle time at |accel| < 0.25 m/s^2  (n={tot})")
