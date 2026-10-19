import pandas as pd, numpy as np, statsmodels.formula.api as smf, warnings
warnings.simplefilter("ignore")
T = pd.read_parquet("out/monza_trap2.parquet").dropna(subset=["gap","v_entry"])
A = T[(T.gap > 2.0) & (T.accel_time >= 5)].copy()
print(f"clean-air laps with a full straight run: {len(A)}  drivers: {A.driver.nunique()}\n")

def row(name, f):
    m = smf.ols(f, data=A).fit()
    b = m.params["lap"]; lo, hi = m.conf_int().loc["lap"]
    print(f"  {name:<46} {b:+.4f}  [{lo:+.4f},{hi:+.4f}]  = {b*53:+.2f} km/h / race")
    return m

print("effect of lap_number on clean-air top speed:")
row("primary: + driver FE", "vmax ~ lap + C(driver)")
row("+ corner-entry speed", "vmax ~ lap + v_entry + C(driver)")
m = row("+ entry speed + time spent accelerating", "vmax ~ lap + v_entry + accel_time + C(driver)")
print(f"\n  v_entry coef    {m.params['v_entry']:+.3f} km/h per km/h of corner exit")
print(f"  accel_time coef {m.params['accel_time']:+.3f} km/h per extra second at full throttle")

print("\nis lap_number just standing in for tyre age?")
row("+ tyre age", "vmax ~ lap + v_entry + accel_time + tyre_age + C(driver)")
m2 = smf.ols("vmax ~ lap + v_entry + accel_time + tyre_age + C(driver)", data=A).fit()
b2 = m2.params["tyre_age"]; l2, h2 = m2.conf_int().loc["tyre_age"]
print(f"  tyre_age coef   {b2:+.4f}  [{l2:+.4f},{h2:+.4f}]  p={m2.pvalues['tyre_age']:.3g}")
