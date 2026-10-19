import pandas as pd, numpy as np, statsmodels.formula.api as smf, warnings
warnings.simplefilter("ignore")
T = pd.read_parquet("out/monza_trap2.parquet").dropna(subset=["gap","v_entry"])
A = T[T.accel_time >= 5].copy()
A["post_vsc"]  = A.lap.isin([30, 31])
A["post_vsc2"] = A.lap.isin([32, 33, 34])

print("gap by lap window (the confound check):")
print(A.assign(w=np.select([A.lap.between(24,27), A.post_vsc, A.post_vsc2],
       ["pre (24-27)","restart (30-31)","after (32-34)"], "other"))
      .query("w != 'other'").groupby("w").agg(n=("gap","size"), median_gap=("gap","median"),
                                              vmax=("vmax","mean")).round(2).to_string())

for name, f in [("no gap control",
                 "vmax ~ post_vsc + post_vsc2 + lap + v_entry + accel_time + C(driver)"),
                ("WITH gap control",
                 "vmax ~ post_vsc + post_vsc2 + lap + np.log1p(gap) + v_entry + accel_time + C(driver)")]:
    m = smf.ols(f, data=A).fit()
    print(f"\n=== {name} (n={int(m.nobs)}) ===")
    for k in ["post_vsc[T.True]", "post_vsc2[T.True]"]:
        b = m.params[k]; lo, hi = m.conf_int().loc[k]
        lbl = "laps 30-31" if "2" not in k else "laps 32-34"
        print(f"  {lbl:<12} {b:+6.2f} km/h  95% CI [{lo:+6.2f},{hi:+6.2f}]  p={m.pvalues[k]:.3g}")
