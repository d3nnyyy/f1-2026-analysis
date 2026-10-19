import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, pandas as pd, numpy as np
BG, FG, MUT, ACC, RED, GRN = "#1A1817","#E4E0DB","#7A736C","#F0D800","#C84B3C","#7FB069"

C = pd.read_csv("out/pace_championship.csv").rename(columns={"family":"driver"})
C = C[C.pace_pos <= 10].sort_values("pace_pos")

fig = plt.figure(figsize=(10, 7.4), facecolor=BG)
ax = fig.add_axes([0.30, 0.07, 0.40, 0.78])     # explicit box: leaves room up top
ax.set_facecolor(BG)

for r in C.itertuples():
    moved = r.real_pos - r.pace_pos
    col = RED if moved > 0 else (GRN if moved < 0 else MUT)
    big = abs(moved) >= 2
    ax.plot([0, 1], [r.pace_pos, r.real_pos], color=col,
            lw=2.8 if big else 1.4, alpha=1 if big else .45, zorder=2, solid_capstyle="round")
    ax.scatter([0, 1], [r.pace_pos, r.real_pos], s=40, color=col, zorder=3,
               edgecolor=BG, lw=1.4)
    ax.text(-0.115, r.pace_pos, f"{r.driver}", ha="right", va="center",
            color=FG if big else MUT, fontsize=11.5, fontweight="bold" if big else "normal")
    ax.text(-0.028, r.pace_pos, f"{r.pace_pos}", ha="right", va="center",
            color=MUT, fontsize=10)
    ax.text(1.028, r.real_pos, f"{r.real_pos}", ha="left", va="center", color=MUT, fontsize=10)
    tag = f"{r.driver}"
    if moved: tag += f"   {'▼' if moved>0 else '▲'}{abs(moved)}"
    ax.text(1.115, r.real_pos, tag, ha="left", va="center",
            color=FG if big else MUT, fontsize=11.5, fontweight="bold" if big else "normal")

ax.invert_yaxis()
ax.set_xlim(-0.04, 1.04); ax.set_ylim(10.6, 0.4)
ax.set_xticks([]); ax.set_yticks([])
for s in ax.spines.values(): s.set_visible(False)

# column headers, placed relative to the axes box so they cannot collide with the title
ax.text(0, -0.045, "BY PACE", transform=ax.transAxes, ha="center", va="bottom",
        color=ACC, fontsize=11.5, fontweight="bold")
ax.text(1, -0.045, "ACTUAL POINTS", transform=ax.transAxes, ha="center", va="bottom",
        color=ACC, fontsize=11.5, fontweight="bold")

fig.text(0.055, 0.962, "2026 championship: pace vs reality", color=FG,
         fontsize=19, fontweight="bold", va="top")
fig.text(0.055, 0.908, "Points awarded by race pace instead of finishing position, 17 rounds.",
         color=FG, fontsize=11.5, va="top", alpha=.85)
fig.text(0.055, 0.876, "Green gained places on merit, red lost them. Main races only.",
         color=MUT, fontsize=11.5, va="top")
plt.savefig("out/championship_slope.png", dpi=190, facecolor=BG)
print("saved")
