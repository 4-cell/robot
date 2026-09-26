import wpilib
 
# class MyRobot(wpilib.TimedRobot):
 
#     def robotInit(self):
#         print("Robot startup")
 
#     def teleopInit(self):
#         print("Teleop started")
 
#     def teleopPeriodic(self):
#         print("Teleop loop")

# if __name__ == "__main__":
#     wpilib.run(MyRobot)

class Robot(wpilib.TimedRobot):
    def robotInit(self):
        # PWM port 0 — wire the Spark Max's PWM input to this port on the RoboRIO
        self.motor = wpilib.PWMSparkMax(0)

        self.timer = wpilib.Timer()
        self.state = "forward"

    def autonomousInit(self):
        self.timer.restart()
        self.state = "forward"

    def autonomousPeriodic(self):
        self.motor.set(0.5)  # 50% speed forward
        # # print("autonomousPeriodic loop")
        # if self.state == "forward":
        #     self.motor.set(0.5)  # 50% speed forward
        #     if self.timer.hasElapsed(1.0):
        #         self.timer.restart()
        #         self.state = "backward"
        # elif self.state == "backward":
        #     self.motor.set(-0.5)  # 50% speed backward
        #     if self.timer.hasElapsed(1.0):
        #         self.timer.restart()
        #         self.state = "done"
        # else:
        #     self.motor.stopMotor()

    def disabledInit(self):
        self.motor.stopMotor()


if __name__ == "__main__":
    wpilib.run(Robot)

