"""Corner-entry covariate: the speed the car ENTERS the main straight at.
This absorbs tyre grip and track evolution, which both raise corner-exit speed
and would otherwise masquerade as a power effect."""
import json, glob, numpy as np, pandas as pd
SK = 11361
T = pd.read_parquet("out/monza_trap.parquet")
rows = []
for f in glob.glob(f"data/car_data_driver_number=*&session_key={SK}.json"):
    dn = int(f.split("driver_number=")[1].split("&")[0])
    sub = T[T.driver == dn]
    if sub.empty: continue
    car = pd.DataFrame(json.load(open(f)))
    car["t"] = pd.to_datetime(car.date, format="ISO8601")
    car = car.sort_values("t").reset_index(drop=True)
    car["flat"] = (car.throttle >= 98) & (car.brake < 50) & (car.speed > 100)
    car["grp"] = (car.flat != car.flat.shift()).cumsum()
    seg = car[car.flat].groupby("grp").agg(t0=("t","min"), t1=("t","max"),
                                           v0=("speed","first"), n=("speed","size"))
    seg = seg[seg.n >= 12]
    for _, r in sub.iterrows():
        tv = r.t_at_vmax
        hit = seg[(seg.t0 <= tv) & (seg.t1 >= tv)]
        if len(hit) == 1:
            rows.append({"driver": dn, "lap": r.lap, "v_entry": float(hit.v0.iloc[0]),
                         "accel_time": float((tv - hit.t0.iloc[0]).total_seconds())})
E = pd.DataFrame(rows)
print(f"entry speeds recovered for {len(E)} / {len(T)} trap laps")
T2 = T.merge(E, on=["driver","lap"], how="left")
T2.to_parquet("out/monza_trap2.parquet")
print(T2[["vmax","v_entry","accel_time"]].describe().round(1).to_string())
