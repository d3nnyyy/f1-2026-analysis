import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, pandas as pd, numpy as np
import statsmodels.formula.api as smf, warnings
warnings.simplefilter("ignore")
BG, FG, MUT, ACC, RED, GRY = "#1A1817","#D6D2CE","#6E6862","#F0D800","#C84B3C","#8A837C"
A = pd.read_parquet("out/withinlap_analysis.parquet")
CL = {"cov_type":"cluster","cov_kwds":{"groups": A.unit}}
F  = "log_t ~ dv2k + tow + np.log1p(gap) + lap + C(unit)"
m  = smf.ols(F, data=A).fit(**CL)
iqr = A.dv2k.quantile(.75) - A.dv2k.quantile(.25)
def row(k, scale, lbl):
    b = m.params[k]*scale; lo, hi = m.conf_int().loc[k]*scale
    return {"lbl": lbl, "b": b*100, "lo": lo*100, "hi": hi*100}
E = pd.DataFrame([
    row("tow", 1, "Slipstream\n(within 1 s of car ahead)"),
    row("lap", 10, "Fuel burn\n(per 10 laps)"),
    row("dv2k", iqr, "Energy harvested in braking\n(IQR of run-up, the battery test)"),
])
fig, ax = plt.subplots(figsize=(10.8, 4.6), facecolor=BG); ax.set_facecolor(BG)
cols = [ACC, ACC, RED]
y = np.arange(len(E))[::-1]
for i, (_, r) in enumerate(E.iterrows()):
    yy = y[i]
    ax.hlines(yy, r.lo, r.hi, color=cols[i], lw=3.4, alpha=.9)
    ax.scatter(r.b, yy, s=95, color=cols[i], zorder=3, edgecolor=BG, lw=1.4)
    tx = r.hi + 0.45 if r.b > -2 else r.lo - 0.45
    ha = "left" if r.b > -2 else "right"
    ax.text(tx, yy, f"{r.b:+.2f}%", color=cols[i], fontsize=10.5, va="center", ha=ha, fontweight="bold")
ax.axvline(0, color=FG, ls=":", lw=1.1)
ax.set_yticks(y); ax.set_yticklabels(E.lbl, color=FG, fontsize=10)
ax.get_yticklabels()[-1].set_color(RED)
ax.set_xlabel("change in acceleration time  (negative = car accelerates faster)", color=FG, fontsize=10.5)
ax.set_title("What the instrument can see — and what isn't there", color=FG, fontsize=14, loc="left", pad=26)
ax.text(0, 1.045, "4,783 straights, same-lap comparison · 10 circuits · everything else held fixed by construction",
        transform=ax.transAxes, color=MUT, fontsize=9.3, va="bottom")
ax.set_xlim(-11, 7); ax.tick_params(colors=MUT, labelsize=9)
ax.grid(axis="x", color=MUT, alpha=.15, lw=.6)
for s in ax.spines.values(): s.set_color(MUT); s.set_linewidth(.6)
plt.tight_layout(); plt.savefig("out/sensitivity_ladder.png", dpi=190, facecolor=BG)
print(E.round(2).to_string(index=False))
