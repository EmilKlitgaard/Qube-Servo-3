"""
Virtual.py – MuJoCo-based simulator for the Quanser QUBE-Servo 3.

This module implements the QubeInterface using MuJoCo physics engine.
Cross-platform compatible: Windows, macOS, Linux.

The QUBE-Servo 3 has two joints:
  - theta (arm): rotates horizontally, 0 at center, limited to [-π/2, +π/2]
  - alpha (pendulum): rotates vertically about the arm, 0 when upright, π when down

The simulator handles:
  - Motor control via voltage input (mapped to torque via motor constant)
  - Gravity acting on the pendulum
  - Fixed timestep integration
  - LED simulation (stored as state, not visualized)

Following MuJoCo documentation best practices:
  - Model definition stored in MJCF XML file on disk
  - Using platform-independent file path handling via os.path
"""

import os
import math
import time
import mujoco

from Config import config
from typing import Tuple, Optional
from control_platform import QubeInterface

# ── Model file path ────────────────────────────────────────────────────────────
def get_model_file_path() -> str:
    """
    Get the absolute path to Qube_Servo_3.xml model file.
    """
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    model_file = os.path.join(root_dir, "Virtual_model", "Qube_Servo_3.xml")
    return model_file


# ── Virtual Implementation ─────────────────────────────────────────────────────
class Virtual(QubeInterface):
    """
    MuJoCo-based simulator for the Qube-Servo 3.
    
    Implements the QubeInterface using MuJoCo physics engine.
    Following MuJoCo documentation best practices:
    - Model loaded from XML file (enables asset resolution)
    - Mesh assets loaded from Virtual_model/ directory
    - Separation of visualization meshes and collision primitives

    Parameters
    ----------
    dt : Control timestep [s]. Default 0.001 s (1 kHz).
    motor_constant : Motor torque constant [Nm/V]. Default 0.05 Nm/V.
    """

    def __init__(self, dt: float = config.CONTROL_DT, motor_constant: float = config.PLANT_MOTOR_CONSTANT):
        """ Initialize the MuJoCo simulator. """
        # Initialize parrent class
        super().__init__(motor_constant)  

        # Simulator parameters
        self.dt = dt

        # LED states
        self.led_r = 0.0
        self.led_g = 0.0
        self.led_b = 0.0

        # MuJoCo objects (following docs: separate model and data)
        self.model: Optional[mujoco.MjModel] = None
        self.data: Optional[mujoco.MjData] = None
        self.viewer = None  # Reference to passive viewer (None if visualization disabled)

        # Named accessors (using modern API instead of mj_name2id)
        self.theta_joint = None
        self.alpha_joint = None
        self.motor_actuator = None

        # Set startup states for beta and alpha (arm at center, pendulum down)
        self.startup_theta = 0.0
        self.startup_alpha = 0.0

        # Timing variables for real-time control
        self.run_time = 0.0
        self.tick_time = self.dt / config.QUBE_SIMULATION_SPEED
        self.target_time = time.time()   # Target time for next step (enables catch-up if falling behind)

        if config.DEBUG: print("[Virtual] Simulator initialized")
    

    # ── Lifecycle ──────────────────────────────────────────────────────────────
    def open(self) -> None:
        """
        Load the MuJoCo model and initialize the simulator.
        
        Following MuJoCo documentation:
        1. Load mjModel from XML file (enables asset resolution)
        2. Create mjData from mjModel
        3. Find element IDs by name
        """
        try:
            # Step 1: Ensure model file exists on disk
            model_file_path = get_model_file_path()
            
            # Step 2: Load model from file (per MuJoCo docs: enables asset resolution)
            self.model = mujoco.MjModel.from_xml_path(model_file_path)
            
            # Step 3: Create data structure from model (per docs: mjData is scratch pad)
            self.data = mujoco.MjData(self.model)
            
        except Exception as e:
            raise RuntimeError(f"\nFailed to load MuJoCo model: {e}")

        # Step 4: Find joint and actuator using modern named access API (Per docs: O(1) performance)
        self.theta_joint = self.model.joint('theta')
        self.alpha_joint = self.model.joint('alpha')
        self.motor_actuator = self.model.actuator('arm_motor')

        # Step 5: Forward kinematics: Compute all body positions and orientations
        mujoco.mj_forward(self.model, self.data)

        if self.theta_joint is None or self.alpha_joint is None or self.motor_actuator is None:
            raise RuntimeError("Could not find required joints or actuators in MuJoCo model")

        if config.DEBUG: print(f"[Virtual] MuJoCo model loaded from {model_file_path}")


    def close(self) -> None:
        """
        Shut down the simulator.
        Per MuJoCo docs: Resources are automatically freed when structures go out of scope.
        """
        if self.data is not None:
            self.write(0.0)
            self.enable(False)
            self.data = None

        self.model = None
        self.viewer = None
        print("[Virtual] MuJoCo simulator closed.")


    # ── Initialization helpers ────────────────────────────────────────────────────
    def reset(self) -> None:
        """
        Reset the simulation to the initial state.
        
        Initial configuration:
        - Arm at center (theta = 0)
        - Pendulum at upright position (alpha = 0)
        - All velocities zeroed
        """
        # Reset parrent class
        super().reset()

        if self.model is None or self.data is None:
            raise RuntimeError("Simulator not open. Call open() first.")

        # Set initial generalized coordinates (qpos) using named access
        self.data.joint('theta').qpos = self.startup_theta       # theta = 0 (center)
        self.data.joint('alpha').qpos = self.startup_alpha       # alpha = 0 (upright)

        # Zero all generalized velocities (qvel)
        self.data.qvel[:] = 0.0

        # Reset target time
        self.target_time = time.time()

        print("[Virtual] Simulation reset.")


    def set_led(self, r: float, g: float, b: float) -> None:
        """Set LED state and update visualization color (thread-safe with viewer lock)."""
        self.led_r = max(0.0, min(1.0, r))
        self.led_g = max(0.0, min(1.0, g))
        self.led_b = max(0.0, min(1.0, b))

        # Per MuJoCo docs: must acquire viewer lock before modifying model state
        if config.QUBE_VISUALIZE and self.model is not None and self.viewer is not None:
            with self.viewer.lock():
                led_material = self.model.material('led')
                led_material.rgba = [self.led_r, self.led_g, self.led_b, 0.5]


    # ── Control loop ───────────────────────────────────────────────────────────
    def read(self) -> Tuple[float, float, float, float]:
        """
        Read the current simulation state without stepping physics.
        
        Per MuJoCo documentation: mj_step has already been called in write(),
        so mjData contains the current velocities (qvel) and positions (qpos).

        Returns
        -------
        theta : Arm angle [rad], 0 at center, limited to [-π/2, π/2].
        theta_dot : Arm angular velocity [rad/s].
        alpha : Pendulum angle [rad], 0 at upright, π at down. (Internally, we invert and shift the MuJoCo alpha.)
        alpha_dot : Pendulum angular velocity [rad/s].
        """
        if self.model is None or self.data is None:
            raise RuntimeError("Simulator not open. Call open() first.")

        # Get current state from mjData using named access (velocities computed by previous mj_step)
        theta = self.data.joint('theta').qpos.item()
        theta_dot = self.data.joint('theta').qvel.item()
        
        alpha_raw = self.data.joint('alpha').qpos.item()
        alpha_dot_raw = self.data.joint('alpha').qvel.item()

        # Angle convention transformation:
        alpha = math.pi - alpha_raw
        alpha_dot = -alpha_dot_raw  # Velocity sign reversal due to the inversion

        # Wrap alpha to [0, 2π)
        alpha %= (math.radians(360))

        # Clamp theta to [-π/2, π/2] (joint also limited in MJCF)
        theta = max(-math.pi / 2, min(math.pi / 2, theta))

        return theta, theta_dot, alpha, alpha_dot


    def write(self, voltage: float) -> None:
        """
        Apply a motor voltage command and advance the simulation.
        
        Per MuJoCo documentation: mj_step is the top-level function which:
        1. Applies controls to actuators
        2. Computes forward dynamics
        3. Advances state by one timestep
        4. Computes forward kinematics

        The simulator advances by one control step (dt). After this call,
        the next read() will return the updated state and velocities.

        Parameters
        ----------
        voltage : Desired motor voltage [V]. Saturated to ±10 V.
        """
        # update parrent class state
        super().write(voltage)

        # Check if model and data are initialized
        if self.model is None or self.data is None:
            raise RuntimeError("Simulator not open. Call open() first.")
        
        # Apply control: convert voltage to torque
        if self.enabled:
            torque = self.voltage_demand * self.motor_constant
        else:
            torque = 0.0

        # Set actuator control using named access
        self.data.actuator('arm_motor').ctrl = torque

        # Step the simulation
        mujoco.mj_step(self.model, self.data)

        # Update real-time timing with active catch-up
        self.run_time += self.dt
        self.target_time += self.tick_time
        self.sleep_time = self.target_time - time.time()
        if self.sleep_time > 0:
            # Ahead of schedule: Sleep to maintain timing
            time.sleep(self.sleep_time)
        elif config.DEBUG and self.sleep_time < -self.tick_time * 0.1:
            # Behind schedule: Report lag and skip sleep to catch up on next iteration
            print(f"[Control] Behind: {-self.sleep_time*1000:.1f}ms (catching up...)")
        
        # Sync viewer if active
        if self.viewer is not None:
            self.viewer.sync()