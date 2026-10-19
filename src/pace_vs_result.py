"""Per-race pace rank vs actual finishing position.
The residual is everything pace does NOT explain: strategy, starts, incidents,
reliability, safety-car luck, overtaking ability."""
import json, numpy as np, pandas as pd, statsmodels.formula.api as smf, warnings
warnings.simplefilter("ignore")
D = pd.read_parquet("out/pace_fitted.parquet")
res = pd.DataFrame(json.loads(open("data/jolpica_results.json").read()))

# pace residual with NO driver term: what's left is driver+car speed
m = smf.ols("log_lap ~ C(circuit) + race_frac + C(compound) + tyre_age + np.log1p(gap_track)",
            data=D).fit()
D["pace_resid"] = m.resid

rows = []
for (circ, rnd), g in D.groupby(["circuit","round"]):
    p = g.groupby(["driver_number","family","team"]).pace_resid.median().reset_index()
    p = p[g.groupby(["driver_number","family","team"]).size().reset_index(name="n").n.values >= 25]
    if len(p) < 10: continue
    p["pace_rank"] = p.pace_resid.rank().astype(int)
    p["round"] = rnd; p["circuit"] = circ
    rows.append(p)
PR = pd.concat(rows)
M = PR.merge(res[["round","number","position","grid","points","status","family"]],
             left_on=["round","driver_number"], right_on=["round","number"], how="inner",
             suffixes=("","_r"))
M["finished"] = ~M.status.str.contains("Retired|Did not start", na=False)
M["delta"] = M.pace_rank - M.position      # positive = finished BETTER than pace
print(f"driver-races matched: {len(M)}  races {M['round'].nunique()}")

print("\n" + "="*78)
print("WHO BEAT THEIR OWN PACE  (avg positions gained vs pace rank, finishers only)")
print("="*78)
F = M[M.finished]
agg = (F.groupby("family")
        .agg(races=("delta","size"), avg_pace_rank=("pace_rank","mean"),
             avg_finish=("position","mean"), gained=("delta","mean"),
             pts=("points","sum"))
        .query("races >= 8").sort_values("gained", ascending=False))
print(f"  {'driver'.ljust(13)} {'races'.rjust(5)} {'pace rk'.rjust(8)} {'finish'.rjust(7)} {'gained'.rjust(7)} {'pts'.rjust(6)}")
for r in agg.itertuples():
    print(f"  {r.Index[:13].ljust(13)} {str(r.races).rjust(5)} {r.avg_pace_rank:>8.1f} "
          f"{r.avg_finish:>7.1f} {r.gained:>+7.2f} {r.pts:>6.0f}")
agg.to_csv("out/pace_vs_result.csv")

print("\n" + "="*78)
print("RELIABILITY / INCIDENT COST  (races lost to DNF, and pace when they did run)")
print("="*78)
dnf = (M.groupby("family")
        .agg(races=("position","size"), dnfs=("finished", lambda s: int((~s).sum())),
             pace_rank=("pace_rank","mean")).query("races >= 10")
        .sort_values("dnfs", ascending=False))
for r in dnf.head(8).itertuples():
    print(f"  {r.Index[:13].ljust(13)} DNF {r.dnfs}/{r.races}   avg pace rank {r.pace_rank:.1f}")

print("\n" + "="*78)
print("BIGGEST SINGLE-RACE OVERPERFORMANCES (pace rank -> finish)")
print("="*78)
for r in F.nlargest(8, "delta").itertuples():
    print(f"  {r.family[:12].ljust(12)} {r.circuit[:13].ljust(13)} pace {r.pace_rank:>2} -> P{r.position:<2}"
          f"  (+{r.delta})  grid P{r.grid}")
print("\nBIGGEST UNDERPERFORMANCES")
for r in F.nsmallest(8, "delta").itertuples():
    print(f"  {r.family[:12].ljust(12)} {r.circuit[:13].ljust(13)} pace {r.pace_rank:>2} -> P{r.position:<2}"
          f"  ({r.delta})  grid P{r.grid}")
M.to_parquet("out/pace_vs_result.parquet")
