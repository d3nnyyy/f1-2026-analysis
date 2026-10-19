"""Step 1: can we SEE the battery running out? No model yet, just looking."""
import json, numpy as np, pandas as pd

d = pd.DataFrame(json.load(open("data/car_data_driver_number=1&session_key=11361.json")))
d["t"] = pd.to_datetime(d.date, format="ISO8601")
d = d.sort_values("t").reset_index(drop=True)
print("time span:", d.t.min(), "->", d.t.max(), f"({(d.t.max()-d.t.min()).total_seconds()/60:.0f} min)")
print("\nthrottle distribution:"); print(d.throttle.describe().round(1).to_string())
print("\nbrake values:", sorted(d.brake.unique())[:10])
print("speed max:", d.speed.max(), " rpm max:", d.rpm.max(), " gears:", sorted(d.n_gear.dropna().unique()))

# sampling rate
dt = d.t.diff().dt.total_seconds()
print(f"\nsample interval: median {dt.median():.3f}s  p10 {dt.quantile(.1):.3f}  p90 {dt.quantile(.9):.3f}")

# full-throttle, no-brake, moving segments
d["flat"] = (d.throttle >= 98) & (d.brake < 50) & (d.speed > 100)
d["grp"] = (d.flat != d.flat.shift()).cumsum()
seg = (d[d.flat].groupby("grp")
        .agg(t0=("t","min"), t1=("t","max"), n=("speed","size"),
             v0=("speed","min"), v1=("speed","max"))
        .assign(dur=lambda x: (x.t1-x.t0).dt.total_seconds()))
seg = seg[(seg.dur >= 4) & (seg.n >= 12)].sort_values("dur", ascending=False)
print(f"\nsustained full-throttle segments (>=4s): {len(seg)}")
print(seg.head(8)[["t0","dur","n","v0","v1"]].to_string())
seg.to_csv("out/monza_ver_segments.csv")
d.to_parquet("out/monza_ver_telemetry.parquet")
