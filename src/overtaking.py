"""Overtaking under the 2026 regs — the question is NOT 'how many passes happened',
which depends on how much close racing there happened to be. It is the CONVERSION RATE:
given a car within one second, how often does a pass actually follow?"""
import json, numpy as np, pandas as pd
idx = [r for r in json.load(open("out/race_index.json")) if r["n_laps"] > 0]
rows = []
for r in idx:
    L = pd.DataFrame(json.load(open(f"data/laps_session_key={r['session_key']}.json")))
    L["t0"] = pd.to_datetime(L.date_start, format="ISO8601", errors="coerce")
    L = L.dropna(subset=["t0"])
    # order of crossing the line at the start of each lap = running order
    pos = []
    for lap, g in L.groupby("lap_number"):
        g = g.sort_values("t0")
        pos.append(pd.DataFrame({"lap": int(lap), "driver": g.driver_number.values,
                                 "pos": range(1, len(g)+1), "t": g.t0.values}))
    P = pd.concat(pos)
    P["gap_ahead"] = P.groupby("lap").t.diff().dt.total_seconds() if hasattr(P.t, "dt") else np.nan
    P["gap_ahead"] = P.groupby("lap")["t"].transform(lambda s: pd.Series(s).diff().dt.total_seconds().values
                                                     if hasattr(pd.Series(s), "dt") else np.nan)
    # simpler: recompute gaps directly
    g2 = []
    for lap, g in P.groupby("lap"):
        g = g.sort_values("pos")
        d = pd.Series(g.t.values).diff().astype("timedelta64[ns]").dt.total_seconds().values
        g2.append(g.assign(gap=d))
    P = pd.concat(g2)
    nxt = P[["lap","driver","pos"]].copy(); nxt["lap"] -= 1
    nxt = nxt.rename(columns={"pos":"pos_next"})
    P = P.merge(nxt, on=["lap","driver"], how="left")
    # pit stops: a car ahead pitting hands you a position that is not an overtake
    S = pd.DataFrame(json.load(open(f"data/stints_session_key={r['session_key']}.json")))
    pit = set()
    for _, st in S.iterrows():
        if st.lap_start and st.lap_start > 1:
            pit.add((int(st.driver_number), int(st.lap_start)))
            pit.add((int(st.driver_number), int(st.lap_start)-1))
    P["self_pit"] = [ (int(d), int(l)) in pit for d, l in zip(P.driver, P.lap) ]
    ahead = P[["lap","pos","driver"]].copy(); ahead["pos"] += 1
    ahead = ahead.rename(columns={"driver":"drv_ahead"})
    P = P.merge(ahead, on=["lap","pos"], how="left")
    P["ahead_pit"] = [ (int(d), int(l)) in pit if pd.notna(d) else False
                       for d, l in zip(P.drv_ahead, P.lap) ]
    P["circuit"] = r["circuit"]; P["session_key"] = r["session_key"]
    rows.append(P)
A = pd.concat(rows, ignore_index=True).dropna(subset=["pos_next","gap"])
A["passed"] = A.pos_next < A.pos        # moved forward by the next lap
A = A[A.gap.between(0, 30)]
n_pre = len(A)
A = A[(~A.self_pit) & (~A.ahead_pit)]
print(f"dropped {n_pre-len(A)} driver-laps where either car pitted ({(n_pre-len(A))/n_pre:.0%})")
print(f"driver-lap observations: {len(A)}  races {A.circuit.nunique()}")

print("\n" + "="*62)
print("PASS CONVERSION RATE by gap to the car ahead")
print("="*62)
A["bin"] = pd.cut(A.gap, [0,.5,1,1.5,2,3,5,10,30])
t = A.groupby("bin", observed=True).agg(n=("passed","size"), passes=("passed","sum"))
t["rate"] = t.passes/t.n
t["se"] = np.sqrt(t.rate*(1-t.rate)/t.n)
for b, r in t.iterrows():
    if r.n < 40: continue
    bar = "#" * int(r.rate*120)
    print(f"  {str(b).ljust(12)} n={int(r.n):>5}  {r.rate*100:>5.1f}% ±{r.se*196:.1f}  {bar}")

print("\n" + "="*62)
print("WITHIN 1 SECOND: conversion by circuit")
print("="*62)
C = A[A.gap < 1].groupby("circuit").agg(n=("passed","size"), rate=("passed","mean"))
C = C[C.n >= 40].sort_values("rate", ascending=False)
for c, r in C.iterrows():
    print(f"  {c[:18].ljust(18)} {r.rate*100:>5.1f}%   (n={int(r.n)})")
print(f"\n  season-wide, within 1 s: {A[A.gap<1].passed.mean()*100:.1f}%  (n={int((A.gap<1).sum())})")
print(f"  beyond 3 s            : {A[A.gap>3].passed.mean()*100:.1f}%  (n={int((A.gap>3).sum())})")
A.drop(columns=["bin"]).to_parquet("out/overtaking.parquet")
