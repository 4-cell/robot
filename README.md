0, install python 3.14.7

1, uninstall existing one

py -3 -m pip uninstall robotpy robotpy-cli wpilib

 2, install stable (non-alpha) version
 
py -3 -m pip install robotpy

 3, check 2026.2.2 version is installed
 
py -3 -m pip show robotpy   (make sure it is robotpy Version: 2026.2.2)
 
4, create robot.py (see the code)

5, run the sim 

 py -3 -m robotpy sim
 
6, and click teleoperated in the sim window (subwindow on the left top)  

7, in windows cmd, you should see Teleop loop is printed over and over again by the wpilib engine.



robot.py code:
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
