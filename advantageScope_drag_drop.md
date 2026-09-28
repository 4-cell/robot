# AdvantageScope FRC Simulation & Telemetry Integration Notes

## 💡 The Problem Summary
When attempting to track a robot's simulated position on the AdvantageScope 2D field layout, dragging the native `Field2d` object folder or raw double arrays (`double[]`) directly into the **Poses** panel failed to register or render the robot icon. 

### Why the Initial Drag-and-Drop Failed
1. **Structural Mismatch:** `Field2d` publishes coordinates as a sub-table (a folder containing sub-elements named `0`, `1`, `2`). AdvantageScope treats this as a generic folder hierarchy and cannot guarantee the data schema, rejecting the drag action.
2. **Missing Type Context:** A raw array (e.g., `[X, Y, Rotation]`) provides loose floating-point data without metadata. AdvantageScope blocks the drop because it cannot distinguish it from non-spatial datasets (like PID configurations or velocity lists).

---

## 🚀 The Solution: WPILib Struct Serialization
To resolve the interface blockage, the telemetry stream was updated to use **WPILib Struct Serialization via NetworkTables**. By explicitly binding a data topic to a native geometry object type, AdvantageScope instantly validates the data profile and activates the drop targets.

| Telemetry Strategy | NetworkTables Representation | AdvantageScope Behavior |
| :--- | :--- | :--- |
| **Legacy Sub-Tables** (`Field2d`) | Folder hierarchy with child keys (`0`, `1`, `2`) | ❌ **Rejected** (Viewed as a generic directory) |
| **Raw Arrays** (`double[]`) | Plain numerical list (`[2.0, 5.0, 0.0]`) | ❌ **Rejected** (Lacks semantic metadata) |
| **Modern Struct** (`Pose2d`) | Serialized binary stream explicitly tagged as **`Pose2d`** |  **Accepted** (Instantly recognized and mapped) |

---

## 🛠️ Complete Functional Python Implementation (`robot.py`)
This script isolates calculated physics loops inside the correct native `simulationPeriodic` method and broadcasts type-safe `Pose2d` struct telemetry via `robotPeriodic`.

```python
import wpilib
import wpilib.drive
import wpimath.geometry
import math
#from ntcore import NetworkTableInstance
import ntcore


class Robot(wpilib.TimedRobot):

    def robotInit(self):
        # Motors
        self.left_motor = wpilib.PWMSparkMax(0)
        self.right_motor = wpilib.PWMSparkMax(1)

        self.drive = wpilib.drive.DifferentialDrive(
            self.left_motor,
            self.right_motor
        )

        # Controller
        self.controller = wpilib.XboxController(0)

        # AdvantageScope / Field
        self.field = wpilib.Field2d()
        wpilib.SmartDashboard.putData("Field", self.field)

        # Starting position
        self.robot_pose = wpimath.geometry.Pose2d(
            2.0,
            5.0,
            wpimath.geometry.Rotation2d(0)
        )

        # Autonomous timer/state
        self.timer = wpilib.Timer()
        self.auto_state = "forward"

        # 3. Modern NetworkTables Struct Publisher
        # This publishes an explicit schema tag confirming the topic is a valid Pose2d geometry type.
        nt_instance = ntcore.NetworkTableInstance.getDefault()
        table = nt_instance.getTable("SmartDashboard")
        self.struct_pub = table.getStructTopic("ModernRobotPose", wpimath.geometry.Pose2d).publish()
 

    def robotPeriodic(self):
        self.struct_pub.set(self.robot_pose)


    def autonomousInit(self):
        self.timer.restart()
        self.auto_state = "forward"

    def autonomousPeriodic(self):
        if self.auto_state == "forward":
            self.drive.arcadeDrive(0.8, 0.0)

            if self.timer.hasElapsed(3.0):
                self.timer.restart()
                self.auto_state = "turn_left"

        elif self.auto_state == "turn_left":
            self.drive.arcadeDrive(0.0, -0.4)

            if self.timer.hasElapsed(0.5):
                self.timer.restart()
                self.auto_state = "stop"

        elif self.auto_state == "stop":
            self.drive.arcadeDrive(0.0, 0.0)

            if self.timer.hasElapsed(1.0):
                self.timer.restart()
                self.auto_state = "forward"

        self.update_simulation()

    def teleopInit(self):
        self.timer.stop()
        self.auto_state = "done"

    def teleopPeriodic(self):
        forward = -self.controller.getLeftY()
        turn = self.controller.getRightX()

        self.drive.arcadeDrive(forward, turn)

        self.update_simulation()

    def update_simulation(self):
        if wpilib.RobotBase.isSimulation():

            # Simulated wheel speeds
            left_speed = self.left_motor.get() * 3.0
            right_speed = self.right_motor.get() * 3.0

            # TimedRobot normally runs every 20 ms
            dt = 0.02

            # Distance traveled by each wheel
            d_left = left_speed * dt
            d_right = right_speed * dt

            # Distance between wheels
            track_width = 0.6

            # Change in robot angle
            angle_change = (d_right - d_left) / track_width

            old_angle = self.robot_pose.rotation().radians()
            new_angle = old_angle + angle_change

            # Average distance traveled
            distance = (d_left + d_right) / 2.0

            # Update X and Y
            new_x = (
                self.robot_pose.X()
                + distance * math.cos(new_angle)
            )

            new_y = (
                self.robot_pose.Y()
                + distance * math.sin(new_angle)
            )

            # Create new pose
            self.robot_pose = wpimath.geometry.Pose2d(
                new_x,
                new_y,
                wpimath.geometry.Rotation2d(new_angle)
            )

        # Send pose to NetworkTables
        self.field.setRobotPose(self.robot_pose)

    def disabledInit(self):
        self.left_motor.stopMotor()
        self.right_motor.stopMotor()


if __name__ == "__main__":
    wpilib.run(Robot)
```

<img width="1607" height="928" alt="image" src="https://github.com/user-attachments/assets/3518bb70-73b9-49e5-8dd5-74298b345e32" />

---

## 🔍 Verification Checklist
- [ ] **Run Code Simulation:** Execute `python robot.py sim` to instantiate the simulation server.
- [ ] **Establish Client Link:** Confirm AdvantageScope is actively connected to the server host network loopback (`127.0.0.1:1735`).
- [ ] **Verify Sidebar Subscriptions:** Look inside the left directory panel under `SmartDashboard` for **`ModernRobotPose`**.
- [ ] **Lock Component Row:** Drag **`ModernRobotPose`** directly down into the **Poses** tracker panel at the bottom of the field tab view.
