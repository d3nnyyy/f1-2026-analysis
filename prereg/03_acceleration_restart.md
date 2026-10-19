# Pre-registration 4 — acceleration-time restart test
Written 2026-10-19 after validating the measure, BEFORE fitting any restart model on it.

## The change
Previous tests used TOP SPEED, which is drag-dominated: extra power mostly raises the
terminal speed rather than changing what we can measure cleanly. That is why all three
earlier designs returned nulls, and why the race-long trend was unattributable.

New observable: t_accel = seconds from v_lo to v_hi at full throttle, per lap.
Per-circuit bounds (v_lo = p75 of segment start speeds + 5; v_hi = p25 of segment max - 5;
circuits needing >= 40 km/h of window). Outcome is log(t_accel) with unit fixed effects,
so the estimate is a PROPORTIONAL change and pools across circuits of different scale.

## Already validated (not part of the test below)
  slipstream : -6.10%  CI [-7.99, -4.21]  p=2.6e-10   (tow -> faster, correct sign)
  fuel burn  : -0.221% per lap CI [-0.323, -0.119] p=2.1e-05 (lighter -> faster, correct)
Both known effects recovered with the correct sign. Precision +/-1.89% (~57 ms on 3.04 s).

## Primary prediction (committed)
A refilled battery means more deployment available, so the car should accelerate FASTER
out of the corner on the first racing laps after a restart.

  P9.  restart coefficient NEGATIVE (lower t_accel), 95% CI excludes zero.
  P10. decay coefficient closer to zero than restart.

Model: log_t ~ restart + decay + lap + tow + np.log1p(gap) + v_seg_start + C(unit)
       cluster-robust by unit (driver x event).
Same pre-registered windows as PREREG_pooled_sc.md: baseline [dep-8, dep-2],
restart [end+1, end+2], decay [end+3, end+5].
SAME PIT FILTER: drop every driver-event with a stint boundary inside the window.
It stays non-negotiable: fresh tyres also improve corner exit and would fake P9's sign.

## Dose-response (committed, directional)
  P11. effect larger (more negative) after LONGER neutralisations (restart x sc_laps).

## Decision rule
  PASS  : P9 holds AND survives the pit filter AND the gap/tow controls.
  NULL  : CI includes zero -> report null + achieved precision.
  WRONG-SIGN : restart POSITIVE with CI excluding zero -> report as such; would suggest
          cold tyres/brakes dominate, not energy.

## Note on multiplicity
This is the 4th design tested today. Three returned nulls. If this one is significant at
the margin I will say explicitly that it is the 4th look, and that a borderline p-value
after four attempts is weak evidence, not a discovery.
