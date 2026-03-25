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
import mujoco

from Config import config
from typing import Tuple, Optional
from control_platform import QubeInterface
from controller import Controller, SwingUp


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

    def __init__(self, dt: float = 0.001, motor_constant: float = 0.05):
        """Initialize the MuJoCo simulator."""
        self.dt = dt
        self.motor_constant = motor_constant
        self.enabled = False
        self.voltage_demand = 0.0

        # LED state
        self.led_r = 0.0
        self.led_g = 0.0
        self.led_b = 0.0

        # MuJoCo objects (following docs: separate model and data)
        self.model: Optional[mujoco.MjModel] = None
        self.data: Optional[mujoco.MjData] = None

        # Joint indices (found after model load)
        self.theta_joint_id: Optional[int] = None
        self.alpha_joint_id: Optional[int] = None
        self.motor_actuator_id: Optional[int] = None

        # Set startup states for beta and alpha (arm at center, pendulum down)
        self.startup_theta = 0.0
        self.startup_alpha = 0.0


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

        # Step 4: Find joint and actuator IDs by name (Per docs: mj_name2id maps element names to integer ids)
        self.theta_joint_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "theta")
        self.alpha_joint_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "alpha")
        self.motor_actuator_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, "arm_motor")

        if self.theta_joint_id < 0 or self.alpha_joint_id < 0 or self.motor_actuator_id < 0:
            raise RuntimeError("Could not find required joints or actuators in MuJoCo model")

        if config.DEBUG:
            print(f"[Virtual] MuJoCo model loaded from {model_file_path}")
            print(f"[Virtual] Found theta_id={self.theta_joint_id}, alpha_id={self.alpha_joint_id}, motor_id={self.motor_actuator_id}")


    def close(self) -> None:
        """
        Shut down the simulator.
        
        Per MuJoCo docs: resources are automatically freed when structures go out of scope, but explicit cleanup is good practice.
        """
        if self.data is not None:
            self.write(0.0)
            self.enable(False)
        self.model = None
        self.data = None
        print("[Virtual] MuJoCo simulator closed.")


    # ── Initialization helpers ────────────────────────────────────────────────────
    def reset(self) -> None:
        """
        Reset the simulation to the initial state.
        
        Per MuJoCo docs:
        - qpos: generalized coordinates (joint positions)
        - qvel: generalized velocities
        - mjData is the "scratch pad" for all state and intermediate results
        
        Initial configuration:
        - Arm at center (theta = 0)
        - Pendulum at down position (alpha = π in MuJoCo; 
          read() converts to 0 for control logic)
        - All velocities zeroed
        """
        if self.model is None or self.data is None:
            raise RuntimeError("Simulator not open. Call open() first.")

        # Set initial generalized coordinates (qpos)
        self.data.qpos[self.theta_joint_id] = 0.0       # theta = 0 (center)
        self.data.qpos[self.alpha_joint_id] = 0.0       # alpha = 0 (down)

        # Zero all generalized velocities (qvel)
        self.data.qvel[:] = 0.0

        # Reset internal state
        self.voltage_demand = 0.0
        self.enabled = False

        # Forward kinematics: compute all body positions and orientations
        # Per docs: this "provides the basis for all subsequent computations"
        mujoco.mj_forward(self.model, self.data)
        print("[Virtual] Simulation reset.")


    def set_led(self, r: float, g: float, b: float) -> None:
        """Set LED state and update visualization color."""
        self.led_r = max(0.0, min(1.0, r))
        self.led_g = max(0.0, min(1.0, g))
        self.led_b = max(0.0, min(1.0, b))

        if config.QUBE_VISUALIZE and self.model is not None:
            color_index = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_MATERIAL, "led")
            self.model.mat_rgba[color_index] = [self.led_r, self.led_g, self.led_b, 0.5]


    def enable(self, on: bool) -> None:
        """Enable or disable the motor."""
        if on:
            self.enabled = True
        else:
            self.enabled = False
            self.voltage_demand = 0.0


    # ── Control loop ───────────────────────────────────────────────────────────
    def read(self) -> Tuple[float, float, float, float]:
        """
        Step the simulation and return the current state.
        
        Per MuJoCo documentation: mj_step is the top-level function which:
        1. Applies controls to actuators
        2. Computes forward dynamics
        3. Advances state by one timestep
        4. Computes forward kinematics

        The simulator advances by one control step (dt). Joint velocities are
        computed as (q_new - q_old) / dt for consistency.

        Returns
        -------
        theta : Arm angle [rad], 0 at center, limited to [-π/2, π/2].
        theta_dot : Arm angular velocity [rad/s].
        alpha : Pendulum angle [rad], 0 at upright, π at down. (Internally, we invert and shift the MuJoCo alpha.)
        alpha_dot : Pendulum angular velocity [rad/s].
        """
        if self.model is None or self.data is None:
            raise RuntimeError("Simulator not open. Call open() first.")

        # Save old state
        theta_old = self.data.qpos[self.theta_joint_id]
        alpha_old = self.data.qpos[self.alpha_joint_id]

        # Apply control: convert voltage to torque
        # Per docs: actuators have gear ratios and force transmission in mjModel
        if self.enabled:
            torque = self.voltage_demand * self.motor_constant
        else:
            torque = 0.0

        # Set actuator control (gear ratio is 1.0 in MJCF, so ctrl = torque / gear)
        self.data.ctrl[self.motor_actuator_id] = torque

        # Step the simulation (per docs: top-level function advancing all computations)
        # This updates: qpos, qvel, intermediate results
        mujoco.mj_step(self.model, self.data)

        # Get new state from mjData
        theta_new = self.data.qpos[self.theta_joint_id]
        alpha_new = self.data.qpos[self.alpha_joint_id]

        # Finite-difference velocities for consistency
        theta_dot = (theta_new - theta_old) / self.dt
        # For alpha, we compute the raw velocity from MuJoCo (qvel set by mj_step)
        alpha_dot_raw = self.data.qvel[self.alpha_joint_id]

        # Angle convention transformation:
        # - MuJoCo alpha = π at down, 0 at up (standard hinge convention)
        # - Control logic expects: alpha = 0 at upright, π at down
        # So: alpha_returned = π - alpha_mujoco
        alpha_returned = math.pi - alpha_new
        # Velocity sign reversal due to the inversion
        alpha_dot = -alpha_dot_raw

        # Clamp theta to [-π/2, π/2] (joint limited in MJCF, but be safe)
        theta = max(-math.pi / 2, min(math.pi / 2, theta_new))

        return theta, theta_dot, alpha_returned, alpha_dot


    def write(self, voltage: float) -> None:
        """
        Apply a motor voltage command.

        The voltage is saturated to ±10 V and stored for the next read() call.

        Parameters
        ----------
        voltage : Desired motor voltage [V].
        """
        if self.model is None:
            raise RuntimeError("Simulator not open. Call open() first.")

        # Saturate voltage to amplifier limit
        self.voltage_demand = max(-10.0, min(10.0, voltage))