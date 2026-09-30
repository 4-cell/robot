https://github.com/BREAD5940/robot-code/blob/crumbs/robots/delta-systemcore/subsystems/intake/subsystem.py
 
# Bread Intaker: What This Subsystem Does

This intake subsystem controls the robot's intake mechanism, which is used to collect and eject game objects.

The subsystem controls two main mechanisms:

- **Roller motor:** Pulls game objects in or pushes them out.
- **Pivot motor:** Moves the intake to different positions, such as deployed, stowed, compressed, or raised.

The file is:

`robots/delta-systemcore/subsystems/intake/subsystem.py`

The subsystem does not directly control motor controllers or sensors. Instead, it communicates with an `IntakeIO` object, which provides the hardware interface.

---

## Intake States

The subsystem uses the `IntakeState` enum to represent the desired intake behavior:

```python
class IntakeState(Enum):
    STOWED = auto()
    INTAKING = auto()
    OUTTAKING = auto()
    COMPRESS = auto()
    IDLE = auto()
    DEPLOY = auto()
    UP = auto()
```

The states mean:

| State | Roller | Pivot |
|---|---|---|
| `STOWED` | Stopped | Target is set to the stowed position |
| `IDLE` | Stopped | Moves to the deployed position |
| `INTAKING` | Spins inward | Moves to the deployed position |
| `OUTTAKING` | Spins outward | Moves to the deployed position |
| `COMPRESS` | Spins inward | Moves to a custom position |
| `DEPLOY` | Stopped | Moves to the deployed position |
| `UP` | Stopped | Moves to the up position |

The numeric positions and duty cycles are provided by `IntakeConstants`.

---

## How Requests Work

The subsystem has request methods such as:

```python
intake.request_intake()
intake.request_outtake()
intake.request_deploy()
intake.request_up()
intake.request_idle()
```

These methods do not immediately command the motors. They only update the desired state.

For example:

```python
def request_intake(self) -> None:
    self._state = IntakeState.INTAKING
```

This changes the internal state to `INTAKING`.

The motor outputs are applied later when:

```python
intake.process_state()
```

is called.

This creates a separation between:

1. Requesting behavior.
2. Processing the requested state.
3. Sending commands to the hardware.

---

## What `process_state()` Does

`process_state()` converts the current intake state into actual motor commands.

It controls:

- The roller duty cycle.
- The pivot target position.
- The commands sent through `IntakeIO`.

The method checks `self._state` and executes the matching branch.

---

## `STOWED`

```python
if self._state is IntakeState.STOWED:
    self._target_roller_duty_cycle = IntakeConstants.STOPPED_DUTY_CYCLE
    self._io.set_duty_cycle(self._target_roller_duty_cycle)
    self._pivot_target_rotations = IntakeConstants.STOWED_POSITION_ROTATIONS
```

This state:

- Stops the roller.
- Changes the stored pivot target to the stowed position.

Important detail: this branch does not call `self._io.set_position(...)`.

Therefore, it stores the stowed target internally, but it does not directly send a pivot position command in this branch. This may be intentional, or it may be something that should be reviewed if the pivot is expected to physically move to the stowed position.

---

## `IDLE`

```python
elif self._state is IntakeState.IDLE:
    self._target_roller_duty_cycle = IntakeConstants.STOPPED_DUTY_CYCLE
    self._io.set_duty_cycle(self._target_roller_duty_cycle)
    self._pivot_target_rotations = IntakeConstants.DEPLOYED_POSITION_ROTATIONS
    self._io.set_position(self._pivot_target_rotations)
```

This state:

- Stops the roller.
- Commands the pivot to the deployed position.

---

## `INTAKING`

```python
elif self._state is IntakeState.INTAKING:
    self._target_roller_duty_cycle = IntakeConstants.INTAKING_DUTY_CYCLE
    self._io.set_duty_cycle(self._target_roller_duty_cycle)
    self._pivot_target_rotations = IntakeConstants.DEPLOYED_POSITION_ROTATIONS
    self._io.set_position(self._pivot_target_rotations)
```

This state:

- Spins the roller inward.
- Moves the pivot to the deployed position.

The roller duty cycle is taken from:

