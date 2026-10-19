"""Is 'good on tyres' a real, measurable driver skill?

Degradation = how much lap time a driver loses per lap of tyre age.
Car confounds it, so the test is TEAMMATE vs TEAMMATE: same machinery, same races.
Fuel is collinear with tyre age within a stint (the trap from project #2), so the
model carries race_frac as the fuel term and identifies degradation off the fact that
the same tyre age occurs at different points in the race across stints.
"""
import numpy as np, pandas as pd, statsmodels.formula.api as smf, warnings
warnings.simplefilter("ignore")
D = pd.read_parquet("out/pace_fitted.parquet")
D = D[D.tyre_age.between(1, 40)]
BASE = "C(circuit) + race_frac + C(compound) + np.log1p(gap_track)"

rows = []
for t, g in D.groupby("team"):
    fams = g.family.value_counts(); fams = fams[fams >= 250]
    if len(fams) < 2: continue
    g = g[g.family.isin(fams.index)].copy()
    ref = fams.index[0]
    g["fam"] = pd.Categorical(g.family, categories=[ref] + [f for f in fams.index if f != ref])
    m = smf.ols(f"log_lap ~ tyre_age * C(fam) + {BASE}", data=g).fit(
        cov_type="cluster", cov_kwds={"groups": g.circuit + "_" + g.driver_number.astype(str)})
    base_slope = m.params["tyre_age"]
    for f in fams.index:
        if f == ref:
            rows.append({"team": t, "driver": f, "deg": base_slope*100, "lo": np.nan, "hi": np.nan,
                         "n": int(fams[f]), "is_ref": True})
        else:
            k = f"tyre_age:C(fam)[T.{f}]"
            if k not in m.params: continue
            lo, hi = m.conf_int().loc[k]
            rows.append({"team": t, "driver": f, "deg": (base_slope + m.params[k])*100,
                         "lo": lo*100, "hi": hi*100, "n": int(fams[f]), "is_ref": False,
                         "diff": m.params[k]*100, "p": m.pvalues[k]})
R = pd.DataFrame(rows)
print("="*80)
print("TYRE DEGRADATION BY DRIVER  (% lap time lost per lap of tyre age)")
print("  lower = looks after the tyres better.  Compared only within a team.")
print("="*80)
for t, g in R.groupby("team"):
    g = g.sort_values("deg")
    print(f"\n  {t}")
    for r in g.itertuples():
        d = r.deg - g.deg.min()
        ci = "" if np.isnan(r.lo) else f"   gap CI [{r.lo:+.4f},{r.hi:+.4f}]  p={r.p:.3g}"
        tag = "  <-- gentler" if d == 0 else ""
        print(f"    {r.driver[:13].ljust(13)} {r.deg:+.4f}%/lap  (Δ {d:+.4f}){ci}{tag}")

print("\n" + "="*80)
print("TEAMMATE DEGRADATION GAPS, ranked")
print("="*80)
out = []
for t, g in R.groupby("team"):
    if len(g) != 2: continue
    g = g.sort_values("deg")
    gentle, harsh = g.iloc[0], g.iloc[1]
    d = harsh.deg - gentle.deg
    row = g[~g.is_ref].iloc[0]
    clear = (not np.isnan(row.lo)) and (row.lo > 0 or row.hi < 0)
    out.append({"team": t, "gentler": gentle.driver, "harsher": harsh.driver,
                "gap": d, "clear": clear, "p": row.p})
O = pd.DataFrame(out).sort_values("gap", ascending=False)
for r in O.itertuples():
    mark = " *" if r.clear else ""
    print(f"  {r.gentler[:12].ljust(12)} gentler than {r.harsher[:12].ljust(12)} "
          f"by {r.gap:.4f}%/lap  p={r.p:.3g}{mark}   ({r.team[:16]})")
print("\n  * = 95% CI on the difference excludes zero")
print(f"\n  teams where the difference is clear: {O.clear.sum()} of {len(O)}")
R.to_csv("out/tyre_skill.csv", index=False)
