# Superstructure and Subsystem Architecture Q&A

This document summarizes the technical discussion regarding the Command-Based Robot software architecture, focusing on the roles of the **Superstructure**, individual **Subsystems**, path planning, hardware control, and multi-subsystem coordination.



## 1. Development Effort Distribution at the Start of a New Season

### Question
Which part of this software layout takes the most time and effort when a new season begins?

### Answer
The components requiring the most time and effort are the **Superstructure State Machine** and **Shot/Targeting Calculations**:

1. **Superstructure State Machine (`superstructure.py`):** Must be re-architected each season to handle new game piece geometries, intake/storage routines, scoring sequences, and safety readiness checks between mechanisms.
2. **Shot Calculation & Constants (`constants.py` & `util/`):** Building physical trajectory models, generating dynamic distance lookup tables ($RPS$, hood angles), and updating field coordinates for target scoring and passing zones requires extensive calibration and empirical testing.
3. **Autonomous Trajectories (`autonomous/` & `PathPlannerLib`):** All field paths must be redrawn to navigate new field obstacles, collect pieces from starting zones, and align to new field targets within the 15-second autonomous period.

*Reusable Components:* Low-level hardware drivers, Swerve drivetrain abstractions (`subsystems/swerve`), and logical controller abstractions (`controls.py`) are largely modular and carry over year-to-year with minimal adjustments.


## 2. Clarifying Superstructure vs. Drivetrain Subsystem Responsibilities

### Question
You said Real-Time Dynamic Path Replanning is done in subsystems, but it requires input from vision, collision detection, intake, or shooter in coordinating multi-subsystem tasks. Does this change the roles?

### Answer
No, the division of responsibilities remains distinct:

* **Superstructure Commands *What* to Do:**
  * High-level state decisions ("Are we in `PRESHOOT` or `SHOOT` mode?", "Is a game piece indexed?").
  * Decides *when* to re-route or shift behavior.
  * Directs individual subsystems simultaneously (e.g., command Swerve to drive to Pose $(X, Y)$, command Shooter to spin to $RPS$).
* **Drivetrain Subsystem Executes *How* to Drive:**
  * Uses `PhotonVision` updates fed into the swerve pose estimator.
  * Trajectory Generation & Replanning math (generating splines around obstacles, calculating wheel module speeds $v_x, v_y, \omega$) occurs inside the navigation engine/Drivetrain subsystem.
  * Runs $20\text{ ms}$ PID control loops to track the calculated path.

---

## 3. Control Complexity: Simultaneous vs. Sequential Operations

### Question
Which option is easier to control and program, and why?
* **Option A:** Move, shoot, and intake at the same time.
* **Option B:** Stop intake, move to a certain point, stop, and shoot.

### Answer
**Option B** (Sequential) is significantly easier to control and program than **Option A** (Simultaneous).

### Detailed Breakdown

1. **Kinematics & Targeting Math:**
   * *Option B (Sequential):* Stationary pose $(X, Y, \theta)$ allows fixed 2D lookup tables for shooter speed ($RPS$), hood angle, and aiming heading.
   * *Option A (Simultaneous):* Requires **real-time velocity compensation**. Shot calculations must adjust for linear velocity, rotational velocity, and projectile time-of-flight on the fly.
2. **State Machine Complexity:**
   * *Option B (Sequential):* Simple sequential state machine (`SequentialCommandGroup`): $\text{Intake} \rightarrow \text{Drive To Pose} \rightarrow \text{Shoot}$. Subsystems operate in isolation.
   * *Option A (Simultaneous):* Requires a high-level Superstructure to continuously evaluate swerve pose, heading lock, flywheel velocity, and game piece feeding without jams.
3. **Physical Dynamics & Electrical Stability:**
   * *Option B (Sequential):* Stopping eliminates frame vibrations and sensor jitter right before firing.
   * *Option A (Simultaneous):* Intaking while moving introduces mechanical noise. Simultaneous high-current draws across drive, intake, indexer, and flywheel motors create risk of **voltage sags (brownouts)**.

---

## 4. Dynamic Obstacle Avoidance vs. Superstructure

### Question
When the robot is ordered to go from Point A to Point B in the field and an enemy robot is blocking the path, what should the robot do to accomplish the command? Is Real-Time Dynamic Path Replanning part of the Superstructure?

### Answer
When a path-following command encounters an obstacle:

1. **Detection:** Coprocessors running tools like PhotonVision or distance sensors detect the physical boundary or AprilTag occlusion of the blocking robot. Field updates mark the space occupied by the opponent as unnavigable in the internal costmap/grid.
2. **Real-Time Dynamic Path Replanning:** Pathfinding tools (such as **PathPlannerLib**) generate a new waypoint trajectory around the blocked zone while trying to preserve heading and target timing. The online pathplanner continuously re-evaluates local waypoints each periodic loop ($20\text{ ms}$) to steer clear of the obstacle.
3. **Fallback & Drivers:**
   * *Autonomous Mode:* If no path exists, the command will stall until a timeout occurs or cycle to a fallback state to avoid pin/blocking penalties.
   * *Teleoperated Mode:* The pathfinding command can be interrupted by manual driver overrides or toggled off.

