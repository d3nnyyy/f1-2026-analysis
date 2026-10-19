"""Correct for regression-to-the-mean: a car qualifying 18th on pace can only gain,
a car with pace rank 1 can only lose. Measure that mechanical relationship first,
then judge each driver against what their OWN pace rank predicts."""
import numpy as np, pandas as pd, statsmodels.formula.api as smf, warnings
warnings.simplefilter("ignore")
M = pd.read_parquet("out/pace_vs_result.parquet")
F = M[M.finished].copy()

mech = smf.ols("delta ~ pace_rank", data=F).fit()
print("THE ARTIFACT, measured:")
print(f"  delta = {mech.params['Intercept']:+.2f} {mech.params['pace_rank']:+.3f} x pace_rank"
      f"   R2={mech.rsquared:.3f}  p={mech.pvalues['pace_rank']:.2g}")
print(f"  -> a driver 10 pace-places further back gains {mech.params['pace_rank']*10:+.2f} positions")
print(f"     PURELY mechanically. {mech.rsquared*100:.0f}% of all variation in 'gained' is this.")

F["expected"] = mech.predict(F)
F["skill"] = F.delta - F["expected"]        # beat your own pace rank's expectation

print("\n" + "="*72)
print("CORRECTED: positions gained BEYOND what the pace rank mechanically predicts")
print("="*72)
agg = (F.groupby("family").agg(races=("skill","size"), pace_rk=("pace_rank","mean"),
        raw_gain=("delta","mean"), corrected=("skill","mean"),
        sd=("skill","std")).query("races >= 8"))
agg["se"] = agg.sd/np.sqrt(agg.races)
agg["lo"] = agg.corrected - 1.96*agg.se; agg["hi"] = agg.corrected + 1.96*agg.se
agg = agg.sort_values("corrected", ascending=False)
print(f"  {'driver'.ljust(13)} {'races'.rjust(5)} {'pace'.rjust(5)} {'raw'.rjust(6)} {'corrected'.rjust(10)} {'95% CI'.rjust(18)}")
for r in agg.itertuples():
    star = " *" if (r.lo > 0 or r.hi < 0) else ""
    print(f"  {r.Index[:13].ljust(13)} {str(r.races).rjust(5)} {r.pace_rk:>5.1f} {r.raw_gain:>+6.2f} "
          f"{r.corrected:>+10.2f}   [{r.lo:+5.2f},{r.hi:+5.2f}]{star}")
print("\n  * = 95% CI excludes zero")
agg.to_csv("out/pace_corrected.csv")
