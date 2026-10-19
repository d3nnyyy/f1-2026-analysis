# Pre-registration — Monza clean-air test
Written: 2026-10-19, BEFORE running. Data already in hand (Monza race, 307 clean-air laps),
so this is not blind to the dataset — but it IS blind to the result: no model of
vmax ~ lap_number has been fitted at any point.

## Why this test, and why it comes before the battery test

The fuel effect is a SECOND positive control, and simultaneously a power analysis.

A car burns ~100 kg of fuel over a race. Lighter car -> higher top speed. This is known
physics, nobody disputes it, and it is the same KIND of effect as the battery: a change in
available power-to-mass showing up in straight-line speed.

So:
- if the trap CAN see 100 kg of fuel, it is sensitive to power/mass, and the battery test
  is worth running.
- if the trap CANNOT see 100 kg of fuel, then top speed at Monza is purely drag-limited and
  insensitive to power/mass. In that case it can NEVER see energy management either, the
  battery test is dead on arrival at this circuit, and I stop rather than fish.

This is the step I skipped in v1: asking whether the measurement had the power to detect
the effect BEFORE interpreting a null as evidence.

## Primary prediction (committed)

Model:  vmax ~ lap_number + C(driver),  clean air only (gap > 2 s), Monza race.

  P1. Slope on lap_number is POSITIVE.
  P2. Magnitude between +0.03 and +0.10 km/h per lap
      (= +1.6 to +5.3 km/h across 53 laps).

## Decision rule (committed)

  PASS  : slope positive AND 95% CI excludes zero AND point estimate in [0.02, 0.15]
          -> instrument is mass/power sensitive. Proceed to the battery test.
  FAIL-FLAT : CI includes zero -> trap is drag-limited, insensitive. STOP. Report that
          the battery is not detectable from top speed at Monza.
  FAIL-WEIRD: slope negative and CI excludes zero -> something is wrong with the pipeline
          or an uncontrolled confound dominates. STOP and diagnose, do not reinterpret.

## Known threat to this test
Tyre age is correlated with lap number within a stint. Fresh tyres give a better corner
exit onto the straight, which raises top speed independently of mass. Mitigation: a
corner-entry speed covariate (minimum speed in the 15 s before the trap = Parabolica),
reported as a SECONDARY model. The primary decision rests on the simple model above.

## What I am NOT doing
Not testing multiple slicings and reporting the best. One model, one slope, one decision.

---

# Pre-registration 2 — the VSC natural experiment
Written 2026-10-19, after the fuel test, BEFORE fitting anything involving the VSC.

## Why
The race-long trend (+7 to +9 km/h) is real but UNATTRIBUTABLE: lap number, fuel load and
tyre age are collinear, and the sign of the lap coefficient flips when tyre age enters.
A monotonic trend cannot separate them.

A VSC breaks the collinearity. Monza: VSC DEPLOYED lap 28, VSC ENDING lap 29.
Across it:
  - fuel        : keeps burning (slightly faster per lap, cars are slow) -> no jump
  - tyre age    : +2 laps -> no jump
  - BATTERY     : two slow laps of braking and lifting with no deployment -> REFILLED

So a discontinuity at the restart is attributable to energy in a way a trend is not.

## Prediction (committed)
  P3. Top speed on the first 2 racing laps after the restart (laps 30-31) is HIGHER
      than the race-long trend predicts at those laps.
  P4. The excess decays: laps 32-34 sit closer to trend than laps 30-31.

Magnitude: no strong prior. I expect single-digit km/h if real. I am NOT committing to a
size, only to the SIGN and the DECAY.

## Known threat
A VSC bunches the field, so post-restart laps have SMALLER gaps and therefore MORE tow.
The tow is +10.5 km/h and would produce a false positive of exactly the predicted sign.
Mitigation: gap enters the model as a covariate (log1p) rather than filtering, to keep n.
If the post-VSC coefficient is not robust to the gap control, I report it as confounded.

## Decision rule
  PASS      : laps 30-31 coefficient positive, 95% CI excludes zero, survives gap control.
  NULL      : CI includes zero -> report as null, note the power.
  CONFOUNDED: significant without gap control, not with it -> report as tow, not battery.
