# f1-lab — 2026 season

## Project 2: tyre degradation — DONE
17 races, 16,287 clean race laps (OpenF1).
- Fuel coefficient -0.0420 s/race-lap (pre-registered prediction: -0.03..-0.06). PASSED.
- HARD - SOFT = +0.014 s/lap, 95% CI [-0.003, +0.030], p=0.105. NOT significant.
- Sign stable: leave-one-circuit-out 17/17 same sign, range +0.006..+0.023.
- Track-to-track sd = 0.041 s/lap = 2.9x the compound difference.
- Verdict: "hierarchy inverted" overclaims; "track dominates" is the better description.
- UNRESOLVED: censoring. Teams pit when tyres are done -> survivor bias toward low
  degradation, plausibly stronger for SOFT.
- Silverstone SOFT slope (-0.221) is garbage: 31 laps, 12 stints, max age 12. Excluded.

## Project 1: infer battery state from telemetry — PREMISE NOT SUPPORTED (v1)
Idea: battery state of charge is never published; detect "clipping" (foot flat,
car stops pulling) as its fingerprint.

Three tests at Monza, all null:
1. quali vs race top speed  -> race FASTER by ~8 km/h (wrong direction; confounded
   by slipstream and by out-laps in the quali median)
2. shape of acceleration decay -> quali 16.0% vs race 16.7% of full-throttle time at
   |a|<0.25 m/s^2. Median longest flat run 0.48 s in BOTH = 2 samples = noise.
3. bimodality of delivered power -> absent in 11/12 speed bins.

My error: the "8-second flat plateau" I saw in the speed plot was an axis artifact.
At that y-scale a car gaining 1 km/h/s looks flat but is pulling 0.28 m/s^2.

Diagnosis — this is an IDENTIFIABILITY problem, not only a resolution one:
clipping happens near terminal velocity, where acceleration ~ 0 whatever the power.
More power raises the terminal SPEED; it does not change the shape. So the signal
lives in the LEVEL of top speed, which needs a clean baseline.
  - measurement floor: speed is integer km/h at 4.2 Hz -> 1.16 m/s^2 quantisation noise
  - a full 350 kW cut at 250 km/h would be 6.3 m/s^2 (detectable) but clipping does
    not happen at 250 km/h; it happens at 310+, where it is masked by drag.

## v2 — BUILT AND VALIDATED
Remove the slipstream confound instead of abandoning the premise:
  - `location` (x,y,z, ~3 Hz) -> pin the identical track position every lap
  - `intervals` (gap to car ahead) -> keep only clean-air laps (interval > 2 s)
  - then test whether top speed at that fixed point varies across a stint in a way
    energy management predicts
RESULTS:
- Track map from `location` confirms the trap sits on Monza's main straight
  (380 of the 400 fastest samples).
- POSITIVE CONTROL PASSED: slipstream = +10.5 km/h, 95% CI [9.4, 11.5], p=5e-67,
  monotonic across 9 gap bins, flattening past ~3 s as a slipstream physically should.
  This also retroactively explains the v1 failure: the tow is larger than the 8 km/h
  quali-vs-race anomaly that broke v1, so the v1 control was swamped, as suspected.
- SECOND CONTROL PASSED (direction): clean-air top speed rises +0.14 km/h per lap,
  CI [0.092, 0.189] = +7.4 km/h per race. Predicted +1.6..+5.3, so it OVERSHOT.
- NOT ATTRIBUTABLE: adding tyre_age flips the lap coefficient to -0.18 while tyre_age
  takes +0.37. lap / fuel / tyre age are collinear. Same wall as project 2.
- VSC natural experiment at Monza: NULL. restart +1.11 km/h, CI [-1.08, +3.31], n=30,
  detection floor +/-2.2 km/h. Signs of P3/P4 both correct but indistinguishable from 0.
  My stated threat model was BACKWARDS: I predicted restart laps would have more tow;
  median gap was actually LARGER at restart (3.16 s vs 1.27 s pre-VSC).

