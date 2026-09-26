0, install python 3.14.7

1, uninstall existing one

py -3 -m pip uninstall robotpy robotpy-cli wpilib

 2, install stable (non-alpha) version
 
py -3 -m pip install robotpy

 3, check 2026.2.2 version is installed
 
py -3 -m pip show robotpy   (make sure it is robotpy Version: 2026.2.2)
 
4, create robot.py in your working directory
 
```python
import wpilib
 
class MyRobot(wpilib.TimedRobot):
 
    def robotInit(self):
        print("Robot startup")
 
    def teleopInit(self):
        print("Teleop started")
 
    def teleopPeriodic(self):
        print("Teleop loop")
 
if __name__ == "__main__":
    wpilib.run(MyRobot)
```


5, run the sim 

 py -3 -m robotpy sim
 
6, click teleoperated in the sim window (subwindow on the left top)  
<img width="1022" height="833" alt="Screenshot 2026-09-26 124022" src="https://github.com/user-attachments/assets/ed1bb710-f0cb-4c20-a394-7a09a473fb50" />

7, in windows powershell, you should see Teleop loop is printed over and over again by the wpilib engine.

```
Teleop loop
Teleop loop
Teleop loop
```

8, update robot.py and run the sim (py -3 -m robotpy sim) to see the field image and robot movement

```python
import wpilib
import wpilib.drive
import wpimath.geometry
import math


class Robot(wpilib.TimedRobot):
    def robotInit(self):
        self.left_motor = wpilib.PWMSparkMax(0)
        self.right_motor = wpilib.PWMSparkMax(1)
        self.drive = wpilib.drive.DifferentialDrive(self.left_motor, self.right_motor)
        self.controller = wpilib.XboxController(0)

        self.field = wpilib.Field2d()
        wpilib.SmartDashboard.putData("Field", self.field)

        self.robot_pose = wpimath.geometry.Pose2d(2.0, 5.0, wpimath.geometry.Rotation2d(0))

        self.timer = wpilib.Timer()
        self.teleop_state = "done"  # nothing running until teleopInit fires

    def teleopInit(self):
        # Kick off a short automatic move as soon as teleop starts.
        self.timer.restart()
        self.teleop_state = "forward"

    def teleopPeriodic(self):
        if self.teleop_state == "forward":
            self.drive.arcadeDrive(0.4, 0.0)  # drive forward, no turn
            if self.timer.hasElapsed(0.5):
                self.timer.restart()
                self.teleop_state = "turn_left"

        elif self.teleop_state == "turn_left":
            self.drive.arcadeDrive(0.0, -0.4)  # negative rotation = turn left
            if self.timer.hasElapsed(0.5):
                self.timer.restart()
                self.teleop_state = "stop"

        elif self.teleop_state == "stop":
            self.drive.arcadeDrive(0.0, 0.0)
            self.teleop_state = "done"

        else:
            # Normal manual driving once the auto sequence has finished.
            forward = -self.controller.getLeftY()
            turn = self.controller.getRightX()
            self.drive.arcadeDrive(forward, turn)

        if wpilib.RobotBase.isSimulation():
            left_speed = self.left_motor.get() * 3.0
            right_speed = self.right_motor.get() * 3.0
            dt = 0.02

            d_left = left_speed * dt
            d_right = right_speed * dt
            track_width = 0.6

            angle_change = (d_right - d_left) / track_width
            new_angle = self.robot_pose.rotation().radians() + angle_change
            distance = (d_left + d_right) / 2.0

            new_x = self.robot_pose.X() + distance * math.cos(new_angle)
            new_y = self.robot_pose.Y() + distance * math.sin(new_angle)

            self.robot_pose = wpimath.geometry.Pose2d(
                new_x, new_y, wpimath.geometry.Rotation2d(new_angle)
            )

        self.field.setRobotPose(self.robot_pose)

    def disabledInit(self):
        self.left_motor.stopMotor()
        self.right_motor.stopMotor()


if __name__ == "__main__":
    wpilib.run(Robot)

```
<img width="950" height="634" alt="Screenshot 2026-09-26 102903" src="https://github.com/user-attachments/assets/5eca7d72-dc28-46d3-a345-1302da3e9d6f" />


reference:

tool version checking command: 

py -3 -m pip show robotpy

PS C:\Users\rosep\BREADRobot\robotSimTest> py -3 -m pip show robotpy
```
Name: robotpy
Version: 2026.2.2
Summary: Meta package to make installing robotpy easier
Home-page: https://github.com/robotpy/robotpy-meta
Author: RobotPy Development Team
Author-email: robotpy@googlegroups.com
License: BSD-3-Clause
Location: C:\Users\rosep\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages
Requires: pyfrc, pyntcore, robotpy-cli, robotpy-hal, robotpy-halsim-gui, robotpy-installer, robotpy-wpilib-utilities, robotpy-wpimath, robotpy-wpinet, robotpy-wpiutil, wpilib
Required-by:
```
