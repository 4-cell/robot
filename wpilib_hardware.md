# What Hardware Does WPILib Understand?

WPILib's philosophy: **generic protocol support built directly into `wpilib`**, and
**vendor-specific hardware via separate vendor libraries** — the same pattern seen with
`PWMSparkMax` (generic PWM) vs. `rev.SparkMax` (REV's CAN-specific library).

## Motors (generic, built into `wpilib`)

All PWM-based, following the same pattern as `PWMSparkMax`:

- `PWMSparkMax`, `PWMTalonSRX`, `PWMVictorSPX`, `PWMVictorSP`
- `DMC60` — Digilent DMC 60 Motor Controller
- `Jaguar` — Luminary Micro / Vex Robotics Jaguar Motor Controller with PWM control
- Nidec Brushless Motor support
- `Servo`, `PWMMotorController` (base class)

**CAN-based smart motor controllers** (REV Spark Max/Flex, CTRE Talon FX/SRX/Falcon) are
**not** in core `wpilib` — they require the vendor's own library (`robotpy-rev`,
`robotpy-ctre`/Phoenix). Core `wpilib` does provide a generic `CAN` class — a high-level
class for interfacing with CAN devices conforming to the standard CAN spec — for
low-level custom CAN work, but this isn't what you'd use for standard motor controllers.

## Sensors — built into `wpilib`

**Gyros / IMUs:**
- `ADXRS450_Gyro`, `AnalogGyro` — rate gyro to return the robot's heading relative to a
  starting position
- `ADIS16448_IMU`, `ADIS16470_IMU` (common IMU boards)

**Accelerometers:**
- `BuiltInAccelerometer` — the RoboRIO's own onboard accelerometer
- `ADXL345_I2C`, `ADXL345_SPI`, `ADXL362`, `AnalogAccelerometer`

**Encoders / position sensors:**
- `Encoder` — class to read quadrature encoders
- `AnalogEncoder` — for continuous analog encoders, such as the US Digital MA3
- `AnalogPotentiometer`, `Counter`

**Distance / proximity:**
- `Ultrasonic` — measures absolute distance based on the round-trip time of a ping; a
  common sensor is the Daventech SRF04, which requires a short pulse on a digital channel

**Generic I/O building blocks** (used to wire up many raw sensors yourself):
- `AnalogInput`, `AnalogOutput`, `AnalogTrigger`
- `DigitalInput`, `DigitalOutput`
- `I2C` — I2C bus interface class
- SPI interface (standard core class)

## Vision & AprilTags

These live in separate but official RobotPy packages that install alongside `wpilib`,
not the bare `wpilib` namespace:

- **`CameraServer`** (core `wpilib`) — provides a way to launch an out-of-process
  cscore-based camera service instance, for streaming or for image processing. This is
  how you grab a plain USB webcam feed and stream it to the dashboard.
- **`robotpy-apriltag`** (separate package, `wpilib.apriltag`) — AprilTag detection and
  pose estimation, plus `AprilTagFieldLayout` for known field tag positions (used for
  vision-based localization).
- **Third-party vision coprocessors** — PhotonVision and Limelight are the two dominant
  community tools teams use for AprilTag/vision pipelines. They run on a separate
  coprocessor and talk back to your robot code over NetworkTables, not through a
  `wpilib` hardware class directly. WPILib doesn't ship a driver for these — you install
  their own client library (`photonlibpy` for PhotonVision, or read Limelight's
  NetworkTables entries directly), similar to the REV/CTRE motor vendor libraries.

## Other built-in hardware classes

- `AddressableLED` — for driving addressable LEDs, such as WS2812s and NeoPixels
- `Compressor` — operating a compressor connected to a pneumatics module
- `Solenoid` / `DoubleSolenoid` (pneumatics actuators)
- `PowerDistribution` (PDP/PDH power monitoring)
- `Joystick`, `XboxController`, `PS4Controller` — input from controllers connected to
  the Driver Station
- `Color` / `Color8Bit` — colors usable with Addressable LEDs

## The general pattern to remember

- **Generic electrical protocols** (PWM, analog voltage, digital I/O, I2C, SPI,
  quadrature encoders, standard CAN frame-level access) → built directly into core
  `wpilib`, and work with almost any compliant hardware regardless of brand.
- **Proprietary smart devices** (REV/CTRE CAN motor controllers, PhotonVision/Limelight
  vision coprocessors) → need that vendor's own separate library, which typically builds
  on top of WPILib's common interfaces (like the `MotorController` interface) so they
  still plug into things like `DifferentialDrive` seamlessly.

## Full, always-current class reference

For a complete and version-accurate list rather than the curated summary above, see the
live docs — worth bookmarking since it reflects your exact installed version, given how
often class locations have shifted between seasons in this conversation:

- [wpilib Package — full class reference](https://robotpy.readthedocs.io/projects/wpilib/en/latest/wpilib.html)
