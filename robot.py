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
