import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, pandas as pd, numpy as np
import statsmodels.formula.api as smf, warnings
warnings.simplefilter("ignore")
BG, FG, MUT, ACC, RED = "#1A1817","#D6D2CE","#6E6862","#F0D800","#C84B3C"
D = pd.read_parquet("out/pace_fitted.parquet")
D["stint_len"] = D.groupby(["circuit","driver_number","stint_end"]).lap_number.transform("count")
D = D[D.tyre_age > 3]          # drop warm-up laps, so the caption is true
D["lenbin"] = pd.cut(D.stint_len, [0,10,15,20,25,100], labels=["≤10","11–15","16–20","21–25",">25"])
BASE = "C(circuit) + race_frac + C(compound) + np.log1p(gap_track)"
rows = []
for b, g in D.groupby("lenbin", observed=True):
    if len(g) < 300: continue
    g = g.copy(); g["cl"] = g.circuit+"_"+g.driver_number.astype(str)
    m = smf.ols(f"log_lap ~ tyre_age + {BASE}", data=g).fit(cov_type="cluster", cov_kwds={"groups": g.cl})
    lo, hi = m.conf_int().loc["tyre_age"]
    rows.append({"bin": str(b), "b": m.params["tyre_age"]*100, "lo": lo*100, "hi": hi*100, "n": len(g)})
R = pd.DataFrame(rows)
fig, ax = plt.subplots(figsize=(10.4,5.6), facecolor=BG); ax.set_facecolor(BG)
x = np.arange(len(R))
cols = [RED if v < 0 else ACC for v in R.b]
ax.bar(x, R.b, yerr=[R.b-R.lo, R.hi-R.b], color=cols, width=.6,
       error_kw={"ecolor":FG,"capsize":5,"lw":1.2})
for i, r in enumerate(R.itertuples()):
    off = -0.016 if r.b < 0 else 0.009
    ax.text(i, r.hi+0.009 if r.b>0 else r.lo-0.016, f"{r.b:+.3f}%", ha="center",
            color=FG, fontsize=10.5, fontweight="bold")
    ax.text(i, 0.002 if r.b<0 else -0.006, f"n={r.n}", ha="center", color=MUT, fontsize=8.5)
ax.axhline(0, color=FG, lw=1.2)
ax.set_xticks(x); ax.set_xticklabels(R.bin, color=FG, fontsize=11)
ax.set_xlabel("how many laps the stint actually lasted", color=FG, fontsize=10.5)
ax.set_ylabel("measured tyre degradation (% per lap)", color=FG, fontsize=10.5)
ax.set_title("The same tyres degrade differently depending on when you pitted",
             color=FG, fontsize=14.5, loc="left", pad=46)
ax.text(0, 1.055, "15,125 race laps · teams pit when the tyre is done, so stint length is selected on the outcome\n"
                  "first 3 laps of every stint excluded, so this is not tyre warm-up",
        transform=ax.transAxes, color=MUT, fontsize=9.3, va="bottom")
ax.tick_params(colors=MUT, labelsize=9); ax.grid(axis="y", color=MUT, alpha=.15, lw=.6)
for s in ax.spines.values(): s.set_visible(False)
plt.tight_layout(); plt.savefig("out/survivorship.png", dpi=190, facecolor=BG)
print(R.round(4).to_string(index=False))
