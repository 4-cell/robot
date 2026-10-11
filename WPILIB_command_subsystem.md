There isn’t one official name for it. It combines several well-known patterns, and the pieces do have names.

Your piece	Common names
Sequencer → Superstructure → Subsystems as a whole	Layered (hierarchical) control architecture. In robotics research it is close to the three-layer architecture (often called 3T), which has a skill/controller layer, a sequencing layer, and a planning layer. You have the lower two.
Sequencer with a step table, retries, and GOTO	Task sequencer or executive (the term in NASA and research robotics). The step table with failure policies is a simple plan executive.
Subsystem states (IDLE, LISTENING, ...)	Finite state machines. Nesting them (the Mic’s internal ROUGH → FFT → FINE stages) is a hierarchical state machine (HSM/HFSM), the idea behind statecharts.
Superstructure with one owner and a settle timer	Resource arbiter or mutual-exclusion manager. “Superstructure” is FRC jargon for a state machine that coordinates several mechanisms and prevents unsafe combinations.
request() / update() / result	Command pattern with polled completion. WPILib command-based programming is the same shape (initialize, execute, isFinished, end).
Context shared between steps	Blackboard pattern
Primitives like TURN(angle), LISTEN_CHIRP	Skills or actions. ROS 2 uses the word “actions” for goal / feedback / result tasks.

If you want to read more or use an existing library, these are the closest matches:

WPILib command-based framework (FRC). It is the nearest in spirit: subsystems, commands, command groups, and the scheduler’s requirement system that stops two commands from using the same subsystem. It runs on the roboRIO, not a Teensy, but the documentation explains the ideas well.
Behavior trees (BehaviorTree.CPP, py_trees). They solve the same “sequence with retries and fallbacks” problem as your sequencer, with a different structure: a tree, not a flat table with GOTO. They are popular in ROS 2 and game AI.
Statechart tools and libraries (for example Boost.SML, QP/C++ “Quantum Platform”). QP is an embedded active-object framework that runs well on microcontrollers like the Teensy if you want a formal HSM engine.
ROS 2 with SMACH/FlexBE or Nav2’s action servers. These are larger frameworks aimed at Linux-class computers. A Teensy would normally run only the low-level layer under them (micro-ROS is the bridge).

For a Teensy-only robot with a handful of primitives, what you have is a reasonable size. A framework mainly pays off when the number of states or sequences grows, when you need to edit sequences without recompiling, or when several people work on the code. If you ever outgrow the step table, behavior trees are the usual next step.

 
Searchable terms for your own reading: 
“three-layer robot architecture,” 
“hierarchical finite state machine,” 
“WPILib command-based subsystem requirements,” and “behavior tree vs state machine.”


# WPILib Command-Based: What Happens When a Second Button Is Pressed Mid-Sequence

*Design notes for a sequencer / superstructure / subsystem robot, compared with WPILib's scheduler*

## The question

A button press starts a whole sequence. Before that sequence finishes, a second button is pressed. What happens to the first sequence?

The short answer: it depends on the commands' requirements and on the running command's interruption setting. By default, the new button's command wins and the old sequence is cancelled.

## What happens in WPILib

A command group is itself one command. Its requirements are the **union** of every subsystem used by any step in it. When the second button schedules a command, the scheduler checks whether it shares any subsystem with the running group.

1. **No shared subsystems:** both run at the same time. This is the normal case for unrelated mechanisms.
2. **Shared subsystem, default settings:** the running group is cancelled (`kCancelSelf`). `end(interrupted = true)` runs on the step that was active. The remaining steps never run, and the sequence does not resume afterward. The new command then starts.
3. **Shared subsystem, running group set to `kCancelIncoming`:** the new command is not scheduled and the old sequence continues. You set this with `.withInterruptBehavior(InterruptionBehavior.kCancelIncoming)` on the command.

## Details that are easy to miss

- **The union rule can surprise you.** If a sequence is currently on a step that uses only the shooter, but a later step uses the drivetrain, a drivetrain command can still cancel the whole group, because the group's requirements include the drivetrain.
- **Cleanup is your responsibility.** A cancelled step must stop its own hardware in `end(true)`. For example, an intake command should stop its motor there. If it doesn't, the motor can keep running until something else commands it. When the subsystem becomes free, its default command is scheduled again.
- **Pressing the same button again:** scheduling a command that is already running does nothing, unless you bind it with `toggleOnTrue`, which cancels it, or `whileTrue`, which cancels it on release.
- **Reacting to cancellation:** the command decorators `.handleInterrupt(...)` and `.finallyDo(...)` let you run cleanup code when a sequence is interrupted.

## What this means for our robot

Our `Superstructure::request()` already refuses a new request while busy, so we have to choose the policy for a second command arriving mid-sequence. The three common choices map directly onto WPILib's behavior:

| Policy | Our robot | WPILib equivalent |
| --- | --- | --- |
| **Reject** the new command | Sequencer is running, ignore or queue the new AFSK command | `kCancelIncoming` |
| **Preempt** the sequence | `seq.abort()` (calls `emergencyStop()` and sets FAILED), then start the new sequence | `kCancelSelf` (the default) |
| **Queue** it | Keep a pending command and start it when the sequence reaches DONE | Command groups, or `andThen(...)` chaining |

## Recommendation

- For a **STOP** command, preempting is almost always the right choice: abort whatever is running and make the hardware safe.
- For other commands, rejecting or queueing is usually safer, so a stray message can't wreck a sequence in progress.
- The robot can't hear a new AFSK command while the Mic is not the active subsystem, so a second command can only arrive between primitives. That makes preemption simple to implement.

## Related reading

- WPILib command-based programming: command groups, requirements, and interruption behavior
- Behavior trees, as an alternative to a flat step table once sequences grow
