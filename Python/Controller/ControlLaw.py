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

class ControlLaw:
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
            self.k = [1.0, 1.0, 20.0, 1.5]  # These are reasonable stabilization gains: [k_theta, k_theta_dot, k_alpha, k_alpha_dot]
        else:
            self.k = lqr_k

        # Internal state
        self.mode = "swingup"  # "swingup" or "stabilize"


    def compute_stabilize(self, theta: float, theta_dot: float, alpha: float, alpha_dot: float) -> float:
        """
        Stabilization controller (LQR-like state feedback).
        Uses linear feedback:  u = -K * [theta, theta_dot, alpha, alpha_dot]^T
        
        Stabilizes pendulum at alpha=0 (upright) and arm at theta=0 (center).
        Handles alpha angle wrapping correctly (e.g., 359° ≈ -1° for control purposes).
        
        Parameters
        ----------
        theta, theta_dot, alpha, alpha_dot : Current state.
        
        Returns
        -------
        voltage : Motor voltage command [V].
        """
        # Wrap alpha to [-π, π] for correct angle error around upright (0)
        # This ensures 359° becomes -1° (error of -1°, not +359°)
        alpha_wrapped = math.atan2(math.sin(alpha), math.cos(alpha))
        
        # State vector: [theta, theta_dot, alpha_wrapped, alpha_dot]
        state = [theta, theta_dot, alpha_wrapped, alpha_dot]
        
        # Compute control: Voltage = K * state
        voltage = sum(k_i * state_i for k_i, state_i in zip(self.k, state))
        
        # Saturate to motor limits
        voltage = max(-10.0, min(10.0, voltage))

        return voltage


    def compute(self, theta: float, theta_dot: float, alpha: float, alpha_dot: float) -> Tuple[float, str]:
        """
        Compute motor voltage and return current control mode.
        Switches between swing-up and stabilization modes based on pendulum state.
        
        Parameters
        ----------
        theta, theta_dot, alpha, alpha_dot : Current state from qube.read().
        
        Returns
        -------
        voltage : Motor voltage command [V], saturated to [-18, +18].
        mode : Current mode: "swingup" or "stabilize".
        """
        
        # Add small delay for debugging visualization
        time.sleep(0.001)  

        # Determine if we should switch modes
        if self.mode == "swingup":
            if self.swingup.is_upright(alpha):
                if config.DEBUG: print("[ControlLaw] Switching to stabilization mode.")
                self.mode = "stabilize"
        else:
            if not self.swingup.is_upright(alpha):
                if config.DEBUG: print("[ControlLaw] Pendulum fell down. Switching back to swing-up mode.")
                self.swingup.phase = self.swingup.PHASE_INIT  # Reset swing-up state machine
                self.mode = "swingup"
        
        # Compute control based on mode
        if self.mode == "swingup":
            voltage = self.swingup.compute(theta, theta_dot, alpha, alpha_dot)
        else:
            voltage = self.compute_stabilize(theta, theta_dot, alpha, alpha_dot)
        
        return voltage, self.mode
