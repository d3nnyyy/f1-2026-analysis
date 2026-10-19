"""Pass 2: standardised acceleration time per (circuit, straight), plus harvest proxies."""
import json, os, numpy as np, pandas as pd, cfetch
R = pd.read_parquet("out/withinlap_raw.parquet")
R = R[R.straight >= 1]                      # need a genuine preceding straight in the same lap
R = R[(R.runup_s > 1) & (R.runup_s < 30)]

# bounds per circuit x straight
b = R.groupby(["circuit","straight"]).agg(n=("v0","size"),
        lo=("v0", lambda s: np.percentile(s,75)+3),
        hi=("v1", lambda s: np.percentile(s,25)-3)).reset_index()
b["width"] = b.hi - b.lo
b = b[(b.n >= 40) & (b.width >= 30)]
print(f"usable (circuit,straight) cells: {len(b)}")
print(b.round(0).to_string(index=False))
BD = {(r.circuit, r.straight): (r.lo, r.hi) for r in b.itertuples()}

W = pd.read_json("out/windows2.json")
wmap = {int(w.session_key): w for _, w in W.iterrows()}
rows = []
for (sk, dn), g in R.groupby(["session_key","driver"]):
    w = wmap[sk]
    k = cfetch.key_for("car_data", {"session_key": int(sk), "driver_number": int(dn),
                                    "date>": w.t0, "date<": w.t1})
    if not os.path.exists(k): continue
    c = pd.DataFrame(json.load(open(k)))
    if c.empty: continue
    c["t"] = pd.to_datetime(c.date, format="ISO8601"); c = c.sort_values("t")
    for r in g.itertuples():
        key = (r.circuit, r.straight)
        if key not in BD: continue
        lo, hi = BD[key]
        x = c[(c.t >= r.t0) & (c.t <= r.t1)]
        v = x.speed.values.astype(float)
        if len(v) < 8 or v[0] > lo or v.max() < hi: continue
        tt = (x.t - x.t.iloc[0]).dt.total_seconds().values
        i = np.argmax(v >= lo); j = np.argmax(v >= hi)
        if j <= i or i == 0: continue
        tl = np.interp(lo,[v[i-1],v[i]],[tt[i-1],tt[i]]) if v[i]!=v[i-1] else tt[i]
        th = np.interp(hi,[v[j-1],v[j]],[tt[j-1],tt[j]]) if v[j]!=v[j-1] else tt[j]
        # harvest proxy: kinetic energy dissipated in the run-up, ~ d(v^2)
        prev = c[(c.t > r.t0 - pd.Timedelta(seconds=r.runup_s)) & (c.t < r.t0)]
        if len(prev) < 3: continue
        vt = prev.speed.values.astype(float)/3.6
        dv2 = float(max(vt)**2 - min(vt)**2)
        rows.append({**r._asdict(), "t_accel": th-tl, "v_lo": lo, "v_hi": hi,
                     "dv2_before": dv2, "brake_s": r.brake_before_s})
A = pd.DataFrame(rows).drop(columns=["Index"], errors="ignore")
A["log_t"] = np.log(A.t_accel)
A["unit"] = A.event + "_" + A.driver.astype(str) + "_s" + A.straight.astype(str)
print(f"\nmeasured straight-laps: {len(A)}  units(driver x event x straight): {A.unit.nunique()}")
print(A.groupby("circuit").t_accel.agg(["size","median","std"]).round(2).to_string())
A.to_parquet("out/withinlap.parquet")
