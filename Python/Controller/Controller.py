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

    def __init__(self, dt: float = 0.001, lqr_k: list = [3.0, 3.0, 60.0, 5.0]):
        self.dt = dt
        self.k = lqr_k
        
        # Initialize swing-up controller
        self.swingup = SwingUp(dt)        

        # Internal state
        self.mode = "swingup"  # "swingup" or "stabilize"
        
    def torque_to_voltage(self, torque: float, theta_dot: float) -> float:
        # V = R/kt * torque + Ke * theta_dot
       
        voltage = (config.PLANT_MOTOR_RESISTANCE / config.PLANT_TORQUE_CONSTANT) * torque + (config.PLANT_MOTOR_CONSTANT * theta_dot)
        return max(config.CONTROL_VOLTAGE_MIN, min(config.CONTROL_VOLTAGE_MAX, voltage))  # Saturate to limits



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

        return voltage
    

    def compute_classic_stabilize(self, theta: float, theta_dot: float, alpha: float, alpha_dot: float, theta_target: float = 0.0, alpha_target: float = 0.0) -> float:
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

        # Compute errors
        alpha_error = alpha_wrapped - alpha_target
        theta_error = theta - theta_target
    
        # PD control: u = -Kp * alpha_error - Kd * alpha_dot
        # decent vals = 49, 5.0, 3, 3
        Kp = 0.225  # Proportional gain for angle error
        Kd = 0.015   # Derivative gain for angular velocity
        Kp_theta = 0.01875  # Proportional gain for arm angle error
        Kd_theta = 0.003  # Derivative gain for arm angular velocity  
        torque = (Kp * alpha_error) + (Kd * alpha_dot) + (Kp_theta * theta_error) + (Kd_theta * theta_dot)  # Add arm stabilization terms
        voltage = self.torque_to_voltage(torque, theta_dot)

        return voltage


    def compute(self, theta: float, theta_dot: float, alpha: float, alpha_dot: float, theta_target: float = 0.0, alpha_target: float = 0.0) -> Tuple[float, str]:
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
        """
        if theta > math.radians(100) or theta < math.radians(-100):
            #if config.DEBUG: 
            print("[Controller] Arm exceeded ±100 degrees. Switching back to swing-up mode.")
            self.swingup.phase = self.swingup.PHASE_INIT # Reset swing-up phase
            self.mode = "swingup"
             # Delay to prevent immediate re-triggering
            for i in range (1, 1000):
                    print()
        """

        if self.mode == "swingup":
            # Compute swing-up voltage
            voltage = self.swingup.compute(theta, theta_dot, alpha, alpha_dot)

            # Check if we are close enough to upright to switch to stabilization
            if self.swingup.is_far_upright(alpha):
                if config.DEBUG: print("[Controller] Switching to stabilization mode.")
                self.mode = "stabilize"
        else:
            # Compute stabilization voltage
            if config.CONTROL_MODERN_STABILIZATION:
                voltage = self.compute_modern_stabilize(theta, theta_dot, alpha, alpha_dot, theta_target, alpha_target)
            else:
                voltage = self.compute_classic_stabilize(theta, theta_dot, alpha, alpha_dot, theta_target, alpha_target)
            
            # Check if pendulum has fallen down during stabilization
            if not self.swingup.is_upright(alpha):
                if config.DEBUG: print("[Controller] Pendulum fell down. Switching back to swing-up mode.")
                self.swingup.phase = self.swingup.PHASE_INIT # Reset swing-up phase
                self.mode = "swingup"

        # Saturate voltage to motor limits
        voltage = max(config.CONTROL_VOLTAGE_MIN, min(config.CONTROL_VOLTAGE_MAX, voltage))

        return voltage, self.mode