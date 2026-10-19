"""
2026 tyre degradation: is the compound hierarchy really inverted?

Two published analyses disagree. Hypothesis: the disagreement is a pooling +
fuel-confound artifact, not a real inversion.

Within one stint, tyre_age and lap_number move 1:1, so degradation and fuel
burn are collinear. They are only separately identified because the same tyre
age occurs at different race laps ACROSS stints. A model without a fuel term
estimates (degradation - fuel_burn), and since compounds are not randomly
allocated across the race, that bias differs by compound.
"""
import json, glob, warnings
import numpy as np, pandas as pd
import statsmodels.formula.api as smf

def CL(df):
    """Cluster by driver-stint-race: consecutive laps on one set of tyres are
    not independent observations, and plain OLS SEs would be far too small."""
    g = (df.circuit.astype(str) + "_" + df.driver_number.astype(str)
         + "_" + df.stint_number.astype(str))
    return {"cov_type": "cluster", "cov_kwds": {"groups": g}}
warnings.simplefilter("ignore")
pd.set_option("display.width", 200)

DRY = ["SOFT", "MEDIUM", "HARD"]

def build():
    idx = json.load(open("out/race_index.json"))
    frames = []
    for r in idx:
        sk = r["session_key"]
        try:
            laps = pd.DataFrame(json.load(open(f"data/laps_session_key={sk}.json")))
            stints = pd.DataFrame(json.load(open(f"data/stints_session_key={sk}.json")))
        except FileNotFoundError:
            continue
        if laps.empty or stints.empty:
            continue
        # attach stint -> each lap, and compute true tyre age
        recs = []
        for _, s in stints.iterrows():
            m = ((laps.driver_number == s.driver_number)
                 & (laps.lap_number >= s.lap_start) & (laps.lap_number <= s.lap_end))
            sub = laps[m].copy()
            if sub.empty:
                continue
            sub["compound"] = s.compound
            sub["stint_number"] = s.stint_number
            sub["tyre_age"] = sub.lap_number - s.lap_start + (s.tyre_age_at_start or 0)
            sub["stint_end"] = s.lap_end
            sub["stint_len"] = int(s.lap_end - s.lap_start + 1)
            sub["is_last_stint"] = s.stint_number == stints[stints.driver_number == s.driver_number].stint_number.max()
            recs.append(sub)
        if not recs:
            continue
        d = pd.concat(recs)
        d["circuit"] = r["circuit"] or r["country"]
        d["race_date"] = r["date"]
        d["round_idx"] = idx.index(r) + 1
        frames.append(d)
    return pd.concat(frames, ignore_index=True)

def clean(d):
    n0 = len(d)
    rep = []
    def drop(mask, why):
        nonlocal d
        k = mask.sum(); d = d[~mask]; rep.append((why, int(k)))
    drop(~d.compound.isin(DRY), "wet/unknown compound")
    drop(d.lap_duration.isna(), "no lap_duration")
    drop(d.is_pit_out_lap.fillna(False).astype(bool), "pit-out lap")
    drop((d.lap_number == d.stint_end) & (~d.is_last_stint), "pit-in lap")
    drop(d.lap_number <= 1, "lap 1 (standing start)")
    # robust per-race pace filter: kills SC/VSC/yellow/traffic laps.
    # recompute the median AFTER the structural drops, and re-derive it between
    # filters so the mask always aligns with the current frame.
    med = d.groupby(["circuit", "driver_number"]).lap_duration.transform("median")
    drop(d.lap_duration > 1.07 * med, ">107% of driver's race median (SC/VSC/traffic)")
    med = d.groupby(["circuit", "driver_number"]).lap_duration.transform("median")
    drop(d.lap_duration < 0.90 * med, "<90% of median (timing glitch)")
    print(f"cleaning: {n0} -> {len(d)} laps")
    for why, k in rep:
        print(f"   -{str(k).rjust(6)}  {why}")
    return d

