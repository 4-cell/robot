robotypy step
1. change directory to this

   
   C:\Users\rosep\breadrobot\robot-code\robots\delta-systemcore
then
py -3.14 -m venv .venv

2. \.venv\Scripts\activate

3. python -m pip install robotpy-installer


If you want to check version use


py -3 -m pip show robotpy-installer

4. py -3 -m pip install --upgrade robotpy-installer

```
(.venv) C:\Users\rosep\breadrobot\robot-code\robots\delta-systemcore>python -m pip show robotpy-installer
Name: robotpy-installer
Version: 2027.0.0a9
```
   
5.python -m pip install robotpy


6. python -m robotpy sync

```
ERROR: Cannot install robotpy and robotpy-commands-v2==2027.0.0a6.post1 because these package versions have conflicting dependencies.

The conflict is caused by:
    robotpy 2027.0.0a7 depends on wpilib==2027.0.0a7
    robotpy-commands-v2 2027.0.0a6.post1 depends on wpilib==2027.0.0a6.post1

Additionally, some packages in these conflicts have no matching distributions available for your environment:
    wpilib

To fix this you could try to:
1. loosen the range of package versions you've specified
2. remove package versions to allow pip to attempt to solve the dependency conflict

ERROR: ResolutionImpossible: for help visit https://pip.pypa.io/en/latest/topics/dependency-resolution/#dealing-with-dependency-conflicts
```
