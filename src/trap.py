"""v2: per-lap speed trap on Monza's main straight.

POSITIVE CONTROL first. Slipstream is a known, large, well-understood effect:
a car within ~1s of the car ahead gets a tow worth ~10-15 km/h at Monza.
If this pipeline cannot recover THAT, it cannot be trusted to find anything subtler,
and I should stop. Only if the tow shows up do I look for an energy signal.
"""
import json, glob, numpy as np, pandas as pd, warnings
import statsmodels.formula.api as smf
warnings.simplefilter("ignore")

SK = 11361
laps   = pd.DataFrame(json.load(open(f"data/laps_session_key={SK}.json")))
stints = pd.DataFrame(json.load(open(f"data/stints_session_key={SK}.json")))
laps["t0"] = pd.to_datetime(laps.date_start, format="ISO8601")
laps = laps.dropna(subset=["t0", "lap_duration"])
laps["t1"] = laps.t0 + pd.to_timedelta(laps.lap_duration, unit="s")

rows = []
for f in glob.glob(f"data/car_data_driver_number=*&session_key={SK}.json"):
    dn = int(f.split("driver_number=")[1].split("&")[0])
    car = pd.DataFrame(json.load(open(f)))
    car["t"] = pd.to_datetime(car.date, format="ISO8601")
    car = car.sort_values("t")
    try:
        iv = pd.DataFrame(json.load(open(f"data/intervals_driver_number={dn}&session_key={SK}.json")))
    except FileNotFoundError:
        continue
    if iv.empty: continue
    iv["t"] = pd.to_datetime(iv.date, format="ISO8601")
    iv["gap"] = pd.to_numeric(iv.interval, errors="coerce")   # "+1 LAP" -> NaN
    iv = iv.dropna(subset=["gap"]).sort_values("t")
    for _, L in laps[laps.driver_number == dn].iterrows():
        g = car[(car.t >= L.t0) & (car.t <= L.t1)]
        if len(g) < 40: continue
        i = g.speed.idxmax()
        rows.append({"driver": dn, "lap": int(L.lap_number), "vmax": float(g.speed.max()),
                     "t_at_vmax": g.loc[i, "t"], "lap_time": float(L.lap_duration)})
    pass
T = pd.DataFrame(rows)
if T.empty: raise SystemExit("no trap rows")

# attach gap to car ahead at the instant of the trap
out = []
for dn, g in T.groupby("driver"):
    iv = pd.DataFrame(json.load(open(f"data/intervals_driver_number={dn}&session_key={SK}.json")))
    iv["t"] = pd.to_datetime(iv.date, format="ISO8601")
    iv["gap"] = pd.to_numeric(iv.interval, errors="coerce")
    iv = iv.dropna(subset=["gap"]).sort_values("t")
    g = g.sort_values("t_at_vmax")
    out.append(pd.merge_asof(g, iv[["t","gap"]], left_on="t_at_vmax", right_on="t",
                             direction="nearest", tolerance=pd.Timedelta("8s")))
T = pd.concat(out)

# attach compound / tyre age
st = []
for _, s in stints.iterrows():
    for lp in range(int(s.lap_start), int(s.lap_end)+1):
        st.append({"driver": s.driver_number, "lap": lp, "compound": s.compound,
                   "tyre_age": lp - s.lap_start + (s.tyre_age_at_start or 0)})
T = T.merge(pd.DataFrame(st), on=["driver","lap"], how="left")
T = T[(T.vmax > 280) & (T.lap > 1)]
T["tow"] = (T.gap < 1.0)
T["clean"] = (T.gap > 2.0)

print(f"trap rows: {len(T)}   drivers: {T.driver.nunique()}   laps: {T.lap.min()}-{T.lap.max()}")
print(f"gap available on {T.gap.notna().mean():.0%} of rows\n")
print("vmax by air condition:")
print(T.assign(air=np.where(T.tow,"tow (<1s)", np.where(T.clean,"clean (>2s)","middle")))
       .groupby("air").vmax.agg(["size","mean","median","std"]).round(1).to_string())

print("\n=== POSITIVE CONTROL: does the tow show up? ===")
m = smf.ols("vmax ~ tow + C(driver)", data=T.dropna(subset=["gap"])).fit()
ci = m.conf_int().loc["tow[T.True]"]
print(f"  tow effect: {m.params['tow[T.True]']:+.2f} km/h  95% CI [{ci[0]:+.2f}, {ci[1]:+.2f}]  p={m.pvalues['tow[T.True]']:.2g}")
m2 = smf.ols("vmax ~ np.log1p(gap) + C(driver)", data=T.dropna(subset=["gap"])).fit()
print(f"  log(gap) slope: {m2.params['np.log1p(gap)']:+.2f} km/h per e-fold  p={m2.pvalues['np.log1p(gap)']:.2g}")
T.to_parquet("out/monza_trap.parquet")
print("\nsaved out/monza_trap.parquet")
