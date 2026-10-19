import json, numpy as np, pandas as pd
M = pd.read_parquet("out/pace_vs_result.parquet")
res = pd.DataFrame(json.loads(open("data/jolpica_results.json").read()))
order = M[["round","circuit"]].drop_duplicates().sort_values("round")

print("="*88)
print("TOP 3 BY PACE   vs   ACTUAL PODIUM")
print("="*88)
print(f"  {'race'.ljust(15)} {'PACE 1-2-3'.ljust(36)} {'ACTUAL PODIUM'.ljust(34)}")
rows = []
for r in order.itertuples():
    g = M[M["round"] == r.round]
    pace = g.nsmallest(3, "pace_rank").sort_values("pace_rank")
    act  = res[(res["round"] == r.round) & (res.position <= 3)].sort_values("position")
    p = " ".join(f"{i+1}.{x[:3].upper()}" for i, x in enumerate(pace.family))
    a = " ".join(f"{i+1}.{x[:3].upper()}" for i, x in enumerate(act.family))
    match = len(set(pace.family) & set(act.family))
    exact = sum(1 for i in range(min(len(pace),len(act)))
                if pace.family.iloc[i] == act.family.iloc[i])
    print(f"  {r.circuit[:15].ljust(15)} {p.ljust(36)} {a.ljust(34)} {match}/3 same, {exact} in place")
    rows.append({"round": r.round, "circuit": r.circuit, "same": match, "exact": exact})
S = pd.DataFrame(rows)
print(f"\n  average overlap: {S.same.mean():.2f}/3 drivers;  {S.exact.mean():.2f}/3 in the exact position")
print(f"  races where the pace top-3 WAS the podium (any order): {(S.same==3).sum()}/{len(S)}")
print(f"  races where it matched exactly: {(S.exact==3).sum()}/{len(S)}")

PTS = [25,18,15,12,10,8,6,4,2,1]
def pts_for(rank): return PTS[rank-1] if 1 <= rank <= 10 else 0
M["pace_points"] = M.pace_rank.apply(pts_for)
champ = (M.groupby("family")
          .agg(pace_pts=("pace_points","sum"), real_pts=("points","sum"),
               races=("pace_rank","size"), avg_pace=("pace_rank","mean"))
          .sort_values("pace_pts", ascending=False))
champ["pace_pos"] = range(1, len(champ)+1)
champ = champ.sort_values("real_pts", ascending=False)
champ["real_pos"] = range(1, len(champ)+1)
champ["move"] = champ.real_pos - champ.pace_pos
champ = champ.sort_values("pace_pos")
print("\n" + "="*88)
print("CHAMPIONSHIP IF POINTS WERE AWARDED BY PACE ALONE  (main races only)")
print("="*88)
print(f"  {'#'.rjust(2)}  {'driver'.ljust(13)} {'pace pts'.rjust(8)} {'|'} {'real pts'.rjust(8)} "
      f"{'real #'.rjust(6)}  {'move'.rjust(5)}  {'avg pace rk'.rjust(11)}")
for r in champ.itertuples():
    mv = f"{r.move:+d}" if r.move else "  ="
    print(f"  {str(r.pace_pos).rjust(2)}  {r.Index[:13].ljust(13)} {r.pace_pts:>8.0f} | {r.real_pts:>8.0f} "
          f"{str(r.real_pos).rjust(6)}  {mv.rjust(5)}  {r.avg_pace:>11.1f}")
champ.to_csv("out/pace_championship.csv")
print(f"\n  NOTE: real pts here = main-race points only; the official standings also include")
print(f"  sprint points, so totals differ from the published table.")
