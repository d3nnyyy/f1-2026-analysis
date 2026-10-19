"""Positive controls for the new observable. If these fail, the measure is junk."""
import numpy as np, pandas as pd, statsmodels.formula.api as smf, warnings, gaps
warnings.simplefilter("ignore")
A = pd.read_parquet("out/accel_raw.parquet")
G = pd.concat([gaps.gaps_for(sk).assign(session_key=sk) for sk in A.session_key.unique()])
A = A.merge(G, on=["session_key","driver","lap"], how="left")
A["gap"] = A.gap_track
A["unit"] = A.event + "_" + A.driver.astype(str)
A = A.dropna(subset=["gap","t_accel"])
A = A[(A.gap > 0) & (A.gap < 60) & (A.t_accel > 0.3) & (A.t_accel < 15)]
A["log_t"] = np.log(A.t_accel)
A["tow"] = (A.gap < 1.0).astype(int)
print(f"rows {len(A)}  units {A.unit.nunique()}  circuits {A.circuit.nunique()}")

CL = {"cov_type":"cluster","cov_kwds":{"groups": A.unit}}
print("\n=== CONTROL 1: slipstream should make acceleration FASTER (negative) ===")
m = smf.ols("log_t ~ tow + v_seg_start + C(unit)", data=A).fit(**CL)
b, (lo, hi) = m.params["tow"], m.conf_int().loc["tow"]
print(f"  tow: {b*100:+.2f}%  95% CI [{lo*100:+.2f}%, {hi*100:+.2f}%]  p={m.pvalues['tow']:.3g}")
print(f"  -> {'PASS (negative)' if hi < 0 else 'FAIL'}")

print("\n=== CONTROL 2: fuel burn should make acceleration FASTER over a race (negative) ===")
m2 = smf.ols("log_t ~ lap + tow + v_seg_start + C(unit)", data=A).fit(**CL)
b2, (l2, h2) = m2.params["lap"], m2.conf_int().loc["lap"]
print(f"  per lap: {b2*100:+.3f}%  95% CI [{l2*100:+.3f}%, {h2*100:+.3f}%]  p={m2.pvalues['lap']:.3g}")
print(f"  over 50 laps: {b2*50*100:+.2f}%")
print(f"  -> {'PASS (negative)' if h2 < 0 else 'FAIL' if l2 > 0 else 'NULL'}")

print("\n=== sensitivity comparison vs the old top-speed measure ===")
m3 = smf.ols("log_t ~ tow + v_seg_start + C(unit)", data=A).fit(**CL)
hw = (m3.conf_int().loc['tow'][1]-m3.conf_int().loc['tow'][0])/2
print(f"  CI half-width on a binary effect: {hw*100:.2f}% of acceleration time")
print(f"  median t_accel {A.t_accel.median():.2f}s -> +/-{hw*A.t_accel.median()*1000:.0f} ms")
A.to_parquet("out/accel.parquet")
