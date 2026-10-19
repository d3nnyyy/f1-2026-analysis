import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, pandas as pd, numpy as np
BG, FG, MUT, ACC, RED = "#1A1817","#D6D2CE","#6E6862","#F0D800","#C84B3C"
R = pd.read_csv("out/teammate_gaps.csv")
rows = []
for t, g in R.groupby("team"):
    if len(g) < 2: continue
    g = g.sort_values("delta")
    f, s = g.iloc[0], g.iloc[1]
    rows.append({"team": t, "fast": f.driver, "slow": s.driver,
                 "gap": s.delta - f.delta,
                 "lo": abs(s.lo) if s.lo*s.hi > 0 else 0,
                 "hi": abs(s.hi) if s.lo*s.hi > 0 else abs(max(abs(s.lo), abs(s.hi))),
                 "clear": (s.lo > 0 or s.hi < 0)})
T = pd.DataFrame(rows).sort_values("gap")
fig, ax = plt.subplots(figsize=(11, 6.4), facecolor=BG); ax.set_facecolor(BG)
y = np.arange(len(T))
cols = [ACC if c else MUT for c in T.clear]
ax.barh(y, T.gap, color=cols, height=.62)
for i, r in enumerate(T.itertuples()):
    ax.text(r.gap + .025, i, f"{r.gap:.3f}%", va="center", color=FG, fontsize=10, fontweight="bold")
    ax.text(-.03, i, f"{r.fast}  ▸  {r.slow}", va="center", ha="right", color=FG, fontsize=10)
    ax.text(r.gap/2, i, r.team[:16], va="center", ha="center", color=BG, fontsize=8.2,
            fontweight="bold", alpha=.85 if r.clear else .6)
ax.set_yticks([]); ax.set_xlim(-0.62, 1.32)
ax.axvline(0, color=FG, lw=1)
ax.set_xlabel("pace gap to teammate  (% per lap, fuel / tyre / traffic / circuit removed)",
              color=FG, fontsize=10.5)
ax.set_title("2026 teammate head-to-head — same car, so this is the driver",
             color=FG, fontsize=14, loc="left", pad=28)
ax.text(0, 1.04, "15,125 race laps, 17 rounds · gold = 95% CI excludes zero · grey = not separable",
        transform=ax.transAxes, color=MUT, fontsize=9.3, va="bottom")
ax.tick_params(colors=MUT, labelsize=9); ax.grid(axis="x", color=MUT, alpha=.15, lw=.6)
for s in ax.spines.values(): s.set_visible(False)
ax.spines["bottom"].set_visible(True); ax.spines["bottom"].set_color(MUT)
plt.tight_layout(); plt.savefig("out/teammates.png", dpi=190, facecolor=BG)
print(T[["team","fast","slow","gap","clear"]].round(3).to_string(index=False))
