"""Who actually gains places off the line?
Position after lap 1 = order of crossing the line to start lap 2.
Corrected for the mechanical floor/ceiling: pole can only lose, P20 can only gain."""
import json, numpy as np, pandas as pd, statsmodels.formula.api as smf, warnings
warnings.simplefilter("ignore")
idx = [r for r in json.load(open("out/race_index.json")) if r["n_laps"] > 0]
res = pd.DataFrame(json.loads(open("data/jolpica_results.json").read()))
order = sorted(idx, key=lambda r: r["date"])
rnd = {r["circuit"]: i+1 for i, r in enumerate(order)}

rows = []
for r in idx:
    L = pd.DataFrame(json.load(open(f"data/laps_session_key={r['session_key']}.json")))
    L["t0"] = pd.to_datetime(L.date_start, format="ISO8601", errors="coerce")
    l2 = L[(L.lap_number == 2) & L.t0.notna()].sort_values("t0")
    if len(l2) < 10: continue
    l2 = l2.assign(pos_l1=range(1, len(l2)+1))
    for x in l2.itertuples():
        rows.append({"round": rnd[r["circuit"]], "circuit": r["circuit"],
                     "number": x.driver_number, "pos_l1": x.pos_l1})
S = pd.DataFrame(rows).merge(res[["round","number","grid","family","team","position","status"]],
                             on=["round","number"], how="inner")
S = S[S.grid > 0]
S["gained"] = S.grid - S.pos_l1
print(f"driver-races with a lap-1 position: {len(S)}  races {S['round'].nunique()}")

mech = smf.ols("gained ~ grid", data=S).fit()
print(f"\nmechanical component: gained = {mech.params['Intercept']:+.2f} {mech.params['grid']:+.3f} x grid"
      f"  (R2={mech.rsquared:.3f}, p={mech.pvalues['grid']:.2g})")
S["skill"] = S.gained - mech.predict(S)

agg = (S.groupby("family").agg(races=("skill","size"), avg_grid=("grid","mean"),
        raw=("gained","mean"), corrected=("skill","mean"), sd=("skill","std"))
       .query("races >= 8"))
agg["se"] = agg.sd/np.sqrt(agg.races)
agg["lo"] = agg.corrected-1.96*agg.se; agg["hi"] = agg.corrected+1.96*agg.se
agg = agg.sort_values("corrected", ascending=False)
print("\n" + "="*72)
print("PLACES GAINED ON LAP 1, corrected for grid position")
print("="*72)
print(f"  {'driver'.ljust(13)} {'races'.rjust(5)} {'grid'.rjust(5)} {'raw'.rjust(6)} {'corrected'.rjust(10)} {'95% CI'.rjust(16)}")
for r in agg.itertuples():
    star = " *" if (r.lo > 0 or r.hi < 0) else ""
    print(f"  {r.Index[:13].ljust(13)} {str(r.races).rjust(5)} {r.avg_grid:>5.1f} {r.raw:>+6.2f} "
          f"{r.corrected:>+10.2f}   [{r.lo:+5.2f},{r.hi:+5.2f}]{star}")
print(f"\n  * = 95% CI excludes zero  ->  {int(((agg.lo>0)|(agg.hi<0)).sum())} of {len(agg)} drivers")
# is start performance even repeatable? split-half across rounds
S["half"] = (S["round"] > S["round"].median()).map({True:"late", False:"early"})
h = S.pivot_table(index="family", columns="half", values="skill", aggfunc="mean").dropna()
rr = np.corrcoef(h.early, h.late)[0,1]
print(f"\n  split-half repeatability (first half of season vs second): r = {rr:+.3f}  n={len(h)}")
print("  -> a real skill should repeat; noise should not.")
agg.to_csv("out/starts.csv")