## v3 — pooled across the season (in progress)
13 usable SC/VSC events / 12 circuits, from 35 total (rest fail the pre-registered
window rules: too early, events stacked too close, no room after).
Pre-registrations: PREREG_monza_fuel.md, PREREG_pooled_sc.md (+ addendum P8).
Key filter: DROP driver-events that pitted inside the window (SCs are cheap pit windows;
fresh tyres would fake the exact effect we want).

## Fetch engineering notes
- OpenF1's real rate cap is MUCH tighter than the documented 30/min: measured 5 successes
  then hard 429s within 3.4 s. Backoff costs more than throttling -> settled at 16/min.
- Windowing is the big lever: full-race car_data = 5.5 MB / 3.6 s per driver;
  a 17-lap window = 0.19 MB / 0.3 s. ~20x smaller.
- Concurrency across SEPARATE PROCESSES does not help (server-side per-IP quota).
  Threads + one shared token bucket is the right shape.
- `intervals` (262 requests) turned out to be UNNECESSARY: gap to car ahead is derivable
  from lap-crossing times already on disk. Validated at Monza - derived gap reproduces
  the tow at +11.42 km/h vs the API's +10.98, overlapping CIs. See gaps.py.
- pkill -f <script> self-matched my own monitor scripts and killed them. Use PID.

## Data notes
- FastF1 is DEAD: livetiming.formula1.com returns 401 on every season (checked 2024 + 2026).
- OpenF1 free tier: 3 req/s, 30/min. Disk cache in data/. Fetcher: fetch.py
- OpenF1 has PHANTOM sessions (Bahrain 2026-04-12, Saudi 2026-04-19) that 404 on laps.
- OpenF1 drops Australia from session_type=Race queries -> enumerate via meetings.
- Timestamps are mixed ISO8601 (some with microseconds) -> parse with format="ISO8601".
- `drs` is null on every 2026 row. No DRS in these regs.

## v3 RESULT — pooled safety-car restart test: NULL

Data: 13 events, 12 circuits, 284 windowed telemetry pulls (0 failures).
After the pre-registered pit filter: 772 laps, 81 driver-events, 116 restart laps.
The pit filter removed 169 of 258 driver-events (65%) — SCs really are when teams pit.

PRIMARY (pre-registered, one fit):
  restart (end+1..+2)   +0.23 km/h   95% CI [-2.13, +2.59]   p=0.85   -> NULL
  decay   (end+3..+5)   +0.18 km/h   95% CI [-2.71, +3.08]
  achieved detection floor: +/-2.36 km/h

Pooling DID work. My earlier claim that the pooled CI was "worse than Monza" was wrong:
I was comparing against the old Monza script, which never applied the pit filter (722 rows
vs 153). Like-for-like under the pre-registered spec:
  Monza alone  +/-4.32 km/h (clustered)
  Pooled       +/-2.36 km/h      -> roughly halved, as sqrt(n) predicts.

P7 straight-length dose-response: +0.545 [+0.015, +1.075]. Direction correct, and the sign
  NEVER flips across leave-one-circuit-out (0/11, range +0.38..+0.61) — but significance is
  knife-edge: the CI covers zero in 6 of 11 LOO fits. Pre-registration says a positive
  dose-response under a null primary is "interesting but NOT a finding". Holding to that.
P8 SC-duration dose-response: +0.721 [-1.611, +3.053] -> null.

CONCLUSION: no detectable top-speed benefit from a refilled battery at a restart, down to
about +/-2.4 km/h. Either the effect is smaller than that, or top speed on a straight is
the wrong observable for energy state (see the v1 identifiability note: clipping happens
near terminal velocity, where more power raises the terminal SPEED but barely changes
anything we can measure cleanly).

