import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, pandas as pd, numpy as np
BG, FG, MUT, ACC, RED, GRN = "#1A1817","#D6D2CE","#6E6862","#F0D800","#C84B3C","#7FB069"
C = pd.read_csv("out/pace_championship.csv").rename(columns={"family":"driver"})
C = C[C.pace_pos <= 12].sort_values("pace_pos")
fig, ax = plt.subplots(figsize=(8.6, 8.2), facecolor=BG); ax.set_facecolor(BG)
for r in C.itertuples():
    moved = r.real_pos - r.pace_pos
    col = RED if moved > 0 else (GRN if moved < 0 else MUT)
    ax.plot([0, 1], [r.pace_pos, r.real_pos], color=col, lw=2.4 if abs(moved) >= 2 else 1.3,
            alpha=.95 if abs(moved) >= 2 else .5, zorder=2)
    ax.scatter([0,1], [r.pace_pos, r.real_pos], s=46, color=col, zorder=3, edgecolor=BG, lw=1.2)
    ax.text(-0.035, r.pace_pos, f"{r.pace_pos}. {r.driver}", ha="right", va="center",
            color=FG, fontsize=10.2)
    tag = f"{r.driver} .{r.real_pos}"
    ax.text(1.035, r.real_pos, tag, ha="left", va="center", color=FG, fontsize=10.2)
ax.invert_yaxis(); ax.set_xlim(-0.52, 1.52); ax.set_xticks([])
ax.set_yticks([])
ax.text(0, C.pace_pos.min()-1.05, "BY PACE", ha="center", color=ACC, fontsize=12, fontweight="bold")
ax.text(1, C.pace_pos.min()-1.05, "ACTUAL POINTS", ha="center", color=ACC, fontsize=12, fontweight="bold")
ax.set_title("2026 championship: pace vs reality", color=FG, fontsize=15, loc="left", pad=34)
ax.text(0, 1.045, "green = finished higher than pace alone deserved  ·  red = lost ground  ·  main races only",
        transform=ax.transAxes, color=MUT, fontsize=9.4, va="bottom")
for s in ax.spines.values(): s.set_visible(False)
plt.tight_layout(); plt.savefig("out/championship_slope.png", dpi=190, facecolor=BG)
print("saved")
