"""
ControlLaw.py – Control laws for the Qube-Servo 3.

Implements mode-switching between:
  1. Swing-up (energy-based) controller: brings pendulum from down to near upright
  2. Stabilization (LQR-like) controller: balances pendulum at upright and centers arm

The controller automatically switches between modes based on pendulum position/velocity.
For swing-up implementation details, see SwingUp.py
"""

import math
import time
from typing import Tuple
from .SwingUp import SwingUp
from Config import config

class Controller:
    """
    Combined swing-up and stabilization controller for the Qube-Servo 3.
    
    This class manages mode-switching between swing-up and stabilization phases.
    The actual swing-up mathematics are delegated to SwingUp class.
    
    Parameters
    ----------
    dt : Control timestep [s].
    lqr_k : list of 4 floats
        LQR feedback gains [k_theta, k_theta_dot, k_alpha, k_alpha_dot].
        Default corresponds to reasonable values for the Qube.
    """

    def __init__(self, dt: float = 0.001, lqr_k: list = None):
        self.dt = dt
        
        # Initialize swing-up controller
        self.swingup = SwingUp(dt)
        
        # Default LQR gains (tuned empirically for Qube dynamics)
        if lqr_k is None:
            self.k = [3.0, 3.0, 60.0, 5.0]  # These are reasonable stabilization gains: [k_theta, k_theta_dot, k_alpha, k_alpha_dot]
        else:
            self.k = lqr_k

        # Internal state
        self.mode = "swingup"  # "swingup" or "stabilize"


    def compute_modern_stabilize(self, theta: float, theta_dot: float, alpha: float, alpha_dot: float, theta_target: float = 0.0, alpha_target: float = 0.0) -> float:
        """
        Stabilization controller (LQR-like state feedback).
        Uses linear feedback:  u = -K * [error_theta, theta_dot, error_alpha, alpha_dot]^T
        
        Stabilizes pendulum at alpha_target and arm at theta_target.
        Handles alpha angle wrapping correctly (e.g., 359° ≈ -1° for control purposes).
        
        Parameters
        ----------
        theta, theta_dot, alpha, alpha_dot : Current state.
        theta_target : Target arm angle [rad]. Default: 0.0 (center).
        alpha_target : Target pendulum angle [rad]. Default: 0.0 (upright).
        
        Returns
        -------
        voltage : Motor voltage command [V].
        """

        # Wrap alpha to [-π, π] for correct angle error around upright
        alpha_wrapped = math.atan2(math.sin(alpha), math.cos(alpha))
        alpha_target_wrapped = math.atan2(math.sin(alpha_target), math.cos(alpha_target))
        
        # Compute errors relative to targets
        theta_error = theta - theta_target
        alpha_error = alpha_wrapped - alpha_target_wrapped
        
        # State vector: [theta_error, theta_dot, alpha_error, alpha_dot]
        state = [theta_error, theta_dot, alpha_error, alpha_dot]
        
        # Compute control: Voltage = -K * state
        voltage = sum(k_i * state_i for k_i, state_i in zip(self.k, state))
        
        # Saturate to motor limits
        voltage = max(-10.0, min(10.0, voltage))

        return voltage
    

    def compute_traditional_stabilize(self, theta: float, theta_dot: float, alpha: float, alpha_dot: float, theta_target: float = 0.0, alpha_target: float = 0.0) -> float:
        """
        Traditional PD stabilization controller.
        Similar to compute_modern_stabilize.
        
        Parameters
        ----------
        theta, theta_dot, alpha, alpha_dot : Current state.
        theta_target : Target arm angle [rad]. Default: 0.0 (center).
        alpha_target : Target pendulum angle [rad]. Default: 0.0 (upright).

        Returns
        -------
        voltage : Motor voltage command [V].
        """

        # Wrap alpha to [-π, π] for correct angle error around upright (0)
        alpha_wrapped = math.atan2(math.sin(alpha), math.cos(alpha))
    
        # PD control: u = -Kp * alpha_error - Kd * alpha_dot
        Kp = 20.0  # Proportional gain for angle error
        Kd = 1.5   # Derivative gain for angular velocity
        error = (-Kp * alpha_wrapped) - (Kd * alpha_dot)
        
        voltage = error

        return voltage


    def compute(self, theta: float, theta_dot: float, alpha: float, alpha_dot: float,
                theta_target: float = 0.0, alpha_target: float = 0.0) -> Tuple[float, str]:
        """
        Compute motor voltage and return current control mode.
        Switches between swing-up and stabilization modes based on pendulum state.
        
        Parameters
        ----------
        theta, theta_dot, alpha, alpha_dot : Current state from qube.read().
        theta_target : Target arm angle [rad]. Default: 0.0 (center).
        alpha_target : Target pendulum angle [rad]. Default: 0.0 (upright).
        
        Returns
        -------
        voltage : Motor voltage command [V], saturated to [-18, +10].
        mode : Current mode: "swingup" or "stabilize".
        """
        
        # Add small delay for debugging visualization
        time.sleep(0.001)  

        """
        # Pause if space is pressed, and wait until it is pressed again (for debugging)
        try:
            time.sleep(0.001)
        except KeyboardInterrupt:
            print("\n[Controller] Spacebar pressed. Pausing control loop. Press spacebar again to resume.")
            input("[Controller] Press Enter to resume...")
        """

        # Determine if we should switch modes
        if self.mode == "swingup":
            if self.swingup.is_upright(alpha):
                if config.DEBUG: print("[Controller] Switching to stabilization mode.")
                self.mode = "stabilize"
        else:
            if not self.swingup.is_upright(alpha):
                if config.DEBUG: print("[Controller] Pendulum fell down. Switching back to swing-up mode.")
                self.swingup.phase = self.swingup.PHASE_INIT  # Reset swing-up state machine
                self.mode = "swingup"
        
        # Compute control based on mode
        if self.mode == "swingup":
            voltage = self.swingup.compute(theta, theta_dot, alpha, alpha_dot)
        else:
            if config.QUBE_MODERN_STABILIZATION:
                voltage = self.compute_modern_stabilize(theta, theta_dot, alpha, alpha_dot, theta_target, alpha_target)
            else:
                voltage = self.compute_traditional_stabilize(theta, theta_dot, alpha, alpha_dot, theta_target, alpha_target)
        
        return voltage, self.mode