import numpy as np, pandas as pd, statsmodels.formula.api as smf, warnings, gaps
warnings.simplefilter("ignore")
A = pd.read_parquet("out/withinlap.parquet")
G = pd.concat([gaps.gaps_for(sk).assign(session_key=sk) for sk in A.session_key.unique()])
A = A.merge(G, on=["session_key","driver","lap"], how="left")
A["gap"] = A.gap_track
A = A.dropna(subset=["gap","t_accel","dv2_before"])
A = A[(A.gap>0)&(A.gap<60)&(A.t_accel>0.3)&(A.t_accel<20)&(A.dv2_before>0)]
A["tow"] = (A.gap<1).astype(int)
A["dv2k"] = A.dv2_before/1000.0          # per 1000 (m/s)^2, for readable coefficients
print(f"rows {len(A)}  units {A.unit.nunique()}  circuits {A.circuit.nunique()}")
CL = {"cov_type":"cluster","cov_kwds":{"groups": A.unit}}

print("\n=== VALIDATION ===")
for lbl, f, k, pred in [("V1 tow", "log_t ~ tow + C(unit)", "tow", "neg"),
                        ("V2 fuel(lap)", "log_t ~ lap + tow + C(unit)", "lap", "neg")]:
    m = smf.ols(f, data=A).fit(**CL); lo, hi = m.conf_int().loc[k]
    ok = "PASS" if hi < 0 else ("FAIL(+)" if lo > 0 else "NULL")
    print(f"  {lbl:<14} {m.params[k]*100:+7.3f}%  [{lo*100:+.3f}%,{hi*100:+.3f}%]  p={m.pvalues[k]:.3g}  {ok}")

print("\n=== PRIMARY (P12) ===")
F = "log_t ~ dv2k + tow + np.log1p(gap) + lap + C(unit)"
m = smf.ols(F, data=A).fit(**CL)
b, (lo, hi) = m.params["dv2k"], m.conf_int().loc["dv2k"]
print(f"  dv2_before: {b*100:+.3f}% per 1000 (m/s)^2   95% CI [{lo*100:+.3f}%, {hi*100:+.3f}%]  p={m.pvalues['dv2k']:.3g}")
print(f"  verdict: {'PASS (negative)' if hi<0 else ('WRONG-SIGN' if lo>0 else 'NULL')}")
iqr = A.dv2k.quantile(.75)-A.dv2k.quantile(.25)
print(f"  effect across the IQR of harvest ({iqr:.2f}k): {b*iqr*100:+.2f}%")

print("\n  leave-one-circuit-out:")
vals=[]
for c in sorted(A.circuit.unique()):
    d = A[A.circuit!=c]
    mm = smf.ols(F, data=d).fit(cov_type="cluster", cov_kwds={"groups": d.unit})
    l2,h2 = mm.conf_int().loc["dv2k"]; vals.append(mm.params["dv2k"])
    print(f"    drop {c:<12} {mm.params['dv2k']*100:+.3f}%  [{l2*100:+.3f},{h2*100:+.3f}]"
          f"{'  <-- CI includes 0' if l2<=0<=h2 else ''}")
print(f"    sign flips: {sum(1 for v in vals if v>0)}/{len(vals)}")
A.to_parquet("out/withinlap_analysis.parquet")
