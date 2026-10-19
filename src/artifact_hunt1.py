"""Artifact hunt 1: why does SOFT come out SLOWER than MEDIUM?
Softs are the fastest compound. The pace model says otherwise. Something is wrong."""
import numpy as np, pandas as pd, statsmodels.formula.api as smf, warnings
warnings.simplefilter("ignore")
D = pd.read_parquet("out/pace_fitted.parquet")
D["cl"] = D.circuit + "_" + D.driver_number.astype(str)
CL = {"cov_type":"cluster","cov_kwds":{"groups": D.cl}}
D["compound"] = pd.Categorical(D.compound, categories=["MEDIUM","SOFT","HARD"])

print("=== how are the compounds actually USED? ===")
print(D.groupby("compound", observed=True).agg(
    laps=("lap_duration","size"),
    mean_tyre_age=("tyre_age","mean"),
    mean_race_frac=("race_frac","mean"),
    median_gap=("gap_track","median")).round(2).to_string())

print("\n=== the apparent result ===")
m = smf.ols("log_lap ~ C(compound) + C(circuit) + race_frac + tyre_age + np.log1p(gap_track)",
            data=D).fit(**CL)
for c in ["SOFT","HARD"]:
    k = f"C(compound)[T.{c}]"
    lo, hi = m.conf_int().loc[k]
    print(f"  {c} vs MEDIUM: {m.params[k]*100:+.3f}%  [{lo*100:+.3f},{hi*100:+.3f}]  p={m.pvalues[k]:.3g}")

print("\n=== same driver, same race, both compounds (within-driver-race contrast) ===")
both = D.groupby(["circuit","driver_number"]).compound.nunique()
keep = both[both >= 2].index
W = D.set_index(["circuit","driver_number"]).loc[keep].reset_index()
W["cl"] = W.circuit + "_" + W.driver_number.astype(str)
W["compound"] = pd.Categorical(W.compound, categories=["MEDIUM","SOFT","HARD"])
m2 = smf.ols("log_lap ~ C(compound) + C(cl) + race_frac + tyre_age + np.log1p(gap_track)",
             data=W).fit(cov_type="cluster", cov_kwds={"groups": W.cl})
print(f"  n={len(W)}  driver-races={W.cl.nunique()}")
for c in ["SOFT","HARD"]:
    k = f"C(compound)[T.{c}]"
    if k not in m2.params: continue
    lo, hi = m2.conf_int().loc[k]
    print(f"  {c} vs MEDIUM: {m2.params[k]*100:+.3f}%  [{lo*100:+.3f},{hi*100:+.3f}]  p={m2.pvalues[k]:.3g}")

print("\n=== FRESH tyres only (age <= 3 laps), where compound grip should show cleanest ===")
F = W[W.tyre_age <= 3].copy()
F["compound"] = pd.Categorical(F.compound, categories=["MEDIUM","SOFT","HARD"])
m3 = smf.ols("log_lap ~ C(compound) + C(cl) + race_frac + np.log1p(gap_track)",
             data=F).fit(cov_type="cluster", cov_kwds={"groups": F.cl})
print(f"  n={len(F)}")
for c in ["SOFT","HARD"]:
    k = f"C(compound)[T.{c}]"
    if k not in m3.params: continue
    lo, hi = m3.conf_int().loc[k]
    print(f"  {c} vs MEDIUM: {m3.params[k]*100:+.3f}%  [{lo*100:+.3f},{hi*100:+.3f}]  p={m3.pvalues[k]:.3g}")
