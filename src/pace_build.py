"""Driver-lap dataset for all 17 races, with everything that isn't pace controlled for."""
import json, re, numpy as np, pandas as pd, gaps

idx = [r for r in json.load(open("out/race_index.json")) if r["n_laps"] > 0]
res = pd.DataFrame(json.loads(open("data/jolpica_results.json").read()))
# map circuit -> round via date order
order = sorted(idx, key=lambda r: r["date"])
rnd = {r["circuit"]: i+1 for i, r in enumerate(order)}

frames = []
for r in idx:
    sk = r["session_key"]
    L = pd.DataFrame(json.load(open(f"data/laps_session_key={sk}.json")))
    S = pd.DataFrame(json.load(open(f"data/stints_session_key={sk}.json")))
    if L.empty or S.empty: continue
    # SC / VSC laps from race control
    try:
        rc = pd.DataFrame(json.load(open(f"data/race_control_session_key={sk}.json")))
        rc["lap_number"] = pd.to_numeric(rc.lap_number, errors="coerce")
        msg = rc.message.astype(str).str.upper()
        bad = set()
        dep = rc[msg.str.contains("SAFETY CAR DEPLOYED|VSC DEPLOYED")].lap_number.dropna()
        end = rc[msg.str.contains("VSC ENDING|TRACK CLEAR|SAFETY CAR IN THIS LAP")].lap_number.dropna()
        for d in dep:
            e = end[end >= d].min()
            e = d + 3 if pd.isna(e) else e
            bad.update(range(int(d)-1, int(e)+2))
    except Exception:
        bad = set()
    recs = []
    for _, s in S.iterrows():
        m = ((L.driver_number == s.driver_number) &
             (L.lap_number >= s.lap_start) & (L.lap_number <= s.lap_end))
        x = L[m].copy()
        if x.empty: continue
        x["compound"] = s.compound
        x["tyre_age"] = x.lap_number - s.lap_start + (s.tyre_age_at_start or 0)
        x["stint_end"] = s.lap_end
        x["is_last"] = s.stint_number == S[S.driver_number == s.driver_number].stint_number.max()
        recs.append(x)
    if not recs: continue
    d = pd.concat(recs)
    d["circuit"] = r["circuit"]; d["session_key"] = sk; d["round"] = rnd[r["circuit"]]
    d["sc_lap"] = d.lap_number.isin(bad)
    G = gaps.gaps_for(sk)
    d = d.merge(G.rename(columns={"driver":"driver_number","lap":"lap_number"}),
                on=["driver_number","lap_number"], how="left")
    d["race_frac"] = d.lap_number / d.lap_number.max()
    frames.append(d)

D = pd.concat(frames, ignore_index=True)
n0 = len(D)
rep = []
def drop(mask, why):
    global D
    k = int(mask.sum()); D = D[~mask]; rep.append((why, k))
drop(~D.compound.isin(["SOFT","MEDIUM","HARD"]), "wet/unknown compound")
drop(D.lap_duration.isna(), "no lap time")
drop(D.is_pit_out_lap.fillna(False).astype(bool), "pit-out lap")
drop((D.lap_number == D.stint_end) & (~D.is_last), "pit-in lap")
drop(D.lap_number <= 1, "lap 1")
drop(D.sc_lap, "safety car / VSC laps")
med = D.groupby(["circuit","driver_number"]).lap_duration.transform("median")
drop(D.lap_duration > 1.06*med, ">106% of own race median (traffic/incident)")
med = D.groupby(["circuit","driver_number"]).lap_duration.transform("median")
drop(D.lap_duration < 0.93*med, "<93% of median (timing artefact)")
print(f"laps {n0} -> {len(D)}")
for w,k in rep: print(f"  -{str(k).rjust(6)}  {w}")

num2team = res.drop_duplicates(["number","round"])[["number","round","team","family","driverId"]]
D = D.merge(num2team, left_on=["driver_number","round"], right_on=["number","round"], how="left")
D["log_lap"] = np.log(D.lap_duration)
D["clean_air"] = (D.gap_track > 2.0) | D.gap_track.isna()
print(f"\nfinal: {len(D)} laps, {D.driver_number.nunique()} drivers, {D.circuit.nunique()} races")
print(f"team mapped on {D.team.notna().mean():.0%} of laps")
print(f"clean-air share: {D.clean_air.mean():.0%}")
D.to_parquet("out/pace_laps.parquet")
