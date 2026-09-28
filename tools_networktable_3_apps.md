# FRC Software Systems: NetworkTables & Core Dashboards

This document provides a comprehensive overview of **NetworkTables** and the three primary data visualization applications used in the FIRST Robotics Competition (FRC): **Shuffleboard**, **Glass**, and **AdvantageScope**.

---

## 1. NetworkTables (The Backbone)
**NetworkTables** is an invisible, built-in network protocol and data library running within your robot code and driver station software. It acts as a **centralized shared whiteboard** in the cloud that both your robot and your laptop can read from and write to simultaneously over Wi-Fi or Ethernet.

### Core Concepts:
* **The "Table" Structure:** Data is organized hierarchically like directories and files on a computer (e.g., `SmartDashboard/Launcher/Shooter RPM`).
* **Publish/Subscribe Model:** Robot code "publishes" a topic (like a sensor value or coordinate array), and dashboard applications "subscribe" to it to read and display the data live.
* **NetworkTables 4 (NT4):** The modern implementation optimized for low latency, high bandwidth, and robust structure parsing (including WPILib Structs).

---

## 2. The Dashboard Applications

| Feature / Attribute | **Shuffleboard** | **Glass** | **AdvantageScope** |
| :--- | :--- | :--- | :--- |
| **Primary Use Case** | Driver Station Interface | Live Developer Tuning | Data Analysis & Log Review |
| **Target User** | Drive Team (Drivers/Operators) | Programmers & Pit Crew | Programmers & Strategists |
| **Data Source** | Live NetworkTables Only | Live NetworkTables Only | **Live NT & Offline Log Files** |
| **Performance Overhead** | Heavy (Java-based) | Extremely Light (Native C++) | Highly Optimized (TypeScript/Electron) |
| **Key Strength** | Big, readable, layout-customizable layouts | High-speed live charts and modularity | Timeline scrubbing, 3D tracking, video sync |

### 📊 Shuffleboard (The Driver's Display)
Shuffleboard is the standard dashboard designed to be mounted on the Driver Station laptop during official matches. It prioritizes clarity and glanceability over raw scientific data.
* **Best For:** Auto selectors, live camera feeds, and massive status indicators (e.g., a giant green box indicating "Intake Loaded").
* **Limitation:** Can be resource-heavy and prone to lag if burdened with high-rate data arrays.

### 🔍 Glass (The Live Tuning Tool)
Glass is a developer-focused utility built natively in C++. It features an ultra-responsive, modular canvas meant for real-time mechanism diagnosis.
* **Best For:** Plotting high-speed strip charts (like matching target RPM vs. actual RPM), adjusting PID gains live, and monitoring raw NetworkTables infrastructure.
* **Limitation:** Cannot save history or open offline logs; once the robot turns off, the data stream vanishes.

### 📈 AdvantageScope (The Data Analyst)
AdvantageScope is an advanced, timeline-driven diagnostic tool. Rather than serving as a real-time driver dashboard, it is designed for analyzing what the robot did after a run completes.
* **Best For:** Opening `.wpilog` or `.hoot` files, scrubbing back and forth on a time-axis, overlaying 2D/3D odometry maps, and syncing phone/match video side-by-side with telemetry logs.
* **Limitation:** Not intended to display a driver camera feed or act as a primary interface during an active match.

---

## 3. Recommended Development Workflow
To maximize efficiency during a competitive season, teams should utilize these tools collectively across different phases:
1. **In the Lab (Code Setup):** Use **Glass** to verify your sensors are reading correctly and tune your closed-loop feedback controllers.
2. **On the Field (During Matches):** Use **Shuffleboard** (or lightweight alternatives like **Elastic**) to give your drive team simple, visual cues and auto selection.
3. **In the Pits (Post-Match Review):** Download the log file from the robot, load it into **AdvantageScope**, and review any anomalies alongside recorded match footage.
