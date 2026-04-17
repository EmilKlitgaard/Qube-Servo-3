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

### 3. Setup actual control loops
**Files:** [Controller.py](../Python/controller/Controller.py) | [ControlLoop.py](../Python/controller/ControlLoop.py) | [SwingUp.py](../Python/controller/SwingUp.py)

**Problem:** Control loops must be integrated and tested to transition smoothly between swing-up and stabilization modes, with proper tuning of LQR gains and PD parameters.

**Details:**
- Update `compute_modern_stabilize()` and `compute_classic_stabilize()` gain coefficients based on hardware testing
- Verify mode-switching thresholds in `swingup.is_upright()` prevent oscillation between modes
- Test voltage saturation limits `[-18V, +10V]` on physical hardware
- Integrate `ControlLoop.py` with `Physical.py` / `Virtual.py` for bidirectional state/command flow
- Tune `config.CONTROL_MODERN_STABILIZATION` selection (LQR vs PD) for stable operation

**Expected behavior:** Pendulum swings up from rest, transitions to stabilization when upright, and maintains balance at target angles with responsive, stable control.