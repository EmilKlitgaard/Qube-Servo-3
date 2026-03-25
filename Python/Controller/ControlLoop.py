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


def on_target(theta: float, theta_dot: float, alpha: float, alpha_dot: float) -> bool:
    """
    Check if the system is on target (pendulum upright and arm centered) and all joints are stationary.
    
    Parameters
    ----------
    theta : Arm angle [rad].
    theta_dot : Arm angular velocity [rad/s].
    alpha : Pendulum angle [rad].
    alpha_dot : Pendulum angular velocity [rad/s].

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
    
    # Check if theta and alpha are within thresholds of target (0 for both)
    theta_on_target = abs(theta) < theta_threshold
    alpha_on_target = abs(alpha) < alpha_threshold or abs(alpha - 2 * math.pi) < alpha_threshold
    
    # Check if angular velocities are low (near stationary)
    theta_dot_on_target = abs(theta_dot) < theta_dot_threshold
    alpha_dot_on_target = abs(alpha_dot) < alpha_dot_threshold  
    return theta_on_target and alpha_on_target and theta_dot_on_target and alpha_dot_on_target


def run_controller(qube: QubeInterface, duration: float = None) -> None:
    """
    Run the main control loop for the Qube-Servo 3.
    
    Stabilizes the pendulum upright (alpha = 0) and centers the arm (theta = 0).
    Uses a combined swing-up + LQR stabilization controller.
    
    Parameters
    ----------
    qube : Either a Virtual (MuJoCo) or Physical (real hardware) interface.
    duration : Maximum runtime [s]. If None, runs until interrupted. Default: None.
    """
    
    # Initialize visualizer if requested (only for Virtual simulator)
    viewer = None
    if config.QUBE_SIMULATION and config.QUBE_VISUALIZE:
        try:
            import mujoco.viewer
            if config.DEBUG: print("[Control] Launching MuJoCo viewer...")
            viewer = mujoco.viewer.launch_passive(qube.model, qube.data)
            if config.DEBUG: print("[Control] Viewer launched.")
        except Exception as e:
            print(f"[Control] Warning: Could not launch viewer: {e}")
            viewer = None
    
    # Initialize controller
    controller = Controller()
    
    # Initialize hardware
    qube.reset()
    qube.set_led(1.0, 1.0, 0.0)  # Yellow: initializing
    qube.enable(True)
    
    if config.DEBUG:
        print("[Control] Starting control loop...")
        print(f"[Control] Control timestep: {controller.dt * 1000:.1f} ms")
        print(f"[Control] Duration: {duration if duration is not None else 'unlimited'} s\n")
    
    input("\nPress ENTER to start control loop...") # Await for enter to start control loop
    
    # Control loop
    try:
        # Initialize timing
        t = 0.0
        iteration = 0
        start_time = time.time()

        while True:
            # Check exit condition
            if duration is not None and t > duration:
                if config.DEBUG: print(f"[Control] Duration of {duration} s reached. Exiting control loop.")
                break
            
            # Check if viewer is still running (passive mode)
            if viewer is not None and not viewer.is_running():
                if config.DEBUG: print("[Control] Viewer window closed.")
                break
            
            # Read current state
            theta, theta_dot, alpha, alpha_dot = qube.read()

            # Wrap alpha to [0, 2π)
            alpha = alpha % (math.radians(360))
            
            # Compute control
            voltage, mode = controller.compute(theta, theta_dot, alpha, alpha_dot)
            
            # Apply control
            qube.write(voltage)
            
            # Sync viewer if active (user responsible for syncing in passive mode)
            if viewer is not None:
                viewer.sync()
            
            # Update elapsed time
            t = time.time() - start_time
            iteration += 1
            
            # Periodic status output
            if config.DEBUG and (iteration % 100) == 0:
                print(f"[{t:.2f}s] Theta: {math.degrees(theta):+.4f}°, alpha: {math.degrees(alpha):+.4f}°, voltage: {voltage:+.2f}V, mode: {mode}")
            
            # LED feedback based on mode
            if mode == "swingup":
                qube.set_led(1.0, 0.5, 0.0)  # Orange: swinging up
            else:
                if on_target(theta, theta_dot, alpha, alpha_dot):
                    qube.set_led(0.0, 1.0, 0.0)  # Green: stabilized
                else:
                    if iteration % 5 == 0:  # Flash Blue: moving to target
                        qube.set_led(0.0, 0.0, 0.0)  # Off
                    else:
                        qube.set_led(0.0, 0.0, 1.0)  # Blue

        if config.DEBUG: print(f"\n[Control] Control loop completed after {t:.2f} s")
    
    except KeyboardInterrupt:
        if config.DEBUG: print("\n[Control] Interrupted by user (Ctrl+C)")
    
    finally:
        # Close viewer if active
        if viewer is not None:
            try:
                viewer.close()
            except:
                pass
        
        # Shutdown sequence
        if config.DEBUG: print("[Control] Shutting down...")
        qube.write(0.0)
        qube.set_led(1.0, 0.0, 0.0)  # Red: shutdown
        qube.enable(False)
        qube.close()
        if config.DEBUG: print("[Control] Done.")