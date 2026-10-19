"""Teammate comparison: the only fair way to separate DRIVER from CAR."""
import numpy as np, pandas as pd, statsmodels.formula.api as smf, warnings
warnings.simplefilter("ignore")
D = pd.read_parquet("out/pace_fitted.parquet")
BASE = "C(circuit) + race_frac + C(compound) + tyre_age + np.log1p(gap_track)"
rows = []
for t, g in D.groupby("team"):
    fams = g.family.value_counts()
    fams = fams[fams >= 200]
    if len(fams) < 2: continue
    g = g[g.family.isin(fams.index)]
    ref = fams.index[0]                    # most laps = reference
    g = g.copy(); g["fam"] = pd.Categorical(g.family, categories=[ref]+[f for f in fams.index if f != ref])
    try:
        m = smf.ols(f"log_lap ~ C(fam) + {BASE}", data=g).fit(
            cov_type="cluster", cov_kwds={"groups": g.circuit + "_" + g.driver_number.astype(str)})
    except Exception as e:
        print(f"  {t}: {e}"); continue
    for f in fams.index:
        if f == ref:
            rows.append({"team": t, "driver": f, "delta": 0.0, "lo": 0.0, "hi": 0.0, "n": int(fams[f])})
        else:
            k = f"C(fam)[T.{f}]"
            if k not in m.params: continue
            lo, hi = m.conf_int().loc[k]
            rows.append({"team": t, "driver": f, "delta": m.params[k]*100,
                         "lo": lo*100, "hi": hi*100, "n": int(fams[f])})
R = pd.DataFrame(rows)
print("="*74)
print("TEAMMATE PACE GAP  (% per lap, negative = faster than the reference teammate)")
print("="*74)
for t, g in R.groupby("team"):
    g = g.sort_values("delta")
    base = g.iloc[0].driver
    print(f"\n  {t}")
    for r in g.itertuples():
        rel = r.delta - g.delta.min()
        ci = "" if r.hi == r.lo == 0 else f"  [{r.lo:+.3f},{r.hi:+.3f}]"
        tag = "  <-- quicker" if rel == 0 else ""
        print(f"    {r.driver[:13].ljust(13)} {rel:+.3f}%{ci.ljust(20)} n={r.n}{tag}")
R.to_csv("out/teammate_gaps.csv", index=False)

print("\n" + "="*74)
print("HEAD-TO-HEAD, ranked by how convincingly one beat the other")
print("="*74)
out = []
for t, g in R.groupby("team"):
    if len(g) != 2: continue
    g = g.sort_values("delta")
    fast, slow = g.iloc[0], g.iloc[1]
    gap = slow.delta - fast.delta
    sig = "yes" if (slow.lo > 0 or slow.hi < 0) else "no"
    out.append({"team": t, "faster": fast.driver, "slower": slow.driver,
                "gap_pct": gap, "clear": sig})
O = pd.DataFrame(out).sort_values("gap_pct", ascending=False)
for r in O.itertuples():
    print(f"  {r.faster[:12].ljust(12)} beats {r.slower[:12].ljust(12)} by {r.gap_pct:.3f}%/lap"
          f"   CI excludes 0: {r.clear}   ({r.team[:18]})")
