import numpy as np, pandas as pd, statsmodels.formula.api as smf, warnings
warnings.simplefilter("ignore")
d = pd.read_parquet("out/laps_clean.parquet")
d["compound"] = pd.Categorical(d.compound, categories=["MEDIUM","SOFT","HARD"])
F = "lap_duration ~ tyre_age * compound + lap_number + C(fe)"
CON = "tyre_age:compound[T.HARD] - tyre_age:compound[T.SOFT] = 0"

def fit(df):
    g = df.circuit.astype(str)+"_"+df.driver_number.astype(str)+"_"+df.stint_number.astype(str)
    m = smf.ols(F, data=df).fit(cov_type="cluster", cov_kwds={"groups": g})
    t = m.t_test(CON); lo,hi = t.conf_int()[0]
    return float(np.ravel(t.effect)[0]), lo, hi, float(np.ravel(t.pvalue)[0]), df.circuit.nunique(), len(df)

print("=== HARD - SOFT (s/lap), robustness ===")
e,lo,hi,p,nc,n = fit(d)
print(f"  {'full sample'.ljust(34)} {e:+.4f}  [{lo:+.4f},{hi:+.4f}] p={p:.3f}  ({nc} circuits, {n} laps)")

# require real tyre-age variation per circuit x compound
ok = d.groupby(["circuit","compound"], observed=True).tyre_age.agg(["size","max"])
good = ok[(ok["size"]>=60) & (ok["max"]>=12)].reset_index()
keep = d.merge(good[["circuit","compound"]], on=["circuit","compound"])
cc = keep.groupby("circuit").compound.nunique()
keep = keep[keep.circuit.isin(cc[cc==3].index)]
e,lo,hi,p,nc,n = fit(keep)
print(f"  {'>=60 laps & age>=12 per cmpd'.ljust(34)} {e:+.4f}  [{lo:+.4f},{hi:+.4f}] p={p:.3f}  ({nc} circuits, {n} laps)")

for drop in ["Monte Carlo","Silverstone","Catalunya"]:
    e,lo,hi,p,nc,n = fit(d[d.circuit!=drop])
    print(f"  {('drop '+drop).ljust(34)} {e:+.4f}  [{lo:+.4f},{hi:+.4f}] p={p:.3f}")

print("\n=== leave-one-circuit-out (full sample) ===")
es = []
for c in sorted(d.circuit.unique()):
    e,lo,hi,p,_,_ = fit(d[d.circuit!=c]); es.append(e)
print(f"  range {min(es):+.4f} .. {max(es):+.4f}   sign flips: {sum(1 for x in es if x<0)}/{len(es)}")

print("\n=== how big is the track effect vs the compound effect? ===")
pc = pd.read_csv("out/per_circuit_degradation.csv")
rel = pc[(pc.circuit!="Silverstone")]
print(f"  sd of degradation ACROSS circuits : {rel[['SOFT','MEDIUM','HARD']].stack().std():.4f} s/lap")
print(f"  HARD-SOFT compound difference     : {abs(e):.4f} s/lap")
print(f"  ratio                             : {rel[['SOFT','MEDIUM','HARD']].stack().std()/abs(e):.1f}x")
