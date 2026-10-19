import numpy as np, pandas as pd, statsmodels.formula.api as smf, warnings, json
from scipy import stats
warnings.simplefilter("ignore")
D = pd.read_parquet("out/pace_fitted.parquet")

print("="*70)
print("CANDIDATE A — SURVIVORSHIP: do long stints look gentler than they are?")
print("="*70)
print("A team pits when the tyre is done. So a stint that RAN LONG is a stint where")
print("degradation happened to be low. Estimating degradation from observed stints")
print("conditions on the outcome.\n")
D["stint_len"] = D.groupby(["circuit","driver_number","stint_end"]).lap_number.transform("count")
D["lenbin"] = pd.cut(D.stint_len, [0,10,15,20,25,100],
                     labels=["<=10","11-15","16-20","21-25",">25"])
BASE = "C(circuit) + race_frac + C(compound) + np.log1p(gap_track)"
for b, g in D.groupby("lenbin", observed=True):
    if len(g) < 400: continue
    g = g.copy(); g["cl"] = g.circuit+"_"+g.driver_number.astype(str)
    m = smf.ols(f"log_lap ~ tyre_age + {BASE}", data=g).fit(
        cov_type="cluster", cov_kwds={"groups": g.cl})
    lo, hi = m.conf_int().loc["tyre_age"]
    print(f"  stints of {str(b).ljust(6)} laps  n={len(g):>5}  degradation {m.params['tyre_age']*100:+.4f}%/lap"
          f"  [{lo*100:+.4f},{hi*100:+.4f}]")

print("\n" + "="*70)
print("CANDIDATE B — COLLIDER: conditioning on finishing position")
print("="*70)
res = pd.DataFrame(json.loads(open("data/jolpica_results.json").read()))
M = pd.read_parquet("out/pace_vs_result.parquet")
M = M.dropna(subset=["grid","position","pace_resid"])
M = M[M.grid > 0]
print("Finishing position is CAUSED BY both grid position and race pace.")
print("Conditioning on it should induce a correlation between the two causes.\n")
r_all, p_all = stats.pearsonr(M.grid, M.pace_resid)
print(f"  everyone              n={len(M):>4}   r(grid, race pace) = {r_all:+.3f}  p={p_all:.2g}")
for lbl, sub in [("points finishers only (P1-10)", M[M.position <= 10]),
                 ("podium finishers only (P1-3)",  M[M.position <= 3]),
                 ("outside the points (P11+)",     M[M.position > 10])]:
    if len(sub) < 25: continue
    r, p = stats.pearsonr(sub.grid, sub.pace_resid)
    print(f"  {lbl.ljust(30)} n={len(sub):>4}   r = {r:+.3f}  p={p:.2g}")
print("\n  (grid is a POSITION so lower = better; pace_resid is a TIME so lower = better.")
print("   A positive r in the full field means 'good qualifiers are also fast'.)")
