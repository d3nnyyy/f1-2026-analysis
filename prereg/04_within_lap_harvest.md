# Pre-registration 5 — within-lap harvest test
Written 2026-10-19, before fitting any model on withinlap.parquet.

## The idea
Compare different STRAIGHTS OF THE SAME LAP. Within one lap the fuel load, tyre
compound, tyre age, driver, car and track evolution are identical by construction, so
none of them can confound the contrast. Pit stops are irrelevant, so the pit filter that
destroyed 64% of the restart sample is not needed: n = 4,826 vs 737.

Energy recovered under braking scales with the kinetic energy dissipated, ~ d(v^2).
So the run-up to each straight has a measurable HARVEST OPPORTUNITY, and it varies
lap to lap for the same corner (traffic, lines, mistakes, lift-and-coast).

## Primary prediction (committed)
  P12. More energy dissipated in the run-up -> more harvest -> more deployment available
       -> FASTER acceleration on the following straight.
       Coefficient on dv2_before NEGATIVE on log(t_accel), 95% CI excludes zero.

Model: log_t ~ dv2_before + tow + np.log1p(gap) + lap + C(unit)
       unit = driver x event x straight-index, so every comparison is the SAME corner
       and the SAME straight, varying only lap to lap.
       Cluster-robust by unit.

## Validation first (must pass, else the measure is junk here)
  V1. tow -> faster acceleration (negative), as it did on the earlier measure (-6.1%).
  V2. lap number -> faster (negative), fuel burn, as before (-0.22%/lap).
If either fails, stop; the within-lap slicing has broken something.

## Threats and their directions
  - Braking harder because you were COMPROMISED (traffic, mistake, dirty air) also means
    a worse exit -> SLOWER acceleration. That biases AGAINST P12. Conservative.
  - Arriving faster (a tow) means more speed to shed AND better acceleration -> would bias
    FOR P12. Controlled by tow + log1p(gap).
  - Measurement starts at a FIXED speed v_lo per (circuit, straight), so a slower corner
    exit does not mechanically change where the clock starts.

## Decision rule
  PASS : P12 negative, CI excludes zero, survives the gap/tow controls.
  NULL : CI includes zero.
  WRONG-SIGN : positive with CI excluding zero -> the compromise channel dominates;
         report as such and do NOT reinterpret it as an energy finding.

## Multiplicity — stated up front
This is the FIFTH design tested today; four returned nulls. A borderline result here is
weak evidence. I will report the leave-one-circuit-out stability and will not treat a
p just under 0.05 as a discovery.