def main():
    d = clean(build())
    d["compound"] = pd.Categorical(d.compound, categories=["MEDIUM", "SOFT", "HARD"])
    d["fe"] = d.circuit.astype(str) + "_" + d.driver_number.astype(str)
    print(f"\nraces={d.circuit.nunique()}  drivers={d.driver_number.nunique()}  laps={len(d)}")
    print("\nlaps by compound:\n", d.compound.value_counts().to_string())

    # --- the mechanism check: are compounds run at different points in the race? ---
    print("\n=== allocation imbalance (the confound) ===")
    print(d.groupby("compound", observed=True)
            .agg(mean_race_lap=("lap_number","mean"),
                 mean_tyre_age=("tyre_age","mean"),
                 mean_stint_len=("stint_len","mean"),
                 n=("lap_duration","size")).round(1).to_string())

    out = {}
    # --- A: naive pooled, no fuel term, no track control ---
    a = smf.ols("lap_duration ~ tyre_age * compound", data=d).fit(**CL(d))
    out["A_naive_pooled"] = {c: a.params["tyre_age"] + a.params.get(f"tyre_age:compound[T.{c}]", 0.0)
                             for c in DRY}
    # --- B: + track/driver fixed effects, still no fuel term ---
    b = smf.ols("lap_duration ~ tyre_age * compound + C(fe)", data=d).fit(**CL(d))
    out["B_plus_trackdriver_FE"] = {c: b.params["tyre_age"] + b.params.get(f"tyre_age:compound[T.{c}]", 0.0)
                                    for c in DRY}
    # --- C: + fuel term (lap_number). the identified model ---
    c_ = smf.ols("lap_duration ~ tyre_age * compound + lap_number + C(fe)", data=d).fit(**CL(d))
    out["C_plus_fuel"] = {c: c_.params["tyre_age"] + c_.params.get(f"tyre_age:compound[T.{c}]", 0.0)
                          for c in DRY}

    print("\n=== degradation slope, s/lap, by model ===")
    res = pd.DataFrame(out).T[DRY].round(4)
    res["HARD-SOFT"] = (res.HARD - res.SOFT).round(4)
    print(res.to_string())
    print("\n=== HARD - SOFT contrast, model C, cluster-robust ===")
    for nm, mod in [("A_naive", a), ("B_plus_FE", b), ("C_plus_fuel", c_)]:
        t = mod.t_test("tyre_age:compound[T.HARD] - tyre_age:compound[T.SOFT] = 0")
        lo, hi = t.conf_int()[0]
        eff = float(np.ravel(t.effect)[0]); pv = float(np.ravel(t.pvalue)[0])
        print(f"  {nm.ljust(12)} {eff:+.4f} s/lap  95% CI [{lo:+.4f}, {hi:+.4f}]  p={pv:.3f}")
    print(f"\nfuel coefficient (model C): {c_.params['lap_number']:+.4f} s per race lap")
    print(f"   (expect NEGATIVE ~-0.03..-0.06: car lightens, laps get quicker)")

    # --- D: per-circuit slopes, to test 'track dominates' ---
    rows = []
    for ck, g in d.groupby("circuit"):
        if g.compound.nunique() < 2 or len(g) < 150:
            continue
        try:
            m = smf.ols("lap_duration ~ tyre_age * compound + lap_number + C(driver_number)", data=g).fit()
            rows.append({"circuit": ck, "n": len(g),
                         **{c: m.params["tyre_age"] + m.params.get(f"tyre_age:compound[T.{c}]", 0.0)
                            for c in DRY}})
        except Exception:
            pass
    pc = pd.DataFrame(rows).set_index("circuit")
    print("\n=== per-circuit degradation (model C per race) ===")
    print(pc.round(3).to_string())
    print("\nmean of within-circuit slopes:\n", pc[DRY].mean().round(4).to_string())
    print("\nspread across circuits (sd):\n", pc[DRY].std().round(4).to_string())
    pc.to_csv("out/per_circuit_degradation.csv")
    d.to_parquet("out/laps_clean.parquet")
    print("\nsaved -> out/laps_clean.parquet, out/per_circuit_degradation.csv")

main()