What would move this next, in order of expected value:
 1. A different observable. Top speed is drag-dominated. Better: time from a fixed corner
    exit to a fixed point down the straight (an acceleration measure, not a terminal one),
    using `location` to fix both ends. Much more sensitive to power.
 2. More events: 2026 has 5 races left after Austin.
 3. Relax the pit filter but model tyre age/compound explicitly — would ~3x the sample.
    EXPLORATORY ONLY, and must be labelled as such; it reintroduces the confound the
    primary design exists to remove.

## v4 — acceleration time instead of top speed
New observable: t_accel = seconds from v_lo to v_hi at full throttle (per-circuit bounds),
outcome log(t) with unit FE so it is a proportional, poolable measure.
Rationale: top speed is DRAG-dominated; acceleration is POWER/MASS-dominated.

Validated (3,067 laps): slipstream -6.10% [-7.99,-4.21] p=2.6e-10;
                        fuel burn  -0.221%/lap [-0.323,-0.119] p=2.1e-05.
The fuel effect, which was never cleanly identifiable from top speed, falls straight out.

SC-restart test on this measure: restart -2.10% [-7.47,+3.28] p=0.44 -> NULL.
Precision only +/-5.38% because the pit filter cut 199 driver-events to 71.
STRUCTURAL CONCLUSION: the safety-car restart is a confounded natural experiment BY
CONSTRUCTION — the event that refills the battery is the event that makes everyone pit.
Filtering is honest but leaves too little. This approach is exhausted, not unlucky.

## v5 — within-lap harvest test  (the best-powered null)
Compare different STRAIGHTS OF THE SAME LAP. Fuel, tyres, tyre age, driver, track
evolution identical by construction. Pit stops irrelevant -> no filter -> n = 4,783.
Harvest proxy = kinetic energy dissipated in the run-up, d(v^2).

VALIDATION (strong): slipstream -7.61% [-9.13,-6.09] p=1.0e-22
                     fuel burn  -0.305%/lap [-0.399,-0.211] p=1.8e-10
PRIMARY P12 (harvest -> faster acceleration):
   +0.205% per 1000 (m/s)^2   95% CI [-1.218, +1.628]   p=0.78   -> NULL
   sign flips 7/10 in leave-one-circuit-out. Pure noise.
   Across the IQR of harvest: +0.38% [-2.27, +3.04].

This is the informative null. The instrument resolves a 3% effect (fuel over 10 laps) and
a 4-7% effect (slipstream) at p<1e-10, on the same rows, in the same model. It sees
nothing from harvest variation. Bound: any effect is under ~1.6% per 1000 (m/s)^2.

INTERPRETATION (hypothesis, not established): F1 energy deployment appears to follow a
PRE-COMPUTED per-lap map rather than responding opportunistically to how much was just
harvested. Marginal harvest is absorbed by the battery buffer; it does not change what the
car deploys on the next straight. That is consistent with how teams describe energy
management, and it would explain all five nulls at once.

## FINAL SCOREBOARD (2026-10-19)
POSITIVE, defensible:
  - Tyre degradation: track matters ~2.9x more than compound; "inverted hierarchy"
    overclaims. Fuel coefficient -0.042 s/lap, pre-registered and hit.
  - Slipstream quantified two independent ways: +10.5 km/h on top speed; -6 to -7.6%
    on acceleration time.
  - Fuel burn quantified: -0.22 to -0.31% acceleration time per lap.
  - A validated measurement pipeline: speed trap, acceleration timer, derived gaps,
    all checked against known physics before use.
NULL, battery (5 designs):
  1 clipping shape (flawed design) · 2 Monza VSC (underpowered) · 3 pooled SC top speed
  (+/-2.36 km/h) · 4 pooled SC acceleration (pit filter) · 5 within-lap harvest (best
  powered, bound ~1.6%).

## PACE PROJECT (2026 season) — car pace, driver pace, and what results add on top

Data: 15,125 race laps, all 17 rounds, after removing wet, pit in/out, lap 1,
all SC/VSC laps (2,310), and laps outside 93-106% of the driver's own race median.
Results/teams/standings from Jolpica (374 result rows).

