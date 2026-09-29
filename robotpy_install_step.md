robotypy step

0. uninstall all  :  py -3 -m pip uninstall robotpy robotpy-cli wpilib robotpy-installer

1. change directory to this

   C:\Users\rosep\breadrobot\robot-code\robots\delta-systemcore
then


2. py -3.14 -m venv .venv

3. \.venv\Scripts\activate

4. py -3 -m pip install robotpy-installer==2027.0.0a9
 
5. py -3 -m pip show robotpy-installer

 

```
(.venv) C:\Users\rosep\breadrobot\robot-code\robots\delta-systemcore>python -m pip show robotpy-installer
Name: robotpy-installer
Version: 2027.0.0a9
```
   
6. py -3 -m pip install robotpy

now, if I do: 
py -3 -m pip show robotpy wpilib robotpy-installer

I got:
```
Name: robotpy
Version: 2026.2.2
Name: wpilib
Version: 2026.2.2
Name: robotpy-installer
Version: 2026.0.2
```


7. py -3 -m robotpy sync

```
(.venv) C:\Users\rosep\BREADRobot\zz_robot-code\robots\delta-systemcore> py -3 -m robotpy sync
21:15:34:573 INFO    : robotpy.installer   : RobotPy Installer 2026.0.2
21:15:34:574 INFO    : robotpy.installer   : -> caching files at C:\Users\rosep\wpilib\2026\robotpy
ERROR: Only RobotPy 2026.x is supported by this version of robotpy-installer (C:\Users\rosep\BREADRobot\zz_robot-code\robots\delta-systemcore\pyproject.toml has 2027.0.0a6.post1)
```
