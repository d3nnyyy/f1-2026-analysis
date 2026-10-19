import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, pandas as pd, numpy as np, json
from scipy import stats
BG, FG, MUT, ACC, GRN, RED = "#1A1817","#D6D2CE","#6E6862","#F0D800","#7FB069","#C84B3C"
P = pd.read_csv("/Users/denys/f1-2026/results/team_pace.csv").sort_values("pace_pct")
P["pace_rank"] = range(1, len(P)+1)
cs = json.load(open("data/jolpica_constructorstandings.json"))
cl = cs["MRData"]["StandingsTable"]["StandingsLists"][-1]["ConstructorStandings"]
C = pd.DataFrame([{"team": c["Constructor"]["name"], "champ_rank": int(c["position"]),
                   "pts": float(c["points"])} for c in cl])
M = P.merge(C, on="team")
rho, p = stats.spearmanr(M.pace_rank, M.champ_rank)
exact = int((M.pace_rank == M.champ_rank).sum())
print(f"Spearman rho = {rho:.3f}  p = {p:.2g}   exact matches: {exact}/{len(M)}")
print(M[["team","pace_rank","champ_rank","pts"]].to_string(index=False))

fig, ax = plt.subplots(figsize=(8.8, 8.4), facecolor=BG); ax.set_facecolor(BG)
for r in M.itertuples():
    same = r.pace_rank == r.champ_rank
    col = GRN if same else ACC
    ax.plot([0,1], [r.pace_rank, r.champ_rank], color=col, lw=2.6 if same else 1.8, alpha=.9)
    ax.scatter([0,1], [r.pace_rank, r.champ_rank], s=52, color=col, zorder=3, edgecolor=BG, lw=1.2)
    ax.text(-0.035, r.pace_rank, f"{r.pace_rank}. {r.team}", ha="right", va="center", color=FG, fontsize=10.5)
    ax.text(1.035, r.champ_rank, f"{r.team} .{r.champ_rank}", ha="left", va="center", color=FG, fontsize=10.5)
ax.invert_yaxis(); ax.set_xlim(-0.62,1.62); ax.set_xticks([]); ax.set_yticks([])
ax.text(0, 0.1, "RANKED BY LAP TIMES", ha="center", color=ACC, fontsize=12, fontweight="bold")
ax.text(1, 0.1, "ACTUAL CHAMPIONSHIP", ha="center", color=ACC, fontsize=12, fontweight="bold")
ax.set_title("The model never sees a result — and gets the championship order anyway",
             color=FG, fontsize=14, loc="left", pad=42)
ax.text(0, 1.055, f"15,125 race laps, fuel / tyre / traffic / circuit removed · Spearman ρ = {rho:.2f} · "
                  f"{exact} of {len(M)} exact\nthe only errors are two adjacent swaps",
        transform=ax.transAxes, color=MUT, fontsize=9.6, va="bottom")
for s in ax.spines.values(): s.set_visible(False)
plt.tight_layout(); plt.savefig("out/validation.png", dpi=190, facecolor=BG)
