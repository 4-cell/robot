# BREAD Delta RobotPy Software and Hardware Guide

This guide explains the structure of the BREAD5940 Delta FRC robot code, the hardware represented by the code, and how operator inputs become physical robot movement.

## 1. What this project is

This is a command-based RobotPy program for the Delta FRC robot. The main entry point is:

```text
robots/delta-systemcore/robot.py
```

That file creates the robot subsystems, connects the driver and operator controls, runs autonomous and teleoperated behavior, reads sensors, applies motor outputs, and publishes diagnostics.

The software is organized into several layers:

```text
Driver/operator controllers
            |
            v
      ButtonBindings
            |
            v
      Superstructure
   High-level coordination
            |
            v
        Subsystems
  Swerve, intake, shooter, etc.
            |
            v
       Hardware I/O
 Phoenix 6 / PhotonVision / simulation
            |
            v
   Motors, encoders, cameras, LEDs
```

The important design principle is that high-level code usually does not directly command motors. Instead, it requests an action, the superstructure coordinates that request, the subsystem resolves it, and the hardware I/O layer sends the actual motor-controller command.

---

## 2. Technology stack

The robot uses:

- **Python 3.12 or newer**
- **RobotPy / WPILib**
- **Commands2**
- **CTRE Phoenix 6**
- **TalonFX motor controllers**
- **CANcoders**
- **PathPlannerLib**
- **PhotonVision / PhotonLib**
- **NetworkTables**
- **SmartDashboard**

The SystemCore robot configuration uses RobotPy 2027 prerelease packages and Phoenix 6 adapters.

---

## 3. Main repository structure

The relevant robot code is organized approximately like this:

```text
robots/delta-systemcore/
  robot.py                  Main RobotPy lifecycle and object assembly
  constants.py              Hardware IDs, dimensions, limits, gains, and shot tables
  io_selection.py           Real, simulation, fake, and disabled I/O selection
  controls.py               Logical driver/operator controller interface
  button_bindings.py        Controller and dashboard command bindings
  superstructure.py         High-level coordinated robot state machine

  autonomous/                Autonomous selection and path-related code

  subsystems/
    swerve/                  Four-module swerve drivetrain
    intake/                  Intake roller and pivot
    treadmill/               Floor conveyor/indexer
    tunnel/                  Internal game-piece conveyor
    shooter/                 Four-motor shooter
    hood/                    Shooter-angle mechanism
    juicer/                  Position-controlled mechanism
    vision/                  Four-camera pose estimation
    leds/                    Status LEDs

  util/                      Geometry, math, shot, and alliance utilities
```

Most mechanisms follow the same internal pattern:

```text
subsystems/<mechanism>/
  subsystem.py       High-level mechanism states and requests
  io.py              Hardware abstraction and input structures
  phoenix_io.py      Real Phoenix 6 implementation
  sim_io.py          Simulation implementation
  __init__.py        Public exports
```

---

# 4. `robot.py`: the main entry point

The `Robot` class extends:

```python
wpilib.TimedRobot
```

`TimedRobot` provides the standard WPILib lifecycle methods:

- `robotPeriodic`
- `simulationInit`
- `disabledInit`
- `disabledPeriodic`
- `autonomousInit`
- `autonomousExit`
- `teleopInit`
- `teleopPeriodic`

During construction, the robot creates the major subsystems:

```python
self.leds = LEDs(...)
self.swerve = Swerve(...)
self.intake = Intake(...)
self.treadmill = Treadmill(...)
self.shooter = Shooter(...)
self.tunnel = Tunnel(...)
self.hood = Hood(...)
self.juicer = Juicer(...)
```

It then creates the coordinator:

```python
self.superstructure = Superstructure(
    self.swerve,
    self.intake,
    self.treadmill,
    self.tunnel,
    self.shooter,
    self.hood,
    self.juicer,
)
```

The constructor also creates:

- Four-camera vision
- Driver controls
- Operator controls
- Controller button bindings
- SmartDashboard data
- Autonomous selection
- Simulation field visualization