```python
IntakeConstants.INTAKING_DUTY_CYCLE
```

---

## `COMPRESS`

```python
elif self._state is IntakeState.COMPRESS:
    self._io.set_position(self._pivot_target_rotations)
    self._target_roller_duty_cycle = IntakeConstants.INTAKING_DUTY_CYCLE
    self._io.set_duty_cycle(self._target_roller_duty_cycle)
```

This state:

- Moves the pivot to a custom target.
- Runs the roller inward.

The custom target is set by:

```python
intake.request_compression(rotations)
```

That method stores the requested position:

```python
def request_compression(self, rotations: float) -> None:
    self._pivot_target_rotations = rotations
    self._state = IntakeState.COMPRESS
```

---

## `OUTTAKING`

```python
elif self._state is IntakeState.OUTTAKING:
    self._target_roller_duty_cycle = IntakeConstants.OUTTAKING_DUTY_CYCLE
    self._io.set_duty_cycle(self._target_roller_duty_cycle)
    self._pivot_target_rotations = IntakeConstants.DEPLOYED_POSITION_ROTATIONS
    self._io.set_position(self._pivot_target_rotations)
```

This state:

- Spins the roller in the outward direction.
- Moves the pivot to the deployed position.

The roller duty cycle is taken from:

```python
IntakeConstants.OUTTAKING_DUTY_CYCLE
```

---

## `DEPLOY`

```python
elif self._state is IntakeState.DEPLOY:
    self._pivot_target_rotations = IntakeConstants.DEPLOYED_POSITION_ROTATIONS
    self._io.set_position(self._pivot_target_rotations)
    self._target_roller_duty_cycle = IntakeConstants.STOPPED_DUTY_CYCLE
    self._io.set_duty_cycle(self._target_roller_duty_cycle)
```

This state:

- Moves the pivot to the deployed position.
- Stops the roller.

---

## `UP`

```python
elif self._state is IntakeState.UP:
    self._target_roller_duty_cycle = IntakeConstants.STOPPED_DUTY_CYCLE
    self._io.set_duty_cycle(self._target_roller_duty_cycle)
    self._pivot_target_rotations = IntakeConstants.UP_POSITION_ROTATIONS
    self._io.set_position(self._pivot_target_rotations)
```

This state:

- Stops the roller.
- Moves the pivot to the up position.

---

# How the Intake Interacts With Sensors

Sensor and motor telemetry is stored in an `IntakeIOInputs` object.

The input data includes:

```python
@dataclass
class IntakeIOInputs:
    roller_rps: float = 0.0
    roller_volts: float = 0.0
    roller_amps: float = 0.0
    pivot_position: float = 0.0
    pivot_volts: float = 0.0
    pivot_amps: float = 0.0
```

These values represent:

| Input | Meaning |
|---|---|
| `roller_rps` | Roller speed in revolutions per second |
| `roller_volts` | Voltage applied to the roller motor |
| `roller_amps` | Current drawn by the roller motor |
| `pivot_position` | Current pivot encoder position in rotations |
| `pivot_volts` | Voltage applied to the pivot motor |
| `pivot_amps` | Current drawn by the pivot motor |

The subsystem updates these values with:

```python
def update_inputs(self) -> None:
    self._io.update_inputs(self.inputs)
```

The `IntakeIO` object reads the real hardware and copies the values into `self.inputs`.

The subsystem provides methods for reading those values:

```python
def get_roller_rps(self) -> float:
    return self.inputs.roller_rps

def get_roller_current(self) -> float:
    return self.inputs.roller_amps

def get_pivot_position(self) -> float:
    return self.inputs.pivot_position

def get_pivot_current(self) -> float:
    return self.inputs.pivot_amps
```

For example:

```python
roller_speed = intake.get_roller_rps()
roller_current = intake.get_roller_current()
pivot_position = intake.get_pivot_position()
```

This file does not include a dedicated game-object sensor such as a beam break or proximity sensor. If the robot detects an object, it may do so using another subsystem or by analyzing values such as roller current and speed.

For example, a high roller current may indicate that the roller is stalled or is pressing against a game object.

---

# How the Intake Interacts With Motors

The subsystem does not directly access motor-controller objects.

Instead, it uses the `IntakeIO` interface:

