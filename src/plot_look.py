import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, pandas as pd, numpy as np
BG, FG, MUT, ACC = "#1A1817", "#D6D2CE", "#6E6862", "#F0D800"

d = pd.read_parquet("out/monza_ver_telemetry.parquet")
d = d[(d.t >= "2026-09-06 13:00") & (d.t <= "2026-09-06 15:05")]   # race only
seg = pd.read_csv("out/monza_ver_segments.csv", parse_dates=["t0","t1"])
seg = seg[seg.t0 >= "2026-09-06 13:00"].nlargest(24, "dur")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.6), facecolor=BG)
accs = []
for _, s in seg.iterrows():
    g = d[(d.t >= s.t0) & (d.t <= s.t1)].copy()
    if len(g) < 12: continue
    g["te"] = (g.t - s.t0).dt.total_seconds()
    v = g.speed.values / 3.6                                   # m/s
    a = np.gradient(v, g.te.values)                            # m/s^2
    ax1.plot(g.te, g.speed, color=ACC, alpha=.30, lw=1.2)
    k = (g.te > 1) & (g.te < s.dur - .6)
    accs.append(pd.DataFrame({"v": g.speed.values[k], "a": a[k]}))
A = pd.concat(accs)

ax1.set_title("Monza, Verstappen — every long full-throttle run", color=FG, fontsize=12.5, loc="left")
ax1.set_xlabel("seconds into full throttle", color=FG); ax1.set_ylabel("speed (km/h)", color=FG)

# binned acceleration vs speed
A["bin"] = pd.cut(A.v, np.arange(200, 340, 8))
b = A.groupby("bin", observed=True).a.agg(["median", "count",
        lambda x: x.quantile(.15), lambda x: x.quantile(.85)])
b.columns = ["med","n","q15","q85"]; b = b[b.n >= 25]
x = [i.mid for i in b.index]
ax2.fill_between(x, b.q15, b.q85, color=ACC, alpha=.18, lw=0)
ax2.plot(x, b.med, color=ACC, lw=2.2, marker="o", ms=4)
ax2.axhline(0, color=MUT, ls=":", lw=1)
ax2.set_title("acceleration vs speed, at full throttle", color=FG, fontsize=12.5, loc="left")
ax2.set_xlabel("speed (km/h)", color=FG); ax2.set_ylabel("acceleration (m/s²)", color=FG)

for ax in (ax1, ax2):
    ax.set_facecolor(BG); ax.tick_params(colors=MUT)
    ax.grid(color=MUT, alpha=.15, lw=.6)
    for s_ in ax.spines.values(): s_.set_color(MUT); s_.set_linewidth(.6)
plt.tight_layout(); plt.savefig("out/monza_look.png", dpi=185, facecolor=BG)
print("laps plotted:", len(seg), " accel samples:", len(A))
print(b.round(2).to_string())
