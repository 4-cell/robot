# Delta Superstructure Summary

File analyzed: `robots/delta-systemcore/superstructure.py`

## 1. How the subsystems are orchestrated

`Superstructure` is a coordination layer for the Delta robot. It does not directly control motors; instead, it sends requests to the individual subsystems:

- Swerve
- Intake
- Treadmill/floor conveyor
- Tunnel
- Shooter
- Hood
- Juicer

The main control loop is `update()`, called by `periodic()` under the command scheduler:

1. Read the robot pose from Swerve.
2. Determine whether the robot is in a scoring zone or a passing zone.
3. Select the appropriate target:
   - Alliance hub for scoring.
   - Near or far pass target for passing.
4. Calculate shooter speed, hood angle, distance, and desired heading.
5. Resolve the requested state into the current state.
6. Apply mechanism requests for that state.
7. Publish readiness and targeting telemetry.

The architecture is request-based. For example, this class calls methods such as:

- `shooter.set_target_rps(...)`
- `hood.set_target_angle(...)`
- `tunnel.request_feed()`
- `treadmill.request_index()`
- `intake.request_compression(...)`

The individual subsystems are responsible for closed-loop control and hardware output.

### Normal operating examples

#### Idle and intake handling

- If the intake is commanded up, the intake moves up and the conveyors remain idle.
- While intaking, the tunnel packs material and the treadmill packs unless the tunnel is backing off.
- While outtaking, the intake, treadmill, and tunnel run in reverse.
- Otherwise, the intake deploys and the other mechanisms remain idle.

#### Preshooting

During `PRESHOOT`:

- The treadmill and tunnel outtake to clear or stage balls.
- The juicer can be raised when forced by the shooting request.
- After a short spin-back delay, the shooter and hood receive their calculated targets.

#### Shooting

During `SHOOT`:

- The treadmill indexes.
- The tunnel feeds.
- The shooter maintains the calculated RPS target.
- The hood maintains the calculated angle.
- The intake performs an automatic compression/jiggle sequence.
- The shooter receives a temporary boost during the first second of shooting.

#### Static shooting

During `STATIC_SHOOT`, fixed settings are used instead of the dynamically calculated shot table:

- Tower shot: 31 RPS and 12 degrees.
- Trench shot: 33 RPS and 13 degrees.

Feeding starts after the shooter reaches its target tolerance. The trench shot raises the juicer; the tower shot uses normal compression behavior.

#### Climbing

During `CLIMB`, the intake, hood, shooter, treadmill, and tunnel are commanded idle.

## 2. Handling unexpected events

This file handles normal control uncertainty through readiness checks, state rollback, timers, and safe mechanism requests. It does not implement full obstacle detection or localization recovery.

### Obstacles or enemy robots in the path

There is no direct obstacle or enemy-robot detection in this class. It does not perform:

- Vision-based obstacle detection.
- Collision classification.
- Path replanning.
- Automatic driving around another robot.
- Automatic stopping because an obstacle was detected.

Those responsibilities would need to be implemented in Swerve, driver-control, autonomous, or higher-level navigation code.

The closest related behavior is the shooting drive logic:

- Scoring normally stops translation while the robot snaps to the target heading.
- Passing can allow translation.
- Translation is limited during applicable shooting modes to `SwerveConstants.SHOOT_MAX_TRANSLATION_MPS`.

### Enemy robot bumps the robot during shooting

The robot checks whether it is still aimed correctly. If it is already in `SHOOT` and loses its heading, it stops the shooting boost and normally returns to `PRESHOOT`:

```text
SHOOT -> PRESHOOT
```

It must become ready again before returning to `SHOOT`.

For normal scoring, shooting readiness requires:

- Shooter speed within tolerance.
- Hood angle within tolerance.
- Heading within tolerance.
- Heading lock acquired where required.

Shoot-on-the-move is more tolerant: the robot may remain in `SHOOT` while Swerve tracks the target heading and translation is limited. Passing also uses wider and asymmetric heading tolerances.

There is no explicit collision sensor or bump response in this file.

### Robot loses its current position

The pose is read from `swerve.get_pose()`. If the pose is `None`, `_pose_value()` falls back to `(0, 0)`. This is only a data fallback; it is not localization recovery.

There is no explicit handling for:

- Odometry reset.
- Vision-based localization recovery.
- Pose confidence.
- Invalid-pose detection.
- Reacquiring field position.
- Automatically stopping because localization is unreliable.

If the pose is wrong, the superstructure can select the wrong scoring/pass zone and calculate incorrect targeting, shooter, hood, and heading values.

Another component can call `set_suspended(True)`. While suspended, the class still updates pose and shot calculations, but it does not resolve transitions or issue mechanism requests.

### Shooter or hood is not ready

The robot does not normally enter `SHOOT` until the shooter, hood, and heading are ready. Scoring and passing use different tolerances:

- Scoring: 1 RPS and 1 degree.
- Passing: 2 RPS and 2 degrees.

If the robot is not ready before shooting, it remains in `PRESHOOT`. Heading loss while already shooting is explicitly handled and can return the robot to `PRESHOOT`. Shooter or hood readiness loss during `SHOOT` is not handled with the same explicit state rollback in every mode; the mechanisms continue receiving their targets.