```python
self._io.set_duty_cycle(...)
self._io.set_position(...)
```

The subsystem decides what should happen, and `IntakeIO` handles how the hardware is commanded.

## Roller motor

The roller is controlled with:

```python
self._io.set_duty_cycle(duty_cycle)
```

The duty cycle comes from constants such as:

```python
IntakeConstants.STOPPED_DUTY_CYCLE
IntakeConstants.INTAKING_DUTY_CYCLE
IntakeConstants.OUTTAKING_DUTY_CYCLE
```

A positive or negative value may represent different roller directions, depending on how the constants are defined.

## Pivot motor

The pivot is controlled with:

```python
self._io.set_position(position_rotations)
```

The position is specified in rotations.

The target values come from constants such as:

```python
IntakeConstants.STOWED_POSITION_ROTATIONS
IntakeConstants.DEPLOYED_POSITION_ROTATIONS
IntakeConstants.UP_POSITION_ROTATIONS
```

The actual pivot motor controller or position-control system is implemented by the concrete `IntakeIO` class.

---

# What `IntakeIO` Is

`IntakeIO` is a Python `Protocol` defined in:

`robots/delta-systemcore/subsystems/intake/io.py`

It defines the interface that any intake hardware implementation must provide.

```python
class IntakeIO(Protocol):
    def update_inputs(self, inputs: IntakeIOInputs) -> None: ...

    def set_duty_cycle(self, duty_cycle: float) -> None: ...

    def set_position(self, position_rotations: float) -> None: ...

    def set_voltage(self, volts: float) -> None: ...

    def get_position(self) -> float: ...
```

A protocol is a contract. Any object passed to the `Intake` constructor should provide these methods.

The `Intake` class receives an `IntakeIO` object here:

```python
def __init__(self, io: IntakeIO) -> None:
    super().__init__()
    self._io = io
```

This is called dependency injection. The subsystem does not create its own hardware object. Instead, another part of the robot creates the correct IO implementation and passes it into the subsystem.

---

# `IntakeIO` Methods

## `update_inputs`

```python
def update_inputs(self, inputs: IntakeIOInputs) -> None:
    ...
```

This method reads sensors and motor telemetry from the hardware and writes the values into `inputs`.

A real implementation might conceptually do this:

```python
def update_inputs(self, inputs: IntakeIOInputs) -> None:
    inputs.roller_rps = self.roller_motor.get_velocity()
    inputs.roller_volts = self.roller_motor.get_voltage()
    inputs.roller_amps = self.roller_motor.get_current()

    inputs.pivot_position = self.pivot_motor.get_position()
    inputs.pivot_volts = self.pivot_motor.get_voltage()
    inputs.pivot_amps = self.pivot_motor.get_current()
```

The exact code depends on the motor controllers and sensors used by the robot.

---

## `set_duty_cycle`

```python
def set_duty_cycle(self, duty_cycle: float) -> None:
    ...
```

This method sends a duty-cycle command to the roller motor.

The intake subsystem calls it when it needs to:

- stop the roller
- intake an object
- outtake an object

---

## `set_position`

```python
def set_position(self, position_rotations: float) -> None:
    ...
```

This method commands the pivot motor to move to a target position.

The position is expressed in rotations.

The implementation may use a motor controller's built-in position-control mode.

---

## `set_voltage`

```python
def set_voltage(self, volts: float) -> None:
    ...
```

This method allows the hardware implementation to accept a voltage command.

The current `Intake` subsystem does not call this method, but it is part of the interface and may be useful for characterization, testing, or another control mode.

---

## `get_position`

```python
def get_position(self) -> float:
    ...
```

This method returns the current pivot position.

The current `Intake` subsystem reads pivot position through `self.inputs.pivot_position`, but this method provides another direct way to access the position.

---

# Example Real Hardware Implementation

A real implementation could look conceptually like this:

