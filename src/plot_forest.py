import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, pandas as pd, numpy as np
import statsmodels.formula.api as smf, warnings
warnings.simplefilter("ignore")
BG, FG, MUT, ACC, RED = "#1A1817", "#D6D2CE", "#6E6862", "#F0D800", "#C84B3C"
D = pd.read_parquet("out/pooled_analysis.parquet")
F = "vmax ~ restart + decay + lap + np.log1p(gap) + v_entry + accel_time + C(unit)"

rows = []
for c, g in D.groupby("circuit"):
    if g.restart.sum() < 4 or g.unit.nunique() < 3: continue
    try:
        m = smf.ols(F, data=g).fit()
        lo, hi = m.conf_int().loc["restart"]
        rows.append({"circuit": c, "b": m.params["restart"], "lo": lo, "hi": hi,
                     "n": int(g.restart.sum()), "straight": g.accel_time.median()})
    except Exception: pass
R = pd.DataFrame(rows).sort_values("straight")
m = smf.ols(F, data=D).fit(cov_type="cluster", cov_kwds={"groups": D.unit})
plo, phi = m.conf_int().loc["restart"]; pb = m.params["restart"]

fig, ax = plt.subplots(figsize=(10.5, 6.2), facecolor=BG); ax.set_facecolor(BG)
y = np.arange(len(R))
ax.hlines(y, R.lo, R.hi, color=ACC, lw=2, alpha=.75)
ax.scatter(R.b, y, s=46, color=ACC, zorder=3, edgecolor=BG, lw=1)
ax.hlines(-1.6, plo, phi, color=RED, lw=3.4)
ax.scatter([pb], [-1.6], s=150, color=RED, marker="D", zorder=4, edgecolor=BG, lw=1.2)
ax.axvline(0, color=FG, ls=":", lw=1.1)
labs = [f"{r.circuit}  (n={r.n})" for _, r in R.iterrows()]
ax.set_yticks(list(y)+[-1.6]); ax.set_yticklabels(labs+["POOLED (pre-registered)"], color=FG, fontsize=9.5)
ax.get_yticklabels()[-1].set_color(RED); ax.get_yticklabels()[-1].set_fontweight("bold")
ax.set_xlabel("top-speed change at the safety-car restart (km/h)", color=FG, fontsize=10.5)
ax.set_title("Does a refilled battery show up at the restart?", color=FG, fontsize=13.5, loc="left", pad=30)
ax.text(0, 1.035, f"13 events / 12 circuits · pit-stop-contaminated driver-events dropped · "
                  f"pooled {pb:+.2f} km/h, 95% CI [{plo:+.2f}, {phi:+.2f}] — NULL",
        transform=ax.transAxes, color=MUT, fontsize=9.3, va="bottom")
ax.set_ylim(-3, len(R)); ax.tick_params(colors=MUT, labelsize=9)
ax.grid(axis="x", color=MUT, alpha=.15, lw=.6)
for s in ax.spines.values(): s.set_color(MUT); s.set_linewidth(.6)
plt.tight_layout(); plt.savefig("out/restart_forest.png", dpi=185, facecolor=BG)
print(R.round(2).to_string(index=False))
