"""Primary test per PREREG_accel.md. One fit."""
import numpy as np, pandas as pd, statsmodels.formula.api as smf, warnings
warnings.simplefilter("ignore")
A = pd.read_parquet("out/accel.parquet")
A["phase"] = np.select(
    [A.lap.between(A.dep_lap-8, A.dep_lap-2),
     A.lap.between(A.end_lap+1, A.end_lap+2),
     A.lap.between(A.end_lap+3, A.end_lap+5)],
    ["baseline","restart","decay"], default="excluded")
A = A[A.phase != "excluded"]
n0 = A.groupby(["event","driver"]).ngroups
A = A[~A.pitted_in_window]
print(f"driver-events after pit filter: {A.groupby(['event','driver']).ngroups} of {n0}")
A["restart"] = (A.phase=="restart").astype(int); A["decay"] = (A.phase=="decay").astype(int)
print(f"rows {len(A)}  units {A.unit.nunique()}  events {A.event.nunique()}")
print(A.phase.value_counts().to_string())

CL = {"cov_type":"cluster","cov_kwds":{"groups": A.unit}}
F = "log_t ~ restart + decay + lap + tow + np.log1p(gap) + v_seg_start + C(unit)"
m = smf.ols(F, data=A).fit(**CL)
print("\n" + "="*60); print("PRIMARY (pre-registered)"); print("="*60)
for k, lbl in [("restart","restart (end+1..+2)"), ("decay","decay (end+3..+5)")]:
    b = m.params[k]; lo, hi = m.conf_int().loc[k]
    print(f"  {lbl:<22} {b*100:+6.2f}%  95% CI [{lo*100:+6.2f}%,{hi*100:+6.2f}%]  p={m.pvalues[k]:.3g}")
lo, hi = m.conf_int().loc["restart"]
print(f"\n  achieved precision: +/-{(hi-lo)/2*100:.2f}%  (~{(hi-lo)/2*A.t_accel.median()*1000:.0f} ms)")
v = "NULL" if lo <= 0 <= hi else ("PASS (negative, as predicted)" if m.params["restart"]<0 else "WRONG-SIGN")
print(f"  P9 verdict : {v}")
print(f"  P10        : {'holds' if abs(m.params['decay']) < abs(m.params['restart']) else 'fails'}")

print("\n--- P11 dose-response on SC duration ---")
A["sc_c"] = A.sc_laps - A.sc_laps.mean()
m2 = smf.ols(F.replace("restart +","restart*sc_c +"), data=A).fit(
     cov_type="cluster", cov_kwds={"groups": A.unit})
k = [x for x in m2.params.index if "restart" in x and "sc_c" in x]
if k:
    b = m2.params[k[0]]; l2, h2 = m2.conf_int().loc[k[0]]
    print(f"  restart x sc_laps: {b*100:+.2f}%  [{l2*100:+.2f}%,{h2*100:+.2f}%]  pred NEGATIVE"
          f"  -> {'CI excludes 0' if not (l2<=0<=h2) else 'CI includes 0'}")
A.to_parquet("out/accel_analysis.parquet")
