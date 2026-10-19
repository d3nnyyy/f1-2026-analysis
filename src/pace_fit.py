"""True pace, stripped of fuel load, tyre, traffic and circuit."""
import numpy as np, pandas as pd, statsmodels.formula.api as smf, warnings
warnings.simplefilter("ignore")
D = pd.read_parquet("out/pace_laps.parquet").dropna(subset=["team","gap_track"])
D = D[D.gap_track > 0]
D["cd"] = D.circuit + "_" + D.driver_number.astype(str)
CL = {"cov_type":"cluster","cov_kwds":{"groups": D.cd}}

BASE = "C(circuit) + race_frac + C(compound) + tyre_age + np.log1p(gap_track)"
print(f"laps {len(D)}  drivers {D.family.nunique()}  teams {D.team.nunique()}")

# --- how big are the nuisance effects we're removing? ---
mm = smf.ols(f"log_lap ~ {BASE}", data=D).fit(**CL)
print("\nnuisance effects (% of lap time):")
print(f"  fuel, start->end of race : {mm.params['race_frac']*100:+.2f}%")
print(f"  per lap of tyre age      : {mm.params['tyre_age']*100:+.3f}%")
print(f"  per e-fold of gap ahead  : {mm.params['np.log1p(gap_track)']*100:+.3f}%  (traffic)")
for c in ["SOFT","HARD"]:
    k = f"C(compound)[T.{c}]"
    if k in mm.params: print(f"  {c} vs MEDIUM            : {mm.params[k]*100:+.3f}%")

# --- TEAM (car) pace ---
mt = smf.ols(f"log_lap ~ C(team) + {BASE}", data=D).fit(**CL)
ref = sorted(D.team.unique())[0]
rows = []
for t in sorted(D.team.unique()):
    k = f"C(team)[T.{t}]"
    b = 0.0 if t == ref else mt.params.get(k, np.nan)
    rows.append({"team": t, "pace": b})
T = pd.DataFrame(rows)
T["pace_pct"] = (T.pace - T.pace.min())*100
T = T.sort_values("pace_pct")
print("\n" + "="*54); print("CAR PACE (% slower than the fastest car)"); print("="*54)
for i, r in enumerate(T.itertuples(), 1):
    print(f"  {str(i).rjust(2)}  {r.team[:20].ljust(20)} {r.pace_pct:+.3f}%")
T.to_csv("out/team_pace.csv", index=False)

# --- DRIVER pace ---
md = smf.ols(f"log_lap ~ C(family) + {BASE}", data=D).fit(**CL)
refd = sorted(D.family.unique())[0]
rows = []
for f in sorted(D.family.unique()):
    k = f"C(family)[T.{f}]"
    b = 0.0 if f == refd else md.params.get(k, np.nan)
    rows.append({"family": f, "pace": b, "team": D[D.family==f].team.mode().iloc[0],
                 "n": int((D.family==f).sum())})
P = pd.DataFrame(rows).dropna()
P["pace_pct"] = (P.pace - P.pace.min())*100
P = P.sort_values("pace_pct")
print("\n" + "="*54); print("DRIVER PACE, raw (% slower than fastest) — CAR-CONFOUNDED"); print("="*54)
for i, r in enumerate(P.itertuples(), 1):
    print(f"  {str(i).rjust(2)}  {r.family[:14].ljust(14)} {r.team[:18].ljust(18)} {r.pace_pct:+.3f}%  (n={r.n})")
P.to_csv("out/driver_pace.csv", index=False)
D.to_parquet("out/pace_fitted.parquet")
