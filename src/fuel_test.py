"""Primary test per PREREG_monza_fuel.md — run exactly once, report whatever comes out."""
import json, numpy as np, pandas as pd, statsmodels.formula.api as smf, warnings
warnings.simplefilter("ignore")

T = pd.read_parquet("out/monza_trap.parquet").dropna(subset=["gap"])
CA = T[T.gap > 2.0].copy()
print(f"clean-air laps: {len(CA)}  drivers: {CA.driver.nunique()}  laps {CA.lap.min()}-{CA.lap.max()}")

m = smf.ols("vmax ~ lap + C(driver)", data=CA).fit()
b = m.params["lap"]; lo, hi = m.conf_int().loc["lap"]; p = m.pvalues["lap"]
print(f"\n=== PRIMARY: vmax ~ lap_number + C(driver), clean air ===")
print(f"  slope      {b:+.4f} km/h per lap   95% CI [{lo:+.4f}, {hi:+.4f}]   p={p:.3g}")
print(f"  over 53 laps: {b*53:+.2f} km/h   (predicted +1.6 to +5.3)")

if lo <= 0 <= hi:                       verdict = "FAIL-FLAT"
elif b < 0:                             verdict = "FAIL-WEIRD"
elif 0.02 <= b <= 0.15:                 verdict = "PASS"
else:                                   verdict = f"PASS-direction, magnitude outside [0.02,0.15]"
print(f"\n  VERDICT: {verdict}")
