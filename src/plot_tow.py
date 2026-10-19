import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, pandas as pd, numpy as np
BG, FG, MUT, ACC, RED = "#1A1817", "#D6D2CE", "#6E6862", "#F0D800", "#C84B3C"
T = pd.read_parquet("out/monza_trap.parquet").dropna(subset=["gap"])
T = T[T.gap < 12]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.4), facecolor=BG,
                               gridspec_kw={"width_ratios":[1.35,1]})
# scatter + binned median
ax1.scatter(T.gap, T.vmax, s=11, color=ACC, alpha=.30, lw=0)
T["b"] = pd.cut(T.gap, [0,.5,1,1.5,2,3,4,6,8,12])
g = T.groupby("b", observed=True).agg(v=("vmax","median"), n=("vmax","size"),
                                      lo=("vmax", lambda x: x.quantile(.25)),
                                      hi=("vmax", lambda x: x.quantile(.75)))
g = g[g.n >= 12]; x = [i.mid for i in g.index]
ax1.plot(x, g.v, color=RED, lw=2.4, marker="o", ms=5.5, zorder=3, label="median")
ax1.fill_between(x, g.lo, g.hi, color=RED, alpha=.14, lw=0)
ax1.axvline(1.0, color=MUT, ls=":", lw=1)
ax1.text(1.08, T.vmax.min()+1, "1 s", color=MUT, fontsize=9)
ax1.set_xlabel("gap to car ahead at the speed trap (s)", color=FG)
ax1.set_ylabel("top speed on main straight (km/h)", color=FG)
ax1.set_title("Monza 2026 — the slipstream, measured", color=FG, fontsize=13, loc="left")
lg = ax1.legend(frameon=False, fontsize=9.5, loc="upper right")
for t in lg.get_texts(): t.set_color(FG)

# the three buckets
cat = pd.cut(T.gap, [0,1,2,99], labels=["tow\n(<1 s)","middle\n(1-2 s)","clean air\n(>2 s)"])
d = T.groupby(cat, observed=True).vmax
mu, se, n = d.mean(), d.std()/np.sqrt(d.size()), d.size()
ax2.bar(range(3), mu, yerr=1.96*se, color=[RED, "#E0A030", ACC], width=.62,
        error_kw={"ecolor":FG, "capsize":5, "lw":1.2})
for i,(m,k) in enumerate(zip(mu, n)):
    ax2.text(i, m+1.3, f"{m:.1f}", ha="center", color=FG, fontsize=11, fontweight="bold")
    ax2.text(i, 300.6, f"n={k}", ha="center", color=MUT, fontsize=8.5)
ax2.set_xticks(range(3)); ax2.set_xticklabels(mu.index, color=FG, fontsize=10)
ax2.set_ylim(300, 334); ax2.set_ylabel("top speed (km/h)", color=FG)
ax2.set_title("+10.5 km/h  95% CI [9.4, 11.5]", color=FG, fontsize=13, loc="left")

for ax in (ax1, ax2):
    ax.set_facecolor(BG); ax.tick_params(colors=MUT, labelsize=9)
    ax.grid(axis="y", color=MUT, alpha=.15, lw=.6)
    for s in ax.spines.values(): s.set_color(MUT); s.set_linewidth(.6)
plt.tight_layout(); plt.savefig("out/monza_tow.png", dpi=185, facecolor=BG)
print(g.round(1).to_string())
