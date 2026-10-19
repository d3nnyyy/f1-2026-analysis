"""Does a lap-level ENERGY BUDGET bind?

If deployment is planned and energy-limited over a lap, then being quicker than expected
on one straight must be paid for on another straight of the SAME lap:
  -> within-lap residuals NEGATIVELY correlated.
If instead the variation is 'good laps are good everywhere' (driver form, clean air,
track state), residuals are POSITIVELY correlated.
Opposite signs, so the test is diagnostic rather than confirmatory.
"""
import numpy as np, pandas as pd, statsmodels.formula.api as smf, warnings
from scipy import stats
warnings.simplefilter("ignore")
A = pd.read_parquet("out/withinlap_analysis.parquet")

# residual after removing everything structural: the straight itself, fuel, tow, traffic
m = smf.ols("log_t ~ tow + np.log1p(gap) + lap + v0 + C(unit)", data=A).fit()
A["resid"] = m.resid
A["lapkey"] = A.event + "_" + A.driver.astype(str) + "_L" + A.lap.astype(str)

# all within-lap straight pairs
pairs = []
for lk, g in A.groupby("lapkey"):
    if len(g) < 2: continue
    g = g.sort_values("straight")
    r = g.resid.values; s = g.straight.values
    for i in range(len(g)):
        for j in range(i+1, len(g)):
            pairs.append({"lapkey": lk, "circuit": g.circuit.iloc[0],
                          "si": s[i], "sj": s[j], "ri": r[i], "rj": r[j]})
P = pd.DataFrame(pairs)
print(f"within-lap straight pairs: {len(P)}  laps: {P.lapkey.nunique()}  circuits: {P.circuit.nunique()}")

r, p = stats.pearsonr(P.ri, P.rj)
n = P.lapkey.nunique()                       # cluster on laps, not pairs
z = np.arctanh(r); se = 1/np.sqrt(max(n-3,1))
lo, hi = np.tanh(z-1.96*se), np.tanh(z+1.96*se)
print(f"\n=== within-lap residual correlation ===")
print(f"  r = {r:+.4f}   95% CI [{lo:+.4f}, {hi:+.4f}]  (CI from n={n} laps, not n={len(P)} pairs)")
print(f"  energy-budget hypothesis predicts NEGATIVE")
print(f"  'good laps are good everywhere'  predicts POSITIVE")
verdict = ("supports ENERGY BUDGET" if hi < 0 else
           "supports LAP-QUALITY (no binding budget)" if lo > 0 else "NULL / indeterminate")
print(f"  -> {verdict}")

print("\n  per circuit:")
for c, g in P.groupby("circuit"):
    if g.lapkey.nunique() < 25: continue
    rc, _ = stats.pearsonr(g.ri, g.rj)
    print(f"    {c:<13} r={rc:+.3f}  (laps={g.lapkey.nunique()})")

# adjacent vs distant straights: a budget should bind hardest between NEIGHBOURING straights
P["sep"] = P.sj - P.si
print("\n  by separation between the two straights:")
for s, g in P.groupby("sep"):
    if len(g) < 60: continue
    rc, _ = stats.pearsonr(g.ri, g.rj)
    print(f"    {int(s)} apart: r={rc:+.3f}  (pairs={len(g)})")