```python
class RealIntakeIO:
    def __init__(self) -> None:
        self.roller_motor = ...
        self.pivot_motor = ...

    def update_inputs(self, inputs: IntakeIOInputs) -> None:
        inputs.roller_rps = self.roller_motor.get_velocity()
        inputs.roller_volts = self.roller_motor.get_voltage()
        inputs.roller_amps = self.roller_motor.get_current()

        inputs.pivot_position = self.pivot_motor.get_position()
        inputs.pivot_volts = self.pivot_motor.get_voltage()
        inputs.pivot_amps = self.pivot_motor.get_current()

    def set_duty_cycle(self, duty_cycle: float) -> None:
        self.roller_motor.set(duty_cycle)

    def set_position(self, position_rotations: float) -> None:
        self.pivot_motor.set_position(position_rotations)

    def set_voltage(self, volts: float) -> None:
        self.roller_motor.set_voltage(volts)

    def get_position(self) -> float:
        return self.pivot_motor.get_position()
```

The exact motor-controller calls will depend on the hardware library being used.

The subsystem would then be constructed with the hardware implementation:

```python
intake = Intake(RealIntakeIO())
```

---

# `FakeIntakeIO`

The repository also contains `FakeIntakeIO`, which is useful for tests.

It does not control real motors. Instead, it:

- stores simulated input values
- records requested commands
- allows tests to verify subsystem behavior

Example:

```python
io = FakeIntakeIO()
intake = Intake(io)

intake.request_intake()
intake.process_state()
```

The fake IO records calls such as:

```python
[
    ("duty_cycle", IntakeConstants.INTAKING_DUTY_CYCLE),
    ("position", IntakeConstants.DEPLOYED_POSITION_ROTATIONS),
]
```

This makes it possible to check whether the subsystem sent the correct commands.

Simulated sensor readings can also be set:

```python
io.inputs.roller_amps = 18.0
io.inputs.roller_rps = 20.0
io.inputs.pivot_position = 3.5

intake.update_inputs()
```

The subsystem can then read them:

```python
current = intake.get_roller_current()
speed = intake.get_roller_rps()
position = intake.get_pivot_position()
```

---

# `DisabledIntakeIO`

`DisabledIntakeIO` is a safe no-op implementation.

It accepts intake commands but does not send them to real motors. Instead, it records suppressed requests in:

```python
suppressed_requests
```

This is useful when:

- the intake hardware is not installed
- the robot is being tested safely
- motor output must be disabled
- the software is running without hardware libraries
- the robot is in a hardware bring-up mode

---

# Telemetry

The subsystem publishes data to the WPILib SmartDashboard with:

```python
intake.publish_telemetry()
```

The published values include:

- current roller speed
- roller current
- roller voltage
- current pivot position
- pivot current
- pivot voltage
- target pivot position
- target roller duty cycle
- current intake state
- last recorded IO request

Examples of dashboard keys include:

```text
Subsystems/Intake/RollerRps
Subsystems/Intake/RollerAmps
Subsystems/Intake/RollerVolts
Subsystems/Intake/PivotPositionRotations
Subsystems/Intake/PivotAmps
Subsystems/Intake/PivotVolts
Subsystems/Intake/TargetPivotRotations
Subsystems/Intake/TargetRollerDutyCycle
Subsystems/Intake/State
Subsystems/Intake/LastRequest
```

This lets developers and drivers inspect what the subsystem believes is happening.

---

# Typical Periodic Usage

A robot loop may use the subsystem like this:

```python
def periodic(self) -> None:
    intake.update_inputs()
    intake.process_state()
    intake.publish_telemetry()
```

A command might request a behavior:

```python
def execute(self) -> None:
    intake.request_intake()
```

The periodic loop then processes that request and sends the corresponding commands to the hardware.

The general flow is:

```text
Robot command
    |
    v
intake.request_intake()
    |
    v
Intake state becomes INTAKING
    |
    v
intake.process_state()
    |
    v
IntakeIO.set_duty_cycle(...)
IntakeIO.set_position(...)
    |
    v
Actual motor controllers
```

Sensor data flows in the opposite direction:

```text
Motor controllers and encoders
    |
    v
IntakeIO.update_inputs(...)
    |
    v
IntakeIOInputs
    |
    v
Intake.get_roller_current()
Intake.get_pivot_position()
Intake.get_roller_rps()
```

---

# Summary

The intake subsystem is a high-level controller for the robot's intake mechanism.

It:

