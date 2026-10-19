"""If the car has TWO power states (electric deploying vs not), then at a given
speed the delivered power should cluster into two groups. Drag alone gives one.
Power at full throttle ~ m*a*v + drag(v); within a narrow speed bin drag is
near-constant, so a*v is a proxy for engine power."""
import json, numpy as np, pandas as pd
from scipy import stats

def power_proxy(sk, dn, lo, hi):
    d = pd.DataFrame(json.load(open(f"data/car_data_driver_number={dn}&session_key={sk}.json")))
    d["t"] = pd.to_datetime(d.date, format="ISO8601"); d = d.sort_values("t")
    d = d[(d.t >= lo) & (d.t <= hi)]
    d["flat"] = (d.throttle >= 98) & (d.brake < 50) & (d.speed > 100)
    d["grp"] = (d.flat != d.flat.shift()).cumsum()
    out = []
    for g, x in d[d.flat].groupby("grp"):
        if len(x) < 15: continue
        te = (x.t - x.t.iloc[0]).dt.total_seconds().values
        if te[-1] < 5: continue
        v = x.speed.values / 3.6
        a = np.gradient(v, te)
        k = (te > 1) & (te < te[-1] - .6)
        out.append(pd.DataFrame({"v": x.speed.values[k], "a": a[k], "P": (a*v)[k]}))
    return pd.concat(out) if out else pd.DataFrame()

for dn in [1, 63]:
    D = power_proxy(11361, dn, "2026-09-06 13:00", "2026-09-06 15:05")
    print(f"\n=== driver {dn}, Monza race, n={len(D)} ===")
    print(f"{'speed bin':>12} {'n':>5} {'mean P':>8} {'sd':>7} {'skew':>7} {'dip p':>8} {'bimodal?':>9}")
    for lo_ in range(240, 330, 15):
        s = D[(D.v >= lo_) & (D.v < lo_+15)]
        if len(s) < 60: continue
        P = s.P.values
        # Hartigan-style check via kurtosis + a 2-component vs 1-component BIC comparison
        k1 = stats.kurtosis(P)
        # crude bimodality coefficient: (skew^2 + 1) / kurtosis ; > 0.555 suggests bimodal
        bc = (stats.skew(P)**2 + 1) / (k1 + 3)
        print(f"{lo_:>5}-{lo_+15:<6} {len(P):>5} {P.mean():>8.1f} {P.std():>7.1f} {stats.skew(P):>7.2f} {bc:>8.3f} {'YES' if bc>0.555 else 'no':>9}")
