"""Join position (x,y) to speed, draw the track, and find where the car is fastest."""
import json, numpy as np, pandas as pd

def joined(sk, dn, lo, hi):
    loc = pd.DataFrame(json.load(open(f"data/location_driver_number={dn}&session_key={sk}.json")))
    car = pd.DataFrame(json.load(open(f"data/car_data_driver_number={dn}&session_key={sk}.json")))
    for d in (loc, car):
        d["t"] = pd.to_datetime(d.date, format="ISO8601")
    loc = loc[(loc.t >= lo) & (loc.t <= hi)].sort_values("t")
    car = car[(car.t >= lo) & (car.t <= hi)].sort_values("t")
    m = pd.merge_asof(loc[["t","x","y"]], car[["t","speed","throttle","brake","n_gear"]],
                      on="t", direction="nearest", tolerance=pd.Timedelta("150ms")).dropna()
    return m[(m.x != 0) | (m.y != 0)]

m = joined(11361, 1, "2026-09-06 13:05", "2026-09-06 15:00")
print("joined samples:", len(m))
print("x range:", m.x.min(), m.x.max(), " y range:", m.y.min(), m.y.max())
print("speed: max", m.speed.max(), " median", m.speed.median())

# strip pit lane / slow laps: keep only samples on the racing line at racing pace
fast = m[m.speed > 60]
print("\ntop-speed region (speed >= 345):")
tp = m[m.speed >= 345]
print(tp[["x","y","speed"]].describe().round(0).to_string())
m.to_parquet("out/monza_ver_xy.parquet")
