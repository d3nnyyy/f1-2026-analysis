"""Better test: not HOW FAST, but the SHAPE of the acceleration decay.
drag  -> acceleration eases toward zero smoothly, rarely pinned at exactly 0
power cut -> acceleration slams to ~0 and HOLDS there while throttle stays pinned."""
import json, numpy as np, pandas as pd

def load(sk, dn, lo, hi):
    d = pd.DataFrame(json.load(open(f"data/car_data_driver_number={dn}&session_key={sk}.json")))
    d["t"] = pd.to_datetime(d.date, format="ISO8601"); d = d.sort_values("t")
    d = d[(d.t >= lo) & (d.t <= hi)]
    d["flat"] = (d.throttle >= 98) & (d.brake < 50) & (d.speed > 100)
    d["grp"] = (d.flat != d.flat.shift()).cumsum()
    return d

def flat_fraction(d, vmin=280):
    """share of full-throttle time, above vmin, spent at ~zero acceleration,
    and the longest unbroken run of it"""
    s = (d[d.flat].groupby("grp").agg(t0=("t","min"), t1=("t","max"), n=("speed","size"))
         .assign(dur=lambda x: (x.t1-x.t0).dt.total_seconds()))
    s = s[(s.dur >= 5) & (s.n >= 15)]
    tot = held = 0; longest = []
    for _, x in s.iterrows():
        g = d[(d.t >= x.t0) & (d.t <= x.t1)]
        if len(g) < 15: continue
        te = (g.t - x.t0).dt.total_seconds().values
        v = g.speed.values / 3.6
        a = np.gradient(v, te)
        k = (te > 1) & (te < x.dur - .6) & (g.speed.values >= vmin)
        if k.sum() < 5: continue
        z = (np.abs(a) < 0.25) & k
        tot += k.sum(); held += z.sum()
        # longest consecutive zero-accel run, in seconds
        run = best = 0
        for i in range(len(z)):
            run = run + 1 if z[i] else 0
            best = max(best, run)
        longest.append(best * np.median(np.diff(te)))
    return len(s), tot, (held/tot if tot else np.nan), (np.median(longest) if longest else np.nan)

print(f"{'driver':>7} {'session':>6} {'runs':>5} {'n':>6} {'% at a~0':>9} {'median longest flat (s)':>24}")
for dn in [1, 16, 63]:
    for nm, sk, lo, hi in [("QUALI", 11357, "2026-09-05 14:00", "2026-09-05 15:10"),
                           ("RACE",  11361, "2026-09-06 13:00", "2026-09-06 15:05")]:
        r, n, f, L = flat_fraction(load(sk, dn, lo, hi))
        print(f"{dn:>7} {nm:>6} {r:>5} {n:>6} {f:>8.1%} {L:>24.2f}")
