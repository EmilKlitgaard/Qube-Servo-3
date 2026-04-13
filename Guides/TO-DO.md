# TO-DO List

## Bugs & Fixes

### 1. Fix StaticGraph initialization error
**Files:** [StaticGraph.py](../Python/interface/StaticGraph.py) | [AppInterface.py](../Python/interface/AppInterface.py)

**Problem:** StaticGraph is not displaying correctly when intended (at the end of simulation). The issue stems from `self.init_dashboard()` not correctly initializing the parent CTk window via `super().__init__()`.

**Details:**
- In StaticGraph, the `run()` method waits for simulation to finish, then calls `self.init_dashboard()`
- The parent AppInterface should initialize the CTk window properly
- When initialization fails, the plot doesn't render or the window appears empty
- Verify that `super().__init__()` in AppInterface creates the CTk window correctly before calling timeline setup and grid configuration

**Expected behavior:** Graph window displays historical data with proper layout after simulation completes.

---

### 2. Modify Physical.py HIL communication
**File:** [Physical.py](../Python/control_platform/Physical.py)

**Problem:** Physical.py needs to correctly communicate with the actual QUBE-Servo 3 hardware via the Quanser HIL API.

**Details:**
- Current implementation uses Quanser SDK (HIL class) to interface with real hardware
- Ensure channel definitions (`_ANA_R`, `_ENC_R`, `_DIG_R`, `_OTH_R` and write channels) match the actual Qube-Servo 3 pinout
- Verify encoder counts-to-radians conversion (`COUNTS_TO_RAD`)
- Test UART communication through the HIL interface
- Ensure motor command (voltage write) and state read (encoder + potentiometer) work bidirectionally

**Expected behavior:** Real hardware reads sensor state and responds to motor voltage commands without errors.

---

## Features

### 3. Implement control loop integration in Dashboard
**File:** [Dashboard.py](../Python/interface/Dashboard.py)

**Problem:** The START/STOP button should only be used for starting [ControlLoop.py](../Python/controller/ControlLoop.py)'s `run_controller()` function. Currently, the control loop awaits user input (waiting for enter) in all modes.

**Details:**
- In **Graph mode** (SIMULATION=True): Keep the current behavior where `run_controller()` waits for user to press enter
- In **Dashboard mode** (SIMULATION=False): The START/STOP button should start the control loop immediately
  - When pressed, the button triggers `run_controller()` (no enter-wait)
  - After the button is pressed, it should be hidden or disabled so it cannot be pressed again
  - Only the MOTOR ENABLE and RESET buttons remain available for control
- Modify [main.py](../Python/main.py) and/or [ControlLoop.py](../Python/controller/ControlLoop.py) to conditionally check if Graph or Dashboard is active before awaiting input

**Expected behavior:** In live Dashboard mode, click START to begin control loop; in simulation Graph mode, hit enter at console prompt.

---

### 4. Add SQL database for logging (optional)
**Files:** [Logging.py](../Python/data/Logging.py) | [Config.yaml](../Python/Config.yaml) | [requirements.txt](../Python/requirements.txt)

**Problem:** Currently, logged data is stored temporarily in memory (lists). Data is lost after session ends.

**Details:**
- Implement persistent storage using SQLite or another lightweight database
- Create a database schema to store:
  - Timestamp
  - System state (theta, theta_dot, alpha, alpha_dot, voltage_demand)
  - Metadata (run date/time, config used, simulation vs physical)
- Modify Logger class to write each entry to database instead of (or in addition to) in-memory lists
- Add database connection management (open/close) in Config or Logger
- Add optional config flag to enable/disable database logging
- Maintain backward compatibility with current in-memory plotting

**Expected behavior:** Logged data persists across sessions and can be queried from database for later analysis.
