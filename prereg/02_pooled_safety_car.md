# Pre-registration 3 — pooled safety-car restart test
Written 2026-10-19 while the data was still downloading. No pooled model has been fitted.

## Design
13 usable SC/VSC events, 12 circuits, ~19 drivers each.
Window per event: 8 laps before deployment -> 9 laps after.

  baseline : laps [L-8, L-2]      (L = deployment lap)
  restart  : laps [end+1, end+2]  (end = lap the SC/VSC ENDED, from race_control)
  decay    : laps [end+3, end+5]

Outcome: vmax = per-lap top speed on the fastest straight (the validated trap).

## Primary model (committed, ONE number)
  vmax ~ restart + decay + lap + log1p(gap) + v_entry + accel_time + C(driver x event)
  cluster-robust SEs by driver x event.

  P5. restart coefficient POSITIVE, 95% CI excludes zero.
  P6. decay coefficient smaller than restart (the bump fades).

Pooled across ALL 13 events with event fixed effects. I am NOT selecting a subset of
circuits. Any per-circuit breakdown is exploratory and will be labelled as such.

## CONFOUND I must handle: pit stops cluster at safety cars
A SC is a cheap time to pit, so many cars take fresh tyres DURING the window. Fresh tyres
give a better corner exit and would produce a positive restart coefficient that has
nothing to do with the battery.
  Mitigation (committed): DROP every driver-event where a stint boundary falls inside
  the window. Baseline and restart laps must be on the SAME set of tyres.
  This is the single most important filter in the design.

## Other threats, and their directions
  - cold tyres after slow laps -> WORSE exit -> biases AGAINST P5 (conservative, fine)
  - bunching -> more tow -> biases FOR P5. Controlled by log1p(gap). At Monza my threat
    model had this backwards (restart gaps were LARGER, 3.16 s vs 1.27 s), so I am not
    assuming the direction; the gap covariate handles it either way.
  - track position changes during SC -> absorbed by driver x event FE + gap.

## Secondary, pre-registered as a DOSE-RESPONSE (exploratory but directional)
  P7. If the restart bump is energy, it should be LARGER at circuits with longer straights,
      because that is where deployment runs out. Proxy for straight length: median
      accel_time (seconds at full throttle into the trap) per circuit.
      Test: interact restart x median_accel_time. Prediction: POSITIVE interaction.
  A null primary with a positive dose-response would be interesting but NOT a finding.
  A positive primary with a FLAT dose-response would make me suspect an artifact.

## Decision rule
  PASS       : P5 holds AND survives the pit-stop filter AND the gap control.
  NULL       : CI includes zero. Report null + the achieved detection floor.
  CONFOUNDED : significant only without the pit filter or gap control -> report as such.

## Power
Monza alone: n=30 restart laps, CI half-width +/-2.2 km/h.
Expected here: ~10-13x the events -> floor should fall to roughly +/-0.6-0.8 km/h.
I will report the ACHIEVED half-width whatever the result, so a null is interpretable.

## Addendum, same day, BEFORE any pooled fit
Discovered while pinning end-laps: SC/VSC duration varies 0-5 laps (median 1).
Shanghai 3, Suzuka 5, the rest 0-2. Longer neutralisation = more time lifting and
braking with no deployment = more recharge.

  P8. DOSE-RESPONSE ON DURATION: the restart bump should be LARGER after longer
      neutralisations. Test: interact restart x sc_laps. Prediction POSITIVE.

Declared now, before fitting, so it is a prediction and not a post-hoc slice.
Note the two zero-duration events (Melbourne 34, Silverstone 22) are weak treatments
by this logic and should show little or nothing. They stay in the primary pool.
