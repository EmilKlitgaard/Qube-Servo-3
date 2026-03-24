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
from control_platform import QubeInterface
from .ControlLaw import ControlLaw
from Config import config

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
    control_law = ControlLaw()
    
    # Initialize hardware
    qube.reset()
    qube.set_led(1.0, 1.0, 0.0)  # Yellow: initializing
    qube.enable(True)
    
    if config.DEBUG:
        print("[Control] Starting control loop...")
        print(f"[Control] Control timestep: {control_law.dt * 1000:.1f} ms")
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

            # Wrap alpha to [0, 2π) - handles any magnitude of rotation
            alpha = alpha % (math.radians(360))
            
            # Compute control
            voltage, mode = control_law.compute(theta, theta_dot, alpha, alpha_dot)
            
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
                # Blink green when stabilized and balanced
                if (iteration % 20) < 10:
                    qube.set_led(0.0, 1.0, 0.0)  # Green: stabilized
                else:
                    qube.set_led(0.0, 0.5, 0.0)  # Dim green
        
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