import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, pandas as pd, numpy as np
BG, FG, MUT, ACC, RED = "#1A1817","#D6D2CE","#6E6862","#F0D800","#C84B3C"
A = pd.read_parquet("out/overtaking.parquet")
A = A[A.gap.between(0,30)]
bins = [0,.5,1,1.5,2,3,5,10,30]
A["bin"] = pd.cut(A.gap, bins)
t = A.groupby("bin", observed=True).agg(n=("passed","size"), rate=("passed","mean"))
t = t[t.n >= 40]
t["se"] = np.sqrt(t.rate*(1-t.rate)/t.n)
labs = ["<0.5 s","0.5–1 s","1–1.5 s","1.5–2 s","2–3 s","3–5 s","5–10 s","10–30 s"][:len(t)]
fig, ax = plt.subplots(figsize=(10.6,5.6), facecolor=BG); ax.set_facecolor(BG)
x = np.arange(len(t))
cols = [ACC] + [MUT]*(len(t)-1)
ax.bar(x, t.rate*100, yerr=t.se*196, color=cols, width=.66,
       error_kw={"ecolor":FG,"capsize":4,"lw":1.1})
for i,(r,n) in enumerate(zip(t.rate, t.n)):
    ax.text(i, r*100+2.2, f"{r*100:.1f}%", ha="center", color=FG, fontsize=11, fontweight="bold")
    ax.text(i, 1.2, f"n={int(n)}", ha="center", color=MUT, fontsize=8)
ax.set_xticks(x); ax.set_xticklabels(labs, color=FG, fontsize=10)
ax.set_ylabel("chance of completing a pass by the next lap", color=FG, fontsize=10.5)
ax.set_ylim(0, 45)
ax.set_title("Overtaking in 2026 lives inside half a second",
             color=FG, fontsize=15, loc="left", pad=30)
ax.text(0, 1.045, "15,592 driver-laps, 17 races · pit-stop position changes removed · gap to the car ahead",
        transform=ax.transAxes, color=MUT, fontsize=9.3, va="bottom")
ax.tick_params(colors=MUT, labelsize=9); ax.grid(axis="y", color=MUT, alpha=.15, lw=.6)
for s in ax.spines.values(): s.set_visible(False)
ax.spines["bottom"].set_visible(True); ax.spines["bottom"].set_color(MUT)
plt.tight_layout(); plt.savefig("out/overtaking.png", dpi=190, facecolor=BG)
print(t.round(3).to_string())