- tracks the requested intake state
- controls the roller motor
- controls the pivot motor
- reads motor and encoder telemetry
- publishes diagnostic information
- supports real, fake, and disabled hardware implementations

`process_state()` is the method that translates the requested state into actual motor commands.

`IntakeIO` is the hardware abstraction layer. It defines how the subsystem:

- reads sensor data
- commands roller duty cycle
- commands pivot position
- optionally applies voltage
- reads pivot position directly

The overall design is:

```text
High-level request
    -> Intake state
    -> process_state()
    -> IntakeIO
    -> Motors
```

and:

```text
Sensors and motor controllers
    -> IntakeIO
    -> IntakeIOInputs
    -> Intake subsystem telemetry
```

This separation keeps the intake behavior easy to test and allows the same subsystem logic to work with real hardware, fake hardware, or disabled hardware.



 # Question

The intaker has two motors: one for deploying the intaker and the other for the roller that sucks in balls. When `self._state` is `IntakeState.INTAKING`, it should control the roller motor, but when `self._state` is `IntakeState.DEPLOY`, it should control the other motor. I only see `self._io.set_position` and `self._io.set_duty_cycle`. How do calling these two functions control different motors at the appropriate time?

# Answer

`self._io.set_position()` and `self._io.set_duty_cycle()` are intended to control different motors through the concrete implementation of `IntakeIO`:

- `set_position(...)` controls the pivot/deployment motor.
- `set_duty_cycle(...)` controls the intake roller motor.

The IO interface defines these commands separately:

```Python
class IntakeIO(Protocol):
    def update_inputs(self, inputs: IntakeIOInputs) -> None: ...
    def set_duty_cycle(self, duty_cycle: float) -> None: ...
    def set_position(self, position_rotations: float) -> None: ...
```

The telemetry fields also indicate the intended motor separation:

```Python
class IntakeIOInputs:
    roller_rps: float = 0.0
    roller_volts: float = 0.0
    roller_amps: float = 0.0
    pivot_position: float = 0.0
    pivot_volts: float = 0.0
    pivot_amps: float = 0.0
```

Therefore, when the state is INTAKING:

```Python
elif self._state is IntakeState.INTAKING:
    self._target_roller_duty_cycle = IntakeConstants.INTAKING_DUTY_CYCLE
    self._io.set_duty_cycle(self._target_roller_duty_cycle)
    self._pivot_target_rotations = IntakeConstants.DEPLOYED_POSITION_ROTATIONS
    self._io.set_position(self._pivot_target_rotations)
```

The calls are intended to work like this:
set_duty_cycle(intaking duty cycle)  -> roller motor runs
set_position(deployed rotations)     -> pivot motor moves or stays deployed

When the state is DEPLOY:

```Python
elif self._state is IntakeState.DEPLOY:
    self._pivot_target_rotations = IntakeConstants.DEPLOYED_POSITION_ROTATIONS
    self._io.set_position(self._pivot_target_rotations)
    self._target_roller_duty_cycle = IntakeConstants.STOPPED_DUTY_CYCLE
    self._io.set_duty_cycle(self._target_roller_duty_cycle)
```

The intended behavior is:
set_position(deployed rotations) -> deployment/pivot motor moves the intake
set_duty_cycle(0)                -> roller motor is stopped

The Intake subsystem itself does not directly know about motor controller objects. It communicates through the IntakeIO abstraction. The concrete hardware implementation must map each method to the correct motor, conceptually like this:

```Python
def set_duty_cycle(self, duty_cycle: float) -> None:
    self.roller_motor.set(duty_cycle)

def set_position(self, position_rotations: float) -> None:
    self.pivot_motor.set_position(position_rotations)
```

So the architecture is:

```text
IntakeState.INTAKING
    ├── set_duty_cycle(...) -> roller motor
    └── set_position(...)    -> pivot/deployment motor

IntakeState.DEPLOY
    ├── set_position(...)    -> pivot/deployment motor
    └── set_duty_cycle(0)    -> roller motor stopped
```

The important caveat is that subsystem.py only defines the requested behavior. It does not prove how the motors are electrically controlled. The concrete class implementing IntakeIO must connect set_duty_cycle() to the roller motor and set_position() to the pivot motor. That hardware implementation is the next file to inspect.
