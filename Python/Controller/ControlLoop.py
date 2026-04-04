"""
Controller.py – Main control loop for the Qube-Servo 3.

This module provides the primary entry point for running the control system.
It works with both Physical and Virtual backends via the QubeInterface abstraction.

Example usage:
    from control_platform import Virtual
    from controller.Controller import run_controller
    
    with Virtual() as qube:
        run_controller(qube, duration=30.0)
"""

import time
import math

from Config import config
from controller import Controller
from control_platform import QubeInterface


def update_led(theta: float, theta_dot: float, alpha: float, alpha_dot: float, mode: str, iteration: int, qube: QubeInterface) -> None:
    """ Update the RGB LED based on the current mode and state. """
    # LED feedback based on mode
    if mode == "swingup":
        qube.set_led(1.0, 0.5, 0.0)  # Orange: swinging up
    else:
        if on_target(theta, theta_dot, alpha, alpha_dot, qube.target_theta, qube.target_alpha):
            qube.set_led(0.0, 1.0, 0.0)  # Green: stabilized
        else:
            if iteration % 5 == 0:  # Flash Blue: moving to target
                qube.set_led(0.0, 0.0, 0.0)  # Off
            else:
                qube.set_led(0.0, 0.0, 1.0)  # Blue


def on_target(theta: float, theta_dot: float, alpha: float, alpha_dot: float, theta_target: float = 0.0, alpha_target: float = 0.0) -> bool:
    """
    Check if the system is on target (pendulum upright and arm centered) and all joints are stationary.
    
    Parameters
    ----------
    theta : Arm angle [rad].
    theta_dot : Arm angular velocity [rad/s].
    alpha : Pendulum angle [rad].
    alpha_dot : Pendulum angular velocity [rad/s].
    theta_target : Target arm angle [rad]. Default: 0.0 (center).
    alpha_target : Target pendulum angle [rad]. Default: 0.0 (upright).

    Returns
    -------
    bool : True if on target, False otherwise.
    """

    # Correctly handle alpha angle wrapping (e.g., 359° ≈ -1° for control purposes)
    alpha = alpha % (math.radians(360))
    
    # Define thresholds for being "on target"
    theta_threshold = math.radians(2)       # 2 degrees
    alpha_threshold = math.radians(2)       # 2 degrees
    theta_dot_threshold = math.radians(5)   # 5 degrees/s
    alpha_dot_threshold = math.radians(10)  # 10 degrees/s
    
    # Check if theta and alpha are within thresholds of target
    theta_on_target = abs(theta - theta_target) < theta_threshold
    alpha_on_target = abs(alpha - alpha_target) < alpha_threshold or abs(alpha - alpha_target - math.radians(360)) < alpha_threshold
    
    # Check if angular velocities are low (near stationary)
    theta_dot_on_target = abs(theta_dot) < theta_dot_threshold
    alpha_dot_on_target = abs(alpha_dot) < alpha_dot_threshold  
    return theta_on_target and alpha_on_target and theta_dot_on_target and alpha_dot_on_target


def run_controller(qube: QubeInterface, duration: float = None) -> None:
    """
    Run the main control loop for the Qube-Servo 3.
    
    Stabilizes the pendulum upright (alpha = 0) and centers the arm (theta = 0).
    Uses a combined swing-up + LQR stabilization controller.
    
    The simulation speed is controlled via config.QUBE_SIMULATION_SPEED:
    - 1.0 = real-time (each physics step takes dt seconds in wall-clock time)
    - 0.5 = half speed (each physics step takes 2*dt seconds in wall-clock time)
    
    Parameters
    ----------
    qube : Either a Virtual (MuJoCo) or Physical (real hardware) interface.
    duration : Maximum runtime [s]. If None, runs until interrupted. Default: None.
    """
    
    # Initialize controller
    controller = Controller()
    
    # Initialize hardware
    qube.reset()
    qube.set_led(1.0, 1.0, 0.0)  # Yellow: initializing
    qube.enable(True)
    
    if config.DEBUG:
        print("[Control] Starting control loop...")
        print(f"[Control] Physics timestep: {controller.dt * 1000:.1f} ms")
        print(f"[Control] Simulation speed: {config.QUBE_SIMULATION_SPEED}x")
        print(f"[Control] Wall-clock timestep: {controller.dt * 1000 / config.QUBE_SIMULATION_SPEED:.1f} ms")
        print(f"[Control] Duration: {duration if duration is not None else 'unlimited'} s\n")
    
    # Initialize visualizer if enabled (only for Virtual simulator)
    viewer = None
    if config.QUBE_SIMULATION and config.QUBE_VISUALIZE:
        try:
            import mujoco.viewer
            if config.DEBUG: print("[Control] Launching MuJoCo viewer...")
            # Launch passive viewer with model and data from qube
            viewer = mujoco.viewer.launch_passive(qube.model, qube.data)
            qube.viewer = viewer
            if config.DEBUG: print("[Control] Viewer launched.\n")
        except Exception as e:
            print(f"[Control] Warning: Could not launch viewer: {e}")
            print(f"[Control] On macOS, ensure you run via 'mjpython' launcher.\n")
            viewer = None

    # Await for enter to start control loop
    input("\nPress ENTER to start control loop...")
    qube.reset() # Reset again to reset time
    
    # Control loop
    try:
        # Timing variables for real-time control
        iteration = 0

        while True:
            # Check exit condition
            if duration is not None and qube.run_time > duration:
                if config.DEBUG: print(f"[Control] Duration of {duration} s reached. Exiting control loop.")
                break

            # Check if viewer is still running
            if viewer is not None and not viewer.is_running():
                if config.DEBUG: print("[Control] Viewer window closed.")
                break
            
            # Read current state
            theta, theta_dot, alpha, alpha_dot = qube.read()
            
            # Compute control from controller
            voltage, mode = controller.compute(theta, theta_dot, alpha, alpha_dot, qube.target_theta, qube.target_alpha)
            
            # Apply control
            qube.write(voltage)
            
            # Update LED based on current state and mode
            update_led(theta, theta_dot, alpha, alpha_dot, mode, iteration, qube)
            
            # Increment iteration counter
            iteration += 1
            
            # Periodic status output
            if config.DEBUG and (iteration % 100) == 0:
                print(f"[{qube.run_time:.2f}s] \tTheta: {math.degrees(theta):+.4f}°, \talpha: {math.degrees(alpha):+.4f}°, \tvoltage: {voltage:+.2f}V, \tmode: {mode}")

        if config.DEBUG: print(f"\n[Control] Control loop completed after {qube.run_time:.2f} s (simulation time)")
    
    except KeyboardInterrupt:
        if config.DEBUG: print("\n[Control] Interrupted by user (Ctrl+C)")
    
    finally:
        # Close viewer if active
        if viewer is not None:
            viewer.close()
        
        # Shutdown sequence
        if config.DEBUG: print("[Control] Shutting down...")
        qube.write(0.0)
        qube.set_led(1.0, 0.0, 0.0)  # Red: shutdown
        qube.enable(False)
        qube.close()
        if config.DEBUG: print("[Control] Done.")