The purpose of `robot.py` is mainly to assemble and schedule the robot. Most individual hardware behavior lives in the subsystem folders.

---

# 5. The main periodic loop

The main control loop is:

```python
def robotPeriodic(self) -> None:
    self.update_mechanism_inputs()
    self.vision.update(self.swerve.get_pose())
    commands2.CommandScheduler.getInstance().run()
    self.process_mechanism_states()
    self.publish_subsystem_telemetry()
    self.publish_status_telemetry()
```

This performs the following sequence.

## Step 1: Read mechanism inputs

```python
self.update_mechanism_inputs()
```

This calls:

```python
self.intake.update_inputs()
self.treadmill.update_inputs()
self.shooter.update_inputs()
self.tunnel.update_inputs()
self.hood.update_inputs()
self.juicer.update_inputs()
```

These methods read values such as:

- Motor position
- Motor velocity
- Motor current
- Encoder position
- Sensor states
- Zeroing status
- Simulation values

## Step 2: Update vision

```python
self.vision.update(self.swerve.get_pose())
```

The vision system processes camera observations and can produce robot-position measurements.

## Step 3: Run the command scheduler

```python
commands2.CommandScheduler.getInstance().run()
```

The command scheduler handles:

- Controller triggers
- Default commands
- `RunCommand`
- `InstantCommand`
- Subsystem periodic methods
- Scheduling and cancellation

The `Superstructure` runs during this phase.

## Step 4: Apply outputs

```python
self.process_mechanism_states()
```

This calls:

```python
self.juicer.process_state()
self.intake.process_state()
self.treadmill.process_state()
self.tunnel.process_state()
self.shooter.process_state()
self.hood.process_state()
```

This is where requested states become actual hardware commands.

For example:

```text
Shooter target = 34 RPS
    -> Shooter.process_state()
    -> PhoenixShooterIO sends velocity request
    -> TalonFX motor controller applies output
    -> Shooter motor spins
```

## Step 5: Publish telemetry

The robot publishes data to SmartDashboard and NetworkTables, including:

- Robot pose
- Current robot mode
- Swerve control mode
- Superstructure state
- Shooter readiness
- Hood readiness
- Camera connectivity
- Mechanism positions
- Real-output gate status

---

# 6. Hardware modes

`io_selection.py` defines four hardware modes:

```python
class IOMode(Enum):
    FAKE = auto()
    SIM = auto()
    REAL = auto()
    DISABLED = auto()
```

## Real mode

On a real robot, the program uses hardware adapters such as:

```text
PhoenixSwerveBackend
PhoenixIntakeIO
PhoenixTreadmillIO
PhoenixShooterIO
PhoenixTunnelIO
PhoenixHoodIO
PhoenixJuicerIO
PhotonVisionIO
PhoenixLEDIO
```

These communicate with physical motor controllers, encoders, cameras, and LEDs.

## Simulation mode

Simulation uses classes such as:

```text
SimSwerveBackend
SimIntakeIO
SimTreadmillIO
SimShooterIO
SimTunnelIO
SimHoodIO
SimJuicerIO
SimVisionIO
```

These imitate hardware without requiring a physical robot.

## Fake mode

Fake I/O is useful for unit tests and hardware-free development.

## Disabled mode

Disabled I/O objects prevent hardware outputs from being sent.

---

# 7. Real hardware safety gates

The code defines:

```python
@dataclass(frozen=True)
class RealOutputConfig:
    swerve: bool = True
    intake: bool = True
    treadmill: bool = True
    tunnel: bool = True
    shooter: bool = True
    hood: bool = True
    juicer: bool = True
    vision: bool = True
    leds: bool = True
```

Each hardware group can be enabled or disabled individually.

For example, if the intake output is disabled, `create_intake_io()` returns a disabled implementation instead of `PhoenixIntakeIO`.

This is useful during hardware bring-up. The team can test one mechanism at a time.

The robot publishes gate statuses such as:

```text
Status/Gate/swerve
Status/Gate/intake
Status/Gate/shooter
Status/Gate/hood
```

Before enabling real outputs, the team should verify the current `REAL_OUTPUTS` configuration and test the robot under supervision.

---

# 8. Hardware represented by the code

## 8.1 Swerve drivetrain

The robot uses a four-module swerve drivetrain.

Each swerve module has:

1. A drive motor
2. A steering motor
3. An absolute steering encoder

The Phoenix backend constructs the drivetrain using:

```python
hardware.TalonFX
hardware.TalonFX
hardware.CANcoder
```

This indicates that the robot uses:

- TalonFX motors/controllers for drive
- TalonFX motors/controllers for steering
- CANcoders for absolute steering-angle feedback

The individual module IDs and offsets are stored in:

```text
tuner_constants.py
```

The chassis constants include:

```text
Wheel radius:       1.94 inches
Track width X:      23.78 inches
Track width Y:      19.78 inches
Maximum speed:      4.39 m/s
Maximum rotation:   11.2 rad/s
```

## 8.2 Intake

The intake uses:

```text
Intake roller motor:       ID 25
Intake follower motor:     ID 26
Intake pivot motor:        ID 27
Intake pivot encoder:      ID 28
```

The intake has two separate functions:

- Rollers collect or eject game pieces.
- A pivot raises, lowers, deploys, and stows the intake.

The intake roller states include:

```text
Stopped
Intaking
Outtaking
```

The pivot has target positions such as:

```text
Stowed
Deployed
Compression position 1
Compression position 2
```

The pivot uses encoder feedback and closed-loop control.

## 8.3 Treadmill/floor conveyor

The treadmill uses:

```text
Leader motor:       ID 31
Follower motor:     ID 32
```

Its configured velocities include:

```text
Idle:       0
Index:      80
Outtake:   -40
Store:       5
```

It moves game pieces from the intake area toward the tunnel.

## 8.4 Shooter

The shooter uses four motors:

```text
Leader:       ID 33
Follower 1:   ID 34
Follower 2:   ID 35
Follower 3:   ID 36
```

The shooter is controlled using target rotational speed in RPS.

The scoring shot table contains approximate values such as:

```text
1.5 meters -> 27 RPS
2.0 meters -> 28 RPS
3.0 meters -> 30.5 RPS
4.0 meters -> 34 RPS
5.0 meters -> 40 RPS
```

The code interpolates between table entries.

The shooter uses closed-loop velocity control. It measures its actual speed and adjusts motor output until it reaches the requested speed.

## 8.5 Tunnel/indexer

The tunnel uses:

```text
Leader motor:       ID 37
Follower motor:     ID 38
```

It is the conveyor stage nearest the shooter.

Its main modes are:

```text
Idle
Feed
Store
Outtake
```

During a shot, the tunnel feeds the game piece into the shooter. During an unjam, it reverses.

## 8.6 Hood

The hood uses:

```text
Hood motor: ID 39
```

It changes the shooter's launch angle.

The hood is zeroed during startup. After zeroing, the superstructure commands an angle based on distance and shot mode.

The hood uses position feedback and closed-loop control.

## 8.7 Juicer

The juicer uses:

```text
Juicer motor: ID 41
```

It is a position-controlled mechanism with positions such as:

```text
Stowed
Raised
Compression
```

The constants also contain left and right climbing poses, suggesting that the juicer is related to climbing or a climbing configuration.

## 8.8 Vision

The robot has four cameras:

```text
FrontRight
RightSide
LeftSide
FrontLeft
```

The camera positions and rotations are defined in `constants.py`.

The cameras use PhotonVision to detect field targets such as AprilTags.

The vision flow is:

```text
Camera detects field tags
    -> PhotonVision estimates pose
    -> Vision validates the observation
    -> Swerve receives a timestamped measurement
    -> Pose estimator combines vision and odometry
```

The code considers:

- Tag distance
- Pose ambiguity
- Field borders
- Single-tag measurements
- Multi-tag measurements

## 8.9 LEDs