### Mechanism jams

There is an explicit `UNJAM` state:

- Hood idle.
- Shooter idle.
- Treadmill outtake.
- Tunnel outtake.

However, automatic jam detection is not implemented here. `set_auto_unjam_enabled()` only stores a flag. It does not automatically transition to `UNJAM`; another command or subsystem must request that state.

### Juicer after shooting

`solve_juicer_post_shooting_state()` checks the juicer position:

- Above 25 rotations: raise the juicer and trigger a rumble notification.
- Otherwise: keep the juicer idle.

The rumble flag is cleared after the juicer reaches near its upper position.

## 3. State machine

The defined states are:

```text
STARTING_CONFIG
IDLE
PRESHOOT
SHOOT
CLIMB
UNJAM
TEST
STATIC_SHOOT
```

The class tracks both:

- `_wanted_state`: the state requested by external commands.
- `_current_state`: the state currently being executed.

This allows a request such as:

```text
Wanted state: SHOOT
Current state: PRESHOOT
```

The robot has been asked to shoot but is still preparing.

### `STARTING_CONFIG`

The initial state. The juicer and hood are commanded to zero. The state changes to `IDLE` only when both report zeroing complete:

```text
STARTING_CONFIG --zeroing complete--> IDLE
```

### `IDLE`

The normal non-shooting state. It manages intake deployment, storage, packing, outtaking, and idle behavior.

The transition to other states is generally command-driven through `set_wanted_state()`.

### `PRESHOOT`

The aiming and preparation state. The robot stages the feed path, starts shooter spin-up after a delay, sets the hood target, and waits for readiness.

Typical transition:

```text
IDLE --shoot requested but not ready--> PRESHOOT
```

### `SHOOT`

The active feed state. The robot indexes and feeds while maintaining shooter and hood targets.

Typical transition:

```text
PRESHOOT --ready--> SHOOT
```

If the robot loses heading during ordinary shooting:

```text
SHOOT --heading lost--> PRESHOOT
```

Shoot-on-the-move can keep the robot in `SHOOT` while it tracks the desired heading.

### `CLIMB`

An externally commanded state that idles most mechanisms:

```text
any state --external command--> CLIMB
```

There is no automatic climb detection in this class.

### `UNJAM`

An externally commanded recovery state that reverses the feed path:

```text
any state --external command--> UNJAM
```

Automatic jam-triggered transition is not implemented here.

### `TEST`

A no-op state. Its handler intentionally performs no actions:

```python
SuperState.TEST: lambda: None
```

### `STATIC_SHOOT`

A fixed-parameter shooting state for tower or trench shots. It continuously commands fixed shooter and hood targets and starts feeding once the shooter reaches its tolerance.

## 4. Important transition behavior

### `PRESHOOT` is normalized to `SHOOT`

If external code requests `PRESHOOT`, `set_wanted_state()` converts it to `SHOOT`. The internal state resolver then chooses whether the current state should be `PRESHOOT` or `SHOOT` based on readiness.

### Leaving shooting resets shooting state

When leaving `PRESHOOT` or `SHOOT`, the class resets:

- Heading lock.
- Spin-back timer.
- Compression timer.
- Shooter boost timer.
- Jiggle phase.
- Forced juicer-up flag.
- Automatic shoot-on-the-move flags.

### Most transitions are command-driven

Only a small number of transitions are automatic:

1. `STARTING_CONFIG -> IDLE` after zeroing.
2. Shooting request -> `PRESHOOT` while not ready.
3. `PRESHOOT -> SHOOT` after readiness.
4. `SHOOT -> PRESHOOT` when heading is lost in normal shooting.

Transitions to `CLIMB`, `UNJAM`, `TEST`, and `STATIC_SHOOT` require external state requests.

## 5. Scoring and passing target selection

The robot decides whether it is scoring or passing from its alliance-relative X position.

### Scoring mode

Inside the scoring zone:

- The target is the alliance hub.
- The shooting table is used.
- The robot aims at the hub.
- Translation is normally stopped while aiming.
- Heading lock is required before shooting.

### Passing mode

Outside the scoring zone:

- A near or far pass target is selected.
- The pass table is used.
- Translation can be allowed.
- Heading tolerances are wider.
- Heading adjustment can be biased toward or away from the field center.

The selected pass target depends on:

- Alliance.
- Robot X position.
- Robot Y side of the field.
- Whether the robot is past the pass-line threshold.

## 6. Overall assessment

This file is strong at coordinating normal mechanism behavior and handling ordinary timing and aiming uncertainty. It provides:

- Clear wanted-state/current-state separation.
- Readiness-based shooting transitions.
- Heading-loss recovery during shooting.
- Shoot-on-the-move support.
- Translation limiting.
- Explicit unjam and suspended modes.
- Timed shooter spin-up, compression, and boost behavior.
- Telemetry for diagnosing targeting and readiness.

It does not itself provide advanced recovery for:

- Obstacles.
- Enemy-robot collisions.
- Path replanning.
- Localization confidence or recovery.
- Automatic jam detection.
- Comprehensive abort behavior for every possible shooter or hood failure during shooting.

Those features would need to be implemented in Swerve, localization, command, autonomous, or higher-level robot-control code.
