"""Primary pooled test, exactly as specified in PREREG_pooled_sc.md. Run once."""
import numpy as np, pandas as pd, statsmodels.formula.api as smf, warnings
warnings.simplefilter("ignore")
pd.set_option("display.width", 200)

D = pd.read_parquet("out/pooled_sc.parquet")
D = D[D.phase != "excluded"].copy()
print(f"rows in window phases : {len(D)}   events {D.event.nunique()}")

# ---- the single most important filter (pre-registered) ----
n_before = D.groupby(["event","driver"]).ngroups
D = D[~D.pitted_in_window]
print(f"driver-events after pit filter : {D.groupby(['event','driver']).ngroups} of {n_before}")
D = D.dropna(subset=["gap","v_entry","accel_time","vmax"])
D = D[(D.accel_time >= 4) & (D.gap > 0) & (D.gap < 60)]
D["unit"] = D.event + "_" + D.driver.astype(str)
D["restart"] = (D.phase == "restart").astype(int)
D["decay"]   = (D.phase == "decay").astype(int)
print(f"analysis rows : {len(D)}   units {D.unit.nunique()}   events {D.event.nunique()}")
print("\nphase counts:"); print(D.phase.value_counts().to_string())
if len(D) < 100: raise SystemExit("too few rows")

CL = {"cov_type":"cluster", "cov_kwds":{"groups": D.unit}}
F = "vmax ~ restart + decay + lap + np.log1p(gap) + v_entry + accel_time + C(unit)"
m = smf.ols(F, data=D).fit(**CL)

print("\n" + "="*62)
print("PRIMARY (pre-registered)")
print("="*62)
for k, lbl in [("restart","restart (end+1..+2)"), ("decay","decay (end+3..+5)")]:
    b = m.params[k]; lo, hi = m.conf_int().loc[k]
    print(f"  {lbl:<22} {b:+6.2f} km/h   95% CI [{lo:+6.2f},{hi:+6.2f}]   p={m.pvalues[k]:.3g}")
hw = (m.conf_int().loc['restart'][1]-m.conf_int().loc['restart'][0])/2
print(f"\n  achieved detection floor (CI half-width): +/-{hw:.2f} km/h")
print(f"  (Monza alone was +/-2.20)")

lo, hi = m.conf_int().loc["restart"]
verdict = "NULL" if lo <= 0 <= hi else ("PASS-direction" if m.params["restart"] > 0 else "NEGATIVE")
print(f"\n  P5 verdict: {verdict}")
print(f"  P6 (decay < restart): {'holds' if m.params['decay'] < m.params['restart'] else 'FAILS'}")

print("\n" + "="*62)
print("DOSE-RESPONSE (pre-registered, directional)")
print("="*62)
st = D.groupby("circuit").accel_time.median().rename("straight")
D2 = D.merge(st, on="circuit")
D2["straight_c"] = D2.straight - D2.straight.mean()
D2["sc_c"] = D2.sc_laps - D2.sc_laps.mean()
for nm, term, pred in [("P7 restart x straight length", "restart:straight_c", "POSITIVE"),
                       ("P8 restart x SC duration",     "restart:sc_c",       "POSITIVE")]:
    f2 = F.replace("restart +", f"restart + {term.replace(':','*')} +")
    try:
        mm = smf.ols(f2, data=D2).fit(cov_type="cluster", cov_kwds={"groups": D2.unit})
        key = [k for k in mm.params.index if ":" in k and "restart" in k and
               term.split(":")[1] in k]
        if not key: print(f"  {nm}: term not found"); continue
        k = key[0]; b = mm.params[k]; l2, h2 = mm.conf_int().loc[k]
        sig = "CI excludes 0" if not (l2 <= 0 <= h2) else "CI includes 0"
        print(f"  {nm:<30} {b:+.3f}  [{l2:+.3f},{h2:+.3f}]  pred {pred}  -> {sig}")
    except Exception as e:
        print(f"  {nm}: failed ({e})")
D.to_parquet("out/pooled_analysis.parquet")
