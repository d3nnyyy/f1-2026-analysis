import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, pandas as pd, numpy as np
BG, FG, MUT = "#1A1817", "#D6D2CE", "#6E6862"
m = pd.read_parquet("out/monza_ver_xy.parquet")
m = m[m.speed > 60]

fig, ax = plt.subplots(figsize=(8.5, 9), facecolor=BG); ax.set_facecolor(BG)
sc = ax.scatter(m.x, m.y, c=m.speed, s=2.2, cmap="inferno", vmin=60, vmax=350, lw=0)
cb = fig.colorbar(sc, ax=ax, fraction=.035, pad=.02)
cb.set_label("speed (km/h)", color=FG); cb.ax.yaxis.set_tick_params(color=MUT)
plt.setp(plt.getp(cb.ax, "yticklabels"), color=MUT)
cb.outline.set_edgecolor(MUT)
top = m.nlargest(400, "speed")
ax.scatter(top.x, top.y, s=16, facecolor="none", edgecolor="#F0D800", lw=.8, label="top 400 speed samples")
ax.set_title("Monza — every position sample, coloured by speed", color=FG, fontsize=13, loc="left")
ax.set_aspect("equal"); ax.tick_params(colors=MUT, labelsize=8)
for s in ax.spines.values(): s.set_color(MUT); s.set_linewidth(.6)
lg = ax.legend(frameon=False, loc="upper left", fontsize=9)
for t in lg.get_texts(): t.set_color(FG)
plt.tight_layout(); plt.savefig("out/monza_track.png", dpi=180, facecolor=BG)
print("saved")
# where exactly are the fastest samples?
top["cluster"] = (top.x > 2000).map({True: "east", False: "west"})
print(top.groupby("cluster").agg(n=("speed","size"), x=("x","mean"), y=("y","mean"),
                                 vmax=("speed","max"), vmed=("speed","median")).round(0).to_string())