Model: log(lap_time) ~ driver/team + C(circuit) + race_frac + C(compound) + tyre_age
       + log1p(gap_to_car_ahead), clustered by driver x circuit.
Nuisance effects recovered (all correct sign, a free validation):
  fuel, start -> end of race : -3.31%
  tyre age                   : +0.032% per lap
  traffic, per e-fold of gap : -0.214%

CAR PACE (% off the fastest car): Mercedes 0.000, Ferrari +0.081, McLaren +0.365,
  Red Bull +0.490, then a cliff: Alpine +1.690, RB +1.817, Audi +1.833, Haas +2.243,
  Williams +2.569, Aston +3.435, Cadillac +3.961.
  Top 4 reproduce the constructors' championship order exactly.

TEAMMATE GAPS (same car, so this is the driver), % per lap:
  Perez > Bottas 1.115 *  | Verstappen > Hadjar 0.622 * | Gasly > Colapinto 0.459
  Norris > Piastri 0.405  | Antonelli > Russell 0.392 * | Alonso > Stroll 0.218 *
  Lawson > Lindblad 0.210 | Bearman > Ocon 0.143 | Hulkenberg > Bortoleto 0.138
  Sainz > Albon 0.038     | Leclerc > Hamilton 0.017
  (* = 95% CI excludes zero).  Leclerc vs Hamilton is a genuine dead heat.

PACE vs RESULTS — and a big artifact caught:
  Raw "positions gained vs pace rank" put Perez 1st (+2.33) and Bottas 6th (+1.22),
  i.e. the slowest cars looked like the best strategists. That is floor/ceiling:
  pace rank 18 can only move up, pace rank 1 can only move down.
  MEASURED: delta = -1.10 + 0.184 x pace_rank, R2=0.151, p=4.5e-12.
  Ten pace places further back buys +1.84 positions mechanically.
  After correcting, Perez falls to +0.10 (8th) and Bottas to -1.09.
  Of 21 drivers only 2 CIs exclude zero (Verstappen +0.57, Bottas -1.09) — which is
  roughly what 21 tests give you by chance. CONCLUSION: in 2026, race results track
  underlying pace closely; no driver systematically beats their own pace by a margin
  we can detect over a season. Single races differ wildly (Antonelli Silverstone:
  pace rank 1 -> P15), but it does not accumulate.

Caveats: SOFT came out +0.399% SLOWER than MEDIUM, which is backwards for raw grip --
  compound choice is endogenous (when and why a compound is fitted), so that coefficient
  is a control, not an estimate of tyre performance. Lawson appears for two teams
  (mid-season move); handled by fitting teammate models per team.

## IS "GOOD ON TYRES" A REAL DRIVER SKILL?  — NO, not detectably

Design: degradation = d log(lap_time) / d tyre_age, estimated TEAMMATE vs TEAMMATE
(same car, same races), with circuit FE, fuel (race_frac), compound and traffic
controlled, cluster-robust by driver x race.

DRIVER EFFECT: 0 of 11 teams show a clear teammate difference. Smallest p = 0.062
  (Lawson vs Lindblad) — across 11 tests that is exactly what chance gives.
  Ranked gaps, all null: Bottas>Perez .0250 | Lawson>Lindblad .0224 | Bearman>Ocon .0217
  | Leclerc>Hamilton .0165 | Albon>Sainz .0115 | Antonelli>Russell .0096 | ... | Piastri
  >Norris .0004 | Stroll>Alonso .0004
  ACHIEVED BOUND: median CI half-width +/-0.0323%/lap = +/-0.58 s over a 20-lap stint on a
  90 s lap. Typical degradation itself is 0.0375%/lap = 0.68 s per stint. So we could have
  caught a driver losing ~0.6 s more per stint than his teammate. Nobody does.

