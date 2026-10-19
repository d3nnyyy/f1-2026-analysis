"""Build the pooled restart dataset per PREREG_pooled_sc.md."""
import json, numpy as np, pandas as pd, cfetch, os

W = pd.read_json("out/windows2.json")
rows = []
for _, w in W.iterrows():
    sk = int(w.session_key)
    laps = pd.DataFrame(json.load(open(f"data/laps_session_key={sk}.json")))
    laps["t0"] = pd.to_datetime(laps.date_start, format="ISO8601", errors="coerce")
    laps = laps.dropna(subset=["t0","lap_duration"])
    laps["t1"] = laps.t0 + pd.to_timedelta(laps.lap_duration, unit="s")
    stints = pd.DataFrame(json.load(open(f"data/stints_session_key={sk}.json")))

    for dn in sorted(laps.driver_number.unique()):
        k = cfetch.key_for("car_data", {"session_key": sk, "driver_number": int(dn),
                                        "date>": w.t0, "date<": w.t1})
        if not os.path.exists(k): continue
        car = pd.DataFrame(json.load(open(k)))
        if car.empty: continue
        car["t"] = pd.to_datetime(car.date, format="ISO8601")
        car = car.sort_values("t").reset_index(drop=True)
        car["flat"] = (car.throttle >= 98) & (car.brake < 50) & (car.speed > 100)
        car["grp"] = (car.flat != car.flat.shift()).cumsum()
        seg = car[car.flat].groupby("grp").agg(t0=("t","min"), t1=("t","max"),
                                               v0=("speed","first"), n=("speed","size"))
        seg = seg[seg.n >= 12]
        # pit-stop filter: did a stint boundary fall inside the window?
        ds = stints[stints.driver_number == dn]
        pitted = bool(((ds.lap_start > w.lo_lap) & (ds.lap_start <= w.hi_lap)).any())

        dl = laps[(laps.driver_number == dn) & laps.lap_number.between(w.lo_lap, w.hi_lap)]
        for _, L in dl.iterrows():
            g = car[(car.t >= L.t0) & (car.t <= L.t1)]
            if len(g) < 30: continue
            i = g.speed.idxmax(); tv = g.loc[i, "t"]
            hit = seg[(seg.t0 <= tv) & (seg.t1 >= tv)]
            if len(hit) != 1: continue
            st = ds[(ds.lap_start <= L.lap_number) & (ds.lap_end >= L.lap_number)]
            rows.append({
                "circuit": w.circuit, "event": f"{w.circuit}_{w.lap}", "session_key": sk,
                "driver": int(dn), "lap": int(L.lap_number),
                "vmax": float(g.speed.max()), "t_at_vmax": tv,
                "v_entry": float(hit.v0.iloc[0]),
                "accel_time": float((tv - hit.t0.iloc[0]).total_seconds()),
                "dep_lap": int(w.lap), "end_lap": int(w.end_lap), "sc_laps": int(w.sc_laps),
                "pitted_in_window": pitted,
                "compound": st.compound.iloc[0] if len(st) else None,
                "tyre_age": (L.lap_number - st.lap_start.iloc[0] + (st.tyre_age_at_start.iloc[0] or 0)) if len(st) else np.nan,
            })
D = pd.DataFrame(rows)
print("raw trap rows:", len(D), " events:", D.event.nunique(), " drivers:", D.driver.nunique())

# attach gap, derived from lap timing (no API calls; validated in gaps.py)
import gaps
G = pd.concat([gaps.gaps_for(sk).assign(session_key=sk) for sk in D.session_key.unique()])
D = D.merge(G, on=["session_key","driver","lap"], how="left")
D["gap"] = D.gap_track

# pre-registered window labels
D["phase"] = np.select(
    [D.lap.between(D.dep_lap-8, D.dep_lap-2),
     D.lap.between(D.end_lap+1, D.end_lap+2),
     D.lap.between(D.end_lap+3, D.end_lap+5)],
    ["baseline", "restart", "decay"], default="excluded")
D.to_parquet("out/pooled_sc.parquet")
print("\nphase counts (before filters):")
print(D.phase.value_counts().to_string())
print(f"\ndriver-events dropped by pit filter: {D[D.pitted_in_window].groupby(['event','driver']).ngroups}"
      f" of {D.groupby(['event','driver']).ngroups}")
print(f"gap coverage: track {D.gap_track.notna().mean():.0%}  class {D.gap_class.notna().mean():.0%}")