The robot uses a Phoenix CANdle:

```text
CANdle device ID: 59
```

The LEDs display information such as:

- Disabled readiness
- Intake position
- Juicer movement
- Other robot status

---

# 9. How the hardware is moved

The general movement sequence is:

```text
Operator input
    -> Controller binding
    -> Superstructure request
    -> Subsystem target/state
    -> Phoenix 6 motor request
    -> Motor controller output
    -> Physical movement
    -> Encoder feedback
    -> Next control-cycle correction
```

Most mechanisms use closed-loop control.

Closed-loop control means the robot does not blindly apply power. Instead:

1. The software requests a target.
2. The motor controller measures the current position or speed.
3. The controller calculates the error.
4. The motor output is adjusted.
5. The process repeats.

---

# 10. How swerve driving works

The driver controls the drivetrain using:

```text
Left stick Y     Forward/backward
Left stick X     Sideways movement
Right stick X    Rotation
```

The code applies a deadband:

```python
deadband(..., 0.05)
```

This prevents small joystick noise from moving the robot.

The values are then converted into chassis velocities:

```python
robot.superstructure.request_driver_swerve_control(
    x * direction * 6.0,
    y * direction * 6.0,
    omega,
    1.0,
    heading_lock_requested,
    shoot_button_pressed,
)
```

## Field-relative driving

Normal driving uses field-relative control.

In field-relative driving, pushing the joystick forward means moving in the field's forward direction regardless of how the robot is rotated.

The Phoenix backend creates:

```python
FieldCentric()
RobotCentric()
```

requests.

## Heading control while shooting

When shooting, the robot can automatically rotate toward a calculated target.

The Phoenix backend creates:

```python
FieldCentricFacingAngle()
```

This request uses heading PID values:

```python
HEADING_KP = 7.0
HEADING_KD = 0.2
```

The superstructure calculates the desired heading toward the scoring or passing target.

When the robot reaches the desired heading, the code may use:

```python
SwerveDriveBrake()
```

The comment in the code identifies this as an X-lock-style hold, where the wheels point inward to help keep the robot stationary.

---

# 11. How the intake moves

The intake roller uses forward and reverse outputs:

```text
Forward -> collect a game piece
Zero duty cycle -> stop
Reverse -> eject a game piece
```

The pivot receives position requests such as:

```python
request_deploy()
request_up()
request_compression(...)
```

The pivot motor uses encoder feedback to move to the requested position.

The code also contains a forward soft limit:

```python
PIVOT_FORWARD_SOFT_LIMIT = 0.31
```

This helps prevent the software from commanding the pivot beyond a safe position.

---

# 12. How the conveyors move

The treadmill and tunnel work as a coordinated system.

## During intake

```text
Intake roller:    Runs forward
Treadmill:        Packs/stores
Tunnel:           Packs/stores
Shooter:          Idle
```

## During outtake

```text
Intake roller:    Runs backward
Treadmill:        Reverses
Tunnel:           Reverses
Shooter:          Idle
```

## During shooting

```text
Treadmill:        Indexes
Tunnel:           Feeds
Shooter:          Spins at target speed
Hood:             Moves to target angle
```

## During unjamming

```text
Treadmill:        Reverses
Tunnel:           Reverses
Shooter:          Idle
Hood:              Idle
```

---

# 13. The superstructure state machine

`superstructure.py` defines the main coordinated states:

```python
class SuperState(Enum):
    STARTING_CONFIG
    IDLE
    PRESHOOT
    SHOOT
    CLIMB
    UNJAM
    TEST
    STATIC_SHOOT
```

## `STARTING_CONFIG`

The hood and juicer are zeroed.

The robot waits for:

```python
self.juicer.is_zeroing_complete()
self.hood.is_zeroing_complete()
```

After both are complete, the robot transitions to `IDLE`.

## `IDLE`

The robot may:

- Intake
- Outtake
- Hold the intake up
- Store a game piece
- Stop all mechanisms

## `PRESHOOT`

