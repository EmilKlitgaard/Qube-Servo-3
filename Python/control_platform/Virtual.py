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
import numpy as np

from Config import config
from typing import Tuple, Optional
from control_platform import QubeInterface

# ── Model file path ────────────────────────────────────────────────────────────
def get_model_file_path() -> str:
    """
    Get the absolute path to Qube_Servo_3.xml model file.
    """
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if config.PENDULUM_TEST_ENABLED:
        model_file = os.path.join(root_dir, "Virtual_model", "Pendulum_test.xml")
    else:
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

    def __init__(self, dt: float = config.CONTROL_DT):
        """ Initialize the MuJoCo simulator. """
        # Initialize parrent class
        super().__init__(dt)

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
        self.dt = dt
        self.run_time = 0.0
        self.tick_time = self.dt / config.QUBE_SIMULATION_SPEED
        self.target_time = time.time()   # Target time for next step (enables catch-up if falling behind)

        # Define constants:
        self.emf_constant = config.PLANT_MOTOR_CONSTANT         # Back EMF constant [V/(rad/s)]
        self.torque_constant = config.PLANT_MOTOR_CONSTANT      # Torque constant [Nm/V]
        self.motor_resistance = config.PLANT_MOTOR_RESISTANCE   # Motor resistance [Ohm]

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

        # [OPTIONAL] Pendulum test setup: 
        if config.PENDULUM_TEST_ENABLED:
            # Set initial joint positions
            self.pendulum_angle = math.radians(config.PENDULUM_TEST_START_ANGLE)
            self.data.joint('alpha').qpos = math.pi                 # Start with pendulum up
            self.data.joint('pendulum').qpos = self.pendulum_angle  # Set pendulum start angle

            # Get geom IDs for contact force measurement
            self.pendulum_disturbance_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "disturbance_capsule")
            self.pendulum_target_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "impact_target")

            # Define state variables for pendulum test
            self.pendulum_locked = True
            self.pendulum_release_time = None
            self.pendulum_reset_time = None
            self.pendulum_joint = self.data.joint("pendulum")
            self.contact_force = np.zeros(6, dtype=np.float64)
            self.pendulum_total_impulse = 0.0
            self.pendulum_peak_force = 0.0
            self.pendulum_dt = self.model.opt.timestep

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
        - Pendulum at down position (alpha = 0)
        - All velocities zeroed
        """
        if self.model is None or self.data is None:
            raise RuntimeError("Simulator not open. Call open() first.")
        
        # Ensure motor is disabled during reset
        self.enable(False)

        # Set initial generalized coordinates (qpos) using named access
        self.data.joint('theta').qpos = self.startup_theta       # theta = 0 (center)
        self.data.joint('alpha').qpos = self.startup_alpha       # alpha = 0 (down)

        # Zero all generalized velocities (qvel)
        self.data.qvel[:] = 0.0

        # Reset target time
        self.target_time = time.time()

        # [OPTIONAL] Pendulum test: Set alpha and pendulum positions 
        if config.PENDULUM_TEST_ENABLED:
            # Reset joint positions
            self.data.joint('alpha').qpos = math.pi                 # Start with pendulum up
            self.data.joint('pendulum').qpos = self.pendulum_angle  # Set pendulum start angle

            # Lock pendulum in place
            self.pendulum_locked = True
            self.pendulum_release_time = time.time() + 5            # Release after 5 seconds

        print("[Virtual] Simulation reset.")


    def enable(self, on) -> None:    
        if on:
            self.enabled = True
        else:
            self.enabled = False
            self.voltage_demand = 0.0


    def set_led(self, r: float, g: float, b: float) -> None:
        """Set LED state and update visualization color (thread-safe with viewer lock)."""
        # Update internal state
        super().set_led(r, g, b)  

        # Per MuJoCo docs: must acquire viewer lock before modifying model state
        if config.QUBE_VISUALIZE and self.model is not None and self.viewer is not None:
            with self.viewer.lock():
                led_material = self.model.material('led')
                led_material.rgba = [self.led_r, self.led_g, self.led_b, 0.5]


    # ── Control loop ───────────────────────────────────────────────────────────
    def read(self) -> tuple[float, float, float, float]:
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
        def energy_reached(self, alpha: float, alpha_dot: float) -> bool:
            """Check if pendulum has reached target energy for swing-up."""
            # Parameters 
            mp = 0.024
            lp = 0.129
            g = 9.82
            jp = (1/3) * mp * lp**2

            alpha %= (math.radians(360))
            mechanical_energy = 0.5 * jp * alpha_dot**2 + mp * g * (0.5 * lp * (1.0 - math.cos(alpha)))
            target_energy = mp * g * lp
            print(f"[SwingUp] Energy: {mechanical_energy:.4f} J, Target Energy: {target_energy:.4f} J")
            return mechanical_energy >= target_energy
        
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
            # Joint velocity
            theta_dot = self.data.joint('theta').qvel.item()

            # Back EMF
            emf_voltage = self.emf_constant * theta_dot

            # Motor current
            motor_current = (self.voltage_demand - emf_voltage) / self.motor_resistance

            # Motor torque
            torque = self.motor_constant * motor_current
        else:
            torque = 0.0

        # Set actuator control using named access
        self.data.actuator('arm_motor').ctrl = torque

        # [OPTIONAL] Energy test: Lock theta in place once pendulum reaches target energy for swing-up
        if config.ENERGY_TEST:
            if energy_reached(self, self.data.joint('alpha').qpos.item(), self.data.joint('alpha').qvel.item()):
                while True:
                    time.sleep(0.01)
                    # Lock theta at current position
                    self.data.joint('theta').qpos = self.data.joint('theta').qpos.item()
                    self.data.joint('theta').qvel = 0.0
                    self.data.actuator('arm_motor').ctrl = 0.0
                    mujoco.mj_step(self.model, self.data)
                    self.viewer.sync()

        # [OPTIONAL] Pendulum test:
        if config.PENDULUM_TEST_ENABLED:
            if self.pendulum_release_time is not None and self.pendulum_release_time < time.time():
                self.pendulum_locked = False
                self.pendulum_release_time = None

            if self.pendulum_reset_time is not None and self.pendulum_reset_time < time.time():
                self.pendulum_locked = True
                self.pendulum_reset_time = None

            if self.pendulum_locked:
                self.data.joint('pendulum').qvel = 0.0
                self.data.joint('pendulum').qpos = self.pendulum_angle

            for i in range(self.data.ncon):
                contact = self.data.contact[i]
                g1 = contact.geom1
                g2 = contact.geom2
                if ((g1 == self.pendulum_disturbance_id and g2 == self.pendulum_target_id) or (g2 == self.pendulum_disturbance_id and g1 == self.pendulum_target_id)):
                    mujoco.mj_contactForce(self.model, self.data, i, self.contact_force)
                    normal_force = abs(self.contact_force[0])
                    impulse = normal_force * self.pendulum_dt
                    self.pendulum_total_impulse += impulse
                    if normal_force > self.pendulum_peak_force:
                        self.pendulum_peak_force = normal_force
                    print(f"Impact force: {normal_force:.2f} N | Impulse: {self.pendulum_total_impulse:.4f} Ns | Peak force: {self.pendulum_peak_force:.2f} N")
                    self.pendulum_reset_time = time.time() + 0.5 # Reset pendulum 0.5s after impact

        # Step the simulation
        mujoco.mj_step(self.model, self.data)
        
        # Sync viewer if active
        if self.viewer is not None:
            self.viewer.sync()

        # Update real-time timing with active catch-up
        self.run_time += self.dt
        self.target_time += self.tick_time
        self.sleep_time = self.target_time - time.time()
        if self.sleep_time > 0:
            # Ahead of schedule: Sleep to maintain timing
            time.sleep(self.sleep_time)
        elif config.DEBUG and self.sleep_time < -self.tick_time * 0.1:
            # Behind schedule: Report lag and skip sleep to catch up on next iteration
            #print(f"[Control] Behind: {-self.sleep_time*1000:.1f}ms (catching up...)")
            pass