**Is it part of the Superstructure?**  
No. Real-time pathfinding, obstacle avoidance, trajectory generation, and drivetrain motor control belong to the drivetrain subsystem (`subsystems/swerve`) and external navigation libraries (**PathPlannerLib**). The Superstructure acts as a high-level state machine coordinator across *multiple* subsystems and does not calculate dynamic navigation paths or trajectory splines around obstacles.

---

## 5. Subsystem Communication & Coordination

### Question
My system wants to do intake, shoot, and swerve at the same time. If they are separated subsystems and not able to talk, they cannot do the three tasks at the same time (because shooting requires knowing current position relative to the target). How can subsystem communication be accomplished? Should this be done in the Superstructure?

### Answer
Yes, coordinating multi-subsystem tasks is precisely what the **Superstructure** is designed to handle.

### Mechanics of Coordination

1. **Role of the Superstructure:**
   In command-based architecture (such as WPILib / Commands2), individual subsystems (`Swerve`, `Shooter`, `Intake`) are kept decoupled. The **Superstructure** sits above all subsystems as a high-level coordinator:
   * **Reads States & Sensors:** Checks the current state of each subsystem (pose, shooter speed, intake deployment).
   * **Calculates Targeting Data:** Takes the current robot pose from `Swerve` and calculates distance and heading relative to the field target.
   * **Issues Commands Simultaneously:**
     * `Swerve`: Lock target heading while maintaining translation control.
     * `Shooter`: Spin up flywheels to target $RPS$ and set hood angle.
     * `Intake`: Deploy and run intake/conveyors when readiness checks pass.

2. **Inter-Subsystem Data Transfer Patterns:**
   * **Centralized Coordination (`superstructure.py`):** Pulls data from one subsystem and passes it as parameters to another during the $20\text{ ms}$ periodic loop.
   * **Shared State / Pose Estimators:** A `Vision` subsystem or Pose Estimator publishes the latest robot position to a shared location (such as `RobotPose` or NetworkTables), which the Superstructure reads to compute shooting parameters.

### Execution Flow
```
+-----------------------+
|    Sensors / Vision   |
+-----------+-----------+
| Updates Robot Pose
v
+-----------------------+
|    Superstructure     | <--- Reads Driver Input / Target Locations
+-----------+-----------+
| Calculates Shot & Heading
|
+--------+--------+------------------+
|                 |                  |
v                 v                  v
+---------+      +-----------+      +-----------+
| Swerve  |      |  Shooter  |      |  Intake   |
+---------+      +-----------+      +-----------+
```
---


## 6. Joystick Commands to Superstructure & Controller Mappings

### Question
How do joystick inputs translate into commands the Superstructure can understand? What is a typical FRC controller/button layout for intake, shooter, and drivetrain?

### Abstraction Pipeline
1. **Hardware Polling:** Axis and button inputs read every $20\text{ ms}$ via driver station protocols (`CommandXboxController`).
2. **Logical Interface (`controls.py`):** Raw axis values pass through deadbands and direction inversion. Maps raw buttons to semantic methods (`get_shoot_button()`).
3. **Command & Trigger Bindings (`button_bindings.py`):** Registers triggers on controller methods to invoke commands or issue state requests to the Superstructure.
4. **State Machine (`superstructure.py`):** Translates requests into high-level state changes (`IDLE` $\rightarrow$ `PRESHOOT` $\rightarrow$ `SHOOT`), calculates aiming parameters, and issues targets to subsystems.
```
[ Driver / Operator Joystick ]
│
▼
controls.py  (Deadband & Axis Filtering)
│
▼
button_bindings.py  (Triggers & Callbacks)
│
▼
superstructure.py  (High-Level State Machine)
│
▼
[ Swerve / Shooter / Intake Subsystems ]
```

### Typical FRC Button Mapping

#### Driver Controller (Port 0)
* **Translation:** Left Stick Y (Forward/Backward), Left Stick X (Strafe).
* **Rotation:** Right Stick X (Rotational Speed), Left Bumper (Heading Lock / Auto-Align).
* **Intake:** Right Trigger (Deploy & Run Intake), Left Trigger (Outtake / Reverse), Y Button (Stow Intake).
* **Shooting:** B Button (Dynamic Shooting with Vision/Heading Lock), Right Bumper (Static Preset Shot).
* **Auxiliary:** Back Button (Raise Juicer/Climber), X Button (Lower/Idle Juicer).

#### Operator Controller (Port 1)
* **Overrides:** A Button (Unjam Sequence), Right Bumper (System Zero / Starting Configuration Reset).

---