The robot prepares for shooting:

- Conveyor mechanisms are controlled to hold the game piece.
- Shooter spins up.
- Hood moves to its target angle.
- Swerve aims toward the target.
- Juicer may move up.
- Readiness checks are performed.

## `SHOOT`

The robot feeds the game piece:

```python
self.treadmill.request_index()
self.tunnel.request_feed()
```

The shooter maintains its target speed and the hood maintains its target angle.

The intake may perform a timed compression or “jiggle” sequence to help position the game piece.

## `CLIMB`

The available code indicates this state idles several mechanisms while the climbing-related hardware is controlled elsewhere or remains under development.

## `UNJAM`

The treadmill and tunnel reverse while the shooter and hood are idled.

## `STATIC_SHOOT`

The robot uses fixed values for known locations:

```text
Tower shot:
  Shooter: 31 RPS
  Hood:    12 degrees

Trench shot:
  Shooter: 33 RPS
  Hood:    13 degrees
```

---

# 14. How a shot is calculated

The superstructure uses the robot's pose, alliance, and location on the field.

It first determines whether the robot is in a scoring zone.

If the robot is in a scoring zone:

```text
Target: Alliance hub
Table:  Scoring shot table
```

Otherwise:

```text
Target: Passing location
Table:  Passing shot table
```

The calculation is performed with:

```python
calculate_shot(
    self.track_target,
    table,
    self._get_shot_state(),
)
```

The resulting shot parameters include:

- Distance to target
- Shooter RPS
- Hood angle
- Desired heading

The robot is ready to shoot only when:

```text
Shooter is at target speed
AND Hood is at target angle
AND Swerve is at target heading
```

This prevents the robot from feeding a game piece before the shot is properly prepared.

---

# 15. Controller structure

`controls.py` defines a common logical controller interface:

```python
class Controls(Protocol):
```

It provides functions such as:

```python
get_left_x()
get_left_y()
get_right_x()
get_right_y()
get_left_trigger()
get_right_trigger()
get_a()
get_b()
get_x()
get_y()
get_left_bumper()
get_right_bumper()
set_rumble(...)
```

There are two controller implementations:

```python
LegacyControls
GamepadControls
```

The active backend is selected by:

```python
CONTROL_BACKEND = ControlBackend.GAMEPAD_2027
```

The robot creates:

```python
self.driver_controls = create_controls(0, ...)
self.operator_controls = create_controls(1, ...)
```

Therefore:

```text
Port 0 -> Driver
Port 1 -> Operator
```

---

# 16. Button bindings

Important driver bindings include:

| Input | Function |
|---|---|
| Left stick | Drive translation |
| Right stick X | Rotate |
| Right trigger | Intake |
| Left trigger | Outtake |
| B | Normal shooting |
| Y | Raise intake |
| Back | Raise juicer |
| X | Lower or idle juicer |
| Right bumper | Static shot |
| Left bumper | Heading lock |

Important operator bindings include:

| Input | Function |
|---|---|
| A | Unjam |
| Right bumper | Starting configuration |

NetworkTables buttons also exist for:

```text
Buttons/Home Hood
Buttons/Home Juicer
Buttons/Starting Config State
Buttons/Unjam Floor and Tunnel
```

These can be controlled from a dashboard.

---

# 17. Autonomous operation

The robot loads a PathPlanner configuration:

```python
self.robot_config = load_robot_config()
```

Then it creates:

```python
self.autonomous_selector = AutonomousSelector(
    self,
    robot_config=self.robot_config,
)
```

During autonomous initialization:

```python
self.autonomous_command = self.get_autonomous_command()

if self.autonomous_command is not None:
    self.autonomous_command.schedule()
```

The autonomous routine runs through the same Commands2 scheduler used for teleoperated behavior.

The robot also:

- Resets the hood
- Resets the juicer
- Sets the superstructure to idle
- Sets autonomous drivetrain behavior
- Changes neutral modes or current limits when supported

---

# 18. Disabled and teleoperated behavior

## Disabled mode

