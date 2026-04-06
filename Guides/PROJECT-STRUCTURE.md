# Project Structure

## Overview
Inverted pendulum stabilization system for Quanser QUBE-Servo 3. The system comprises:
- **Main thread**: GUI event loop (displays live plot and controls)
- **UART thread**: Listens for state updates from microcontroller
- **Control thread**: Executes swing-up sequence, then stabilization control

---

## [`Python/`](../Python/) — Main codebase

| File | Purpose |
|---|---|
| [`main.py`](../Python/main.py) | Entry point. Spawns UART and controller threads, then launches GUI on main thread. |
| [`Config.py`](../Python/Config.py) | Singleton config. Reads `Config.yaml` and exposes settings globally (`from Config import config`). |
| [`Config.yaml`](../Python/Config.yaml) | Project settings: debug mode, UART port/baud, simulation flag, plotting flag. |
| [`requirements.txt`](../Python/requirements.txt) | Dependencies: `pyserial`, `numpy`, `pyyaml`, `matplotlib`. |

---

## [`Python/control_platform/`](../Python/control_platform/) — Hardware abstraction

Supports both physical Qube and virtual (simulated) environments via a common interface.

| File | Purpose |
|---|---|
| [`QubeInterface.py`](../Python/control_platform/QubeInterface.py) | Abstract base class defining the interface: `read()`, `write()`, `set_led()`, `reset()`, `enable()`. |
| [`Physical.py`](../Python/control_platform/Physical.py) | Implementation using Quanser HIL API for actual hardware. |
| [`Virtual.py`](../Python/control_platform/Virtual.py) | Simulated pendulum model (ODEs, no external hardware). |

---

## [`Python/controller/`](../Python/controller/) — Control logic

Mode-switching between swing-up and stabilization phases.

| File | Purpose |
|---|---|
| [`ControlLoop.py`](../Python/controller/ControlLoop.py) | Main loop (`run_controller()`). Reads state, computes voltage demand, updates LED, logs/plots data. |
| [`Controller.py`](../Python/controller/Controller.py) | Combined swing-up + stabilization controller. Manages mode-switching and LQR feedback gains. |
| [`SwingUp.py`](../Python/controller/SwingUp.py) | State machine: moves arm to swing pendulum from down to near-upright (6 discrete steps). |

---

## [`Python/data/`](../Python/data/) — Logging & visualization

| File | Purpose |
|---|---|
| [`Logging.py`](../Python/data/Logging.py) | `Logger` class. Records time, theta, theta_dot, alpha, alpha_dot, voltage at each timestep. |
| [`Plot.py`](../Python/data/Plot.py) | `Plotter` class. Live animated 2D plot (matplotlib) showing state trajectories over time. |

---

## [`Python/interface/`](../Python/interface/) — User interface

| File | Purpose |
|---|---|
| [`GUI.py`](../Python/interface/GUI.py) | GUI window (main thread). Displays live plot section, start/stop control, enable/disable, reset button, mode indicator (swingup/stabilize). Closes gracefully via `stop_event`. |

---

## [`Python/tiva_microcontroller/`](../Python/tiva_microcontroller/) — Microcontroller interface

| File | Purpose |
|---|---|
| [`UART.py`](../Python/tiva_microcontroller/UART.py) | `UART` class (pyserial wrapper). Provides `read_line()`, `loop()`, `list_ports()`. Thread-safe, handles connection errors. |

---

## [`Virtual_model/`](../Virtual_model/) — Robot description

| File | Purpose |
|---|---|
| [`Qube_Servo_3.urdf`](../Virtual_model/Qube_Servo_3.urdf) | URDF model of the Qube Servo 3 (for visualization/simulation environments). |
| [`Qube_Servo_3.xml`](../Virtual_model/Qube_Servo_3.xml) | Simulation configuration (physics, dynamics). |

---

## [`Images/`](../Images/)
Project images used in the README.