TEAM (CAR) EFFECT: joint cluster-robust test F=1.89, p=0.045 — only MARGINAL.
  Just 2 of 10 teams (Ferrari, McLaren) differ clearly from the reference (Alpine).
  Descriptive ordering, gentlest to harshest, in seconds lost over a 20-lap stint:
  Williams 0.45 | Alpine 0.51 | Mercedes 0.59 | Aston 0.60 | Audi 0.70 | Haas 0.72 |
  McLaren 0.75 | Red Bull 0.77 | Ferrari 0.80 | RB 0.88 | Cadillac 0.95

### METHOD WARNING — nearly published an artifact
statsmodels' anova_lm uses UNCLUSTERED errors. It reported teams p=0 (F=868) and drivers
p=2e-108 (F=24.9). Both are junk: consecutive laps on one set of tyres are not independent.
Worked example, Antonelli vs Russell, identical coefficient +0.0096%/lap:
    plain OLS  CI [+0.0005,+0.0188]  p=0.040   -> "significant"
    clustered  CI [-0.0150,+0.0343]  p=0.442   -> null
The honest interval is 2.7x wider. Always pass cov_type='cluster'; never trust anova_lm here.

CONCLUSION: tyre-degradation differences are far smaller and noisier than commentary
implies — for cars (marginal) and especially for drivers (undetectable). Rhymes with
project #2: the track dominated the compound there; here the measurement noise dominates
the driver.

## STARTS — who gains places on lap 1?
Position after lap 1 = order of crossing the line to begin lap 2.
Mechanical component measured and removed: gained = -0.98 + 0.125 x grid (R2=0.074).
Corrected leaders: Leclerc +1.16 *, Lawson +1.16 *, Norris +0.97 *, Ocon +0.96, Sainz +0.95
Corrected losers : Bortoleto -2.01 *, Hulkenberg -1.91 *, Bottas -1.60 *, Bearman -0.97
6 of 22 drivers have CIs excluding zero — more than the ~1 chance would give.
BUT split-half repeatability (first half of season vs second) r = +0.118, n=22.
A real skill should repeat. It barely does. Read: there is probably something there, but
it is weak and unstable, not a reliable trait. Treat single-season start rankings with care.

## OVERTAKING UNDER THE 2026 REGS — conversion rate, not raw counts
The public argument (F1 claimed ~3x the overtakes at Australia; The Race called the number
inflated) is about a COUNT, which depends on how much close racing happened. The invariant
measure is: given a car within X seconds, how often does a pass follow by the next lap?
Pit-stop-driven position changes removed (11% of driver-laps: either car changing stint).

  gap to car ahead      pass by next lap
  under 0.5 s           37.8%  (n=1149)
  0.5 - 1.0 s           12.7%  (n=2417)
  1.0 - 1.5 s            8.3%  (n=1691)
  1.5 - 2.0 s            7.7%  (n=1221)
  2.0 - 3.0 s            7.3%  (n=1705)
  3.0 - 5.0 s            5.7%  (n=2119)
  5 - 10 s               4.9%  (n=2649)
  10 - 30 s              2.6%  (n=2334)   <- residual baseline (retirements, penalties)

THE CLIFF IS AT HALF A SECOND: within 0.5 s you convert 37.8%; between 0.5 and 1.0 s only
12.7%. Three times the chance for the same "within a second" that commentary treats as one
category. Season-wide within 1 s: 23.0%. Beyond 3 s: 4.4%.

By circuit, within 1 s: Monza 34.2 | Kuala Lumpur 32.5 | Silverstone 27.6 | Miami 26.6 |
Catalunya 25.8 | Spa 25.2 | Montreal 25.2 | Zandvoort 24.2 | Shanghai 24.0 | Hungaroring
23.6 | Melbourne 22.3 | Spielberg 21.8 | Madring 20.5 | Singapore 18.8 | Suzuka 16.8 |
Baku 16.8 | Monte Carlo 13.1
Face validity: Monza top, Monaco bottom. Baku at 16.8% is the surprise — historically a
big-overtaking circuit; without DRS the long straight no longer seems to be enough.
