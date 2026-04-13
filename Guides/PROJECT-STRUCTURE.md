# Project Structure

## Overview
Inverted pendulum stabilization system for Quanser QUBE-Servo 3.

**Thread Architecture:**
- **Main thread**: GUI dashboard/visualization (event loop)
- **UART thread**: Receives state updates from TM4C123 microcontroller  
- **Control thread**: Swing-up control, then LQR stabilization

---

## [`Python/`](../Python/) — Host-side control software

| File | Purpose |
|---|---|
| [`main.py`](../Python/main.py) | Entry point. Initializes UART & control threads, then runs dashboard GUI on main thread. |
| [`Config.py`](../Python/Config.py) | Global configuration singleton (reads `Config.yaml`). |
| [`Config.yaml`](../Python/Config.yaml) | Settings: debug mode, UART port/baud, simulation vs. physical, visualization. |
| [`requirements.txt`](../Python/requirements.txt) | Dependencies: `pyserial`, `numpy`, `pyyaml`, `matplotlib`, `customtkinter`. |

---

## [`Python/control_platform/`](../Python/control_platform/) — Hardware abstraction layer

| File | Purpose |
|---|---|
| [`QubeInterface.py`](../Python/control_platform/QubeInterface.py) | Abstract interface: `read()`, `write()`, `set_led()`, `reset()`, `enable()`. |
| [`Physical.py`](../Python/control_platform/Physical.py) | Real hardware implementation (Quanser HIL API). |
| [`Virtual.py`](../Python/control_platform/Virtual.py) | Simulated pendulum (ODE model, no hardware required). |

---

## [`Python/controller/`](../Python/controller/) — Control algorithms

| File | Purpose |
|---|---|
| [`ControlLoop.py`](../Python/controller/ControlLoop.py) | Main control loop. Reads state, computes voltage, logs/plots data. |
| [`Controller.py`](../Python/controller/Controller.py) | Mode-switching logic: swing-up phase → stabilization (LQR). |
| [`SwingUp.py`](../Python/controller/SwingUp.py) | Swing-up state machine (6-step sequence). |

---

## [`Python/data/`](../Python/data/) — Data logging & visualization

| File | Purpose |
|---|---|
| [`Logging.py`](../Python/data/Logging.py) | `Logger` class. Stores time, theta, theta_dot, alpha, alpha_dot, voltage history. |
| [`Plot.py`](../Python/data/Plot.py) | `Plotter` class. Live animated matplotlib plot (embedded or standalone). |

---

## [`Python/interface/`](../Python/interface/) — Dashboard & visualization UI

| File | Purpose |
|---|---|
| [`AppInterface.py`](../Python/interface/AppInterface.py) | Abstract base class for dashboard modes (customtkinter-based). |
| [`Dashboard.py`](../Python/interface/Dashboard.py) | Live control dashboard (SIMULATION=False). Control buttons, status, live plot. |
| [`StaticGraph.py`](../Python/interface/StaticGraph.py) | Historical plot viewer (SIMULATION=True). Post-run data visualization. |

---

## [`Python/tiva_microcontroller/`](../Python/tiva_microcontroller/) — Microcontroller communication

| File | Purpose |
|---|---|
| [`UART.py`](../Python/tiva_microcontroller/UART.py) | UART serial interface (pyserial wrapper). Thread-safe, handles connection management. |

---

## [`Tiva Microcontroller/`](../Tiva%20Microcontroller/) — Embedded firmware (TM4C123 ARM Cortex-M4)

Low-level firmware for the TM4C123GH6PM microcontroller (CCS project).

| File | Purpose |
|---|---|
| [`main.c`](../Tiva%20Microcontroller/main.c), [`*.h`] | Core controller loop. Reads sensors, executes motor control, transmits state via UART. |
| [`uart0.c/h`](../Tiva%20Microcontroller/uart0.c) | UART0 serial communication driver. |
| [`GPIO.c/h`](../Tiva%20Microcontroller/GPIO.c) | GPIO control (LEDs, general I/O). |
| [`Timer.c/h`](../Tiva%20Microcontroller/Timer.c) | Timer interrupts for control loop timing. |
| [`Potentiometer.c/h`](../Tiva%20Microcontroller/Potentiometer.c) | ADC sampling (arm & pendulum angles). |
| [`Button.c/h`](../Tiva%20Microcontroller/Button.c) | Button input handling. |
| [`Numpad.c/h`](../Tiva%20Microcontroller/Numpad.c) | Numeric keypad interface. |
| [`Queue.c/h`](../Tiva%20Microcontroller/Queue.c) | Event queue for concurrent operation. |
| [`Events.c/h`](../Tiva%20Microcontroller/Events.c) | Event dispatcher & handlers. |
| [`Sleep.c/h`](../Tiva%20Microcontroller/Sleep.c) | Sleep mode management. |
| [`Print.c/h`](../Tiva%20Microcontroller/Print.c) | Debug printing utility. |
| [`tm4c123gh6pm.h`] | Microcontroller hardware definitions. |
| [`tm4c123gh6pm_startup_ccs.c`], [`tm4c123gh6pm.cmd`] | Linker script & startup code. |

---

## [`Virtual_model/`](../Virtual_model/) — Robot URDF & physics

| File | Purpose |
|---|---|
| [`Qube_Servo_3.urdf`](../Virtual_model/Qube_Servo_3.urdf) | URDF robot model description. |
| [`Qube_Servo_3.xml`](../Virtual_model/Qube_Servo_3.xml) | MuJoCo physics configuration. |

---

## [`Images/`](../Images/)
Project documentation images.
