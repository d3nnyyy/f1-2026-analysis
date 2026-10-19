import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, pandas as pd, numpy as np

BG, FG, MUT = "#1A1817", "#D6D2CE", "#6E6862"
C = {"SOFT": "#C84B3C", "MEDIUM": "#F0D800", "HARD": "#D6D2CE"}

pc = pd.read_csv("out/per_circuit_degradation.csv")
pc = pc[pc.circuit != "Silverstone"]                      # soft slope unidentified (31 laps)
pc = pc.assign(mean=pc[["SOFT","MEDIUM","HARD"]].mean(axis=1)).sort_values("mean")

fig, ax = plt.subplots(figsize=(11, 6.4), facecolor=BG)
ax.set_facecolor(BG)
y = np.arange(len(pc))
for i, (_, r) in enumerate(pc.iterrows()):
    v = [r.SOFT, r.MEDIUM, r.HARD]
    ax.plot([min(v), max(v)], [i, i], color=MUT, lw=1, zorder=1, alpha=.7)
for cmp_ in ["SOFT","MEDIUM","HARD"]:
    ax.scatter(pc[cmp_], y, s=58, color=C[cmp_], label=cmp_.title(), zorder=3,
               edgecolor=BG, linewidth=1.2)
ax.axvline(0, color=MUT, lw=1, ls=":")
ax.set_yticks(y); ax.set_yticklabels(pc.circuit, color=FG, fontsize=10)
ax.set_xlabel("degradation  (s per lap of tyre age, fuel-corrected)", color=FG, fontsize=10.5)
ax.set_title("2026 tyre degradation: the track matters ~3x more than the compound",
             color=FG, fontsize=14, pad=16, loc="left")
ax.text(0, 1.012, "17 races, 16,287 race laps, OpenF1 · HARD-SOFT = +0.014 s/lap, 95% CI [-0.003, +0.030]",
        transform=ax.transAxes, color=MUT, fontsize=9.5, va="bottom")
for s in ax.spines.values(): s.set_color(MUT); s.set_linewidth(.6)
ax.tick_params(colors=MUT, labelsize=9); ax.grid(axis="x", color=MUT, alpha=.15, lw=.6)
lg = ax.legend(frameon=False, loc="lower right", fontsize=10)
for t in lg.get_texts(): t.set_color(FG)
plt.tight_layout(); plt.savefig("out/tyre_degradation_2026.png", dpi=190, facecolor=BG)
print("saved out/tyre_degradation_2026.png")