While disabled, the robot publishes a checklist that includes:

- Camera connectivity
- Camera-name mismatch status
- Juicer position
- Hood angle
- Distance from the autonomous start pose
- Pregame selection

If pregame mode is selected, the robot can:

- Reset the swerve pose
- Request a slow drivetrain movement
- Display readiness LEDs

This movement behavior should be treated as supervised because the robot can request drivetrain motion while disabled if the pregame setting is enabled.

## Autonomous mode

Autonomous commands are selected and scheduled.

The robot also resets relevant mechanism states and configures drivetrain behavior.

## Teleoperated mode

When teleop begins:

1. Any autonomous command is canceled.
2. The robot exits startup configuration if zeroing is complete.
3. Trigger inputs are checked.
4. The drivetrain is placed into brake mode.
5. Teleoperated drivetrain settings are requested.
6. The default swerve command reads driver inputs continuously.

---

# 19. Request processing

A key idea in this code is the difference between a request and an output.

For example:

```python
self.intake.request_intake()
```

does not necessarily immediately send voltage to a motor. It records the desired mechanism state.

Later:

```python
self.intake.process_state()
```

examines the requested state and sends the correct hardware command.

The general sequence is:

```text
Read sensors
    -> Calculate desired state
    -> Store subsystem requests
    -> Apply subsystem outputs
```

This approach allows the superstructure to coordinate multiple mechanisms before outputs are applied.

---

# 20. Complete example: pressing the shoot button

When the driver presses B:

1. `ButtonBindings` detects the button.
2. It calls `_start_shooting()`.
3. The superstructure is set to `SuperState.SHOOT`.
4. The command scheduler runs `Superstructure.periodic()`.
5. The superstructure determines scoring or passing mode.
6. It selects a target.
7. It calculates shooter speed, hood angle, and desired heading.
8. The robot enters `PRESHOOT`.
9. The shooter spins up.
10. The hood moves to its calculated angle.
11. The swerve drivetrain turns toward the target.
12. The robot checks shooter, hood, and heading readiness.
13. Once ready, the robot enters `SHOOT`.
14. The treadmill indexes.
15. The tunnel feeds.
16. The shooter and hood maintain their targets.
17. The intake may perform a compression sequence.
18. The subsystem `process_state()` methods send hardware commands.
19. Sensor feedback is read on the next periodic cycle.
20. When B is released, the robot returns to `IDLE`.

---

# 21. Recommended reading order

For a new team member, read the code in this order:

1. `robots/delta-systemcore/robot.py`
2. `robots/delta-systemcore/button_bindings.py`
3. `robots/delta-systemcore/superstructure.py`
4. `robots/delta-systemcore/constants.py`
5. `robots/delta-systemcore/io_selection.py`
6. `robots/delta-systemcore/subsystems/swerve/subsystem.py`
7. `robots/delta-systemcore/subsystems/swerve/phoenix_backend.py`
8. One mechanism from end to end, such as:
   - `subsystems/intake/subsystem.py`
   - `subsystems/intake/io.py`
   - `subsystems/intake/phoenix_io.py`
   - `subsystems/intake/sim_io.py`
9. Repeat the same pattern for:
   - Shooter
   - Hood
   - Treadmill
   - Tunnel
   - Juicer
   - Vision

---

# 22. Summary

The Delta robot has:

- A four-module swerve drivetrain
- An intake
- A treadmill/floor conveyor
- A tunnel/indexer
- A four-motor shooter
- An adjustable hood
- A juicer or climbing-related mechanism
- Four vision cameras
- Phoenix CANdle status LEDs

The code is layered:

```text
Controllers
    -> ButtonBindings
    -> Superstructure
    -> Subsystems
    -> Hardware I/O
    -> Physical robot
```

The `Superstructure` coordinates mechanisms so that actions such as shooting are synchronized. Subsystems manage their own states and targets. Phoenix 6 adapters communicate with real motor controllers and sensors. Simulation and fake I/O implementations allow much of the same robot logic to run without physical hardware.