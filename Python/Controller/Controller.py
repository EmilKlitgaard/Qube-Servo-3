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
        LQR feedback gains [k_alpha, k_alpha_dot, k_theta, k_theta_dot].
        Default corresponds to reasonable values for the Qube.
    """

    def __init__(self, lqr_k: list = [37.1, 1.9, 4.3, 1]):
        self.k = lqr_k
        
        # Initialize swing-up controller
        self.swingup = SwingUp()        

        # Internal state
        self.mode = "swingup"  # "swingup" or "stabilize"

        # [OPTIONAL] Specification test: 
        if config.SPECIFICATION_TEST_ENABLED:
            self.specification_finished = False
            self.specification_direction = None
            self.specification_start_angle = 20.0       # Starting angle for test (when entering stabilization mode) in degrees
            self.specification_target_angle = 2.0       # Target angle for success (+/- 2 degrees from upright)
            self.specification_settling_time = None     # Measured settling time (from start of stabilizing to on target)
            self.specification_overshoot = 0.0          # Measured overshoot angle (start_angle_deg / overshoot_angle_deg * 100)
            self.specification_rise_time = None         # Measured rise time (from 10% to 90% of target when entering stabilization mode)
            self.specification_rise_time_start = None   # Time when we first reach 10% of target angle
            self.specification_rise_time_10 = self.specification_start_angle - (self.specification_start_angle * 0.1)  # 10% of target angle
            self.specification_rise_time_90 = self.specification_start_angle - (self.specification_start_angle * 0.9)  # 90% of target angle
            self.specification_on_target_time = None    # Time when we first get on target (for settling time measurement)
            self.swingup.up_threshold = self.specification_start_angle  # Override swing-up threshold to start stabilization at the desired test angle
            print(f"[Specification Test] Starting angle: {self.swingup.up_threshold}°, 10% rise time: {self.specification_rise_time_10:.1f}°, 90% rise time: {self.specification_rise_time_90:.1f}°")


    def check_specification_test(self, alpha: float) -> None:
        if self.specification_settling_time is not None:
            if not self.specification_finished:
                # Rise time: Start at 10% of target angle and end at 90% of target angle
                if self.specification_rise_time_start is None and self.specification_rise_time is None:
                    if self.specification_direction == -1 and alpha > math.radians(180) and alpha > math.radians(360 - self.specification_rise_time_10):
                        self.specification_rise_time_start = time.time()
                        print(f"[Specification Test] Rise time start: {self.specification_rise_time_start-self.specification_settling_time:.2f}s")
                    elif self.specification_direction == 1 and alpha < math.radians(180) and alpha < math.radians(self.specification_rise_time_10):
                        self.specification_rise_time_start = time.time()
                        print(f"[Specification Test] Rise time start: {self.specification_rise_time_start-self.specification_settling_time:.2f}s")
                elif self.specification_rise_time is None:
                    if self.specification_direction == -1 and alpha > math.radians(180) and alpha > math.radians(360 - self.specification_rise_time_90):
                        self.specification_rise_time = time.time() - self.specification_rise_time_start
                        print(f"[Specification Test] Rise time end: {self.specification_rise_time:.2f}s")
                    elif self.specification_direction == 1 and alpha < math.radians(180) and alpha < math.radians(self.specification_rise_time_90):
                        self.specification_rise_time = time.time() - self.specification_rise_time_start
                        print(f"[Specification Test] Rise time end: {self.specification_rise_time:.2f}s")

                # Overshoot:
                if self.specification_direction == -1:
                    if alpha > self.specification_overshoot and alpha < math.radians(180):
                        self.specification_overshoot = alpha
                        print(f"[Specification Test] New overshoot 1: {math.degrees(self.specification_overshoot):.1f}°")
                elif self.specification_direction == 1:
                    if abs((alpha - math.radians(360))) > self.specification_overshoot and alpha > math.radians(180):
                        self.specification_overshoot = abs((alpha - math.radians(360)))
                        print(f"[Specification Test] New overshoot 2: {math.degrees(self.specification_overshoot):.1f}°")

                # Setteling time:
                alpha_threshold = math.radians(self.specification_target_angle)
                alpha_on_target = alpha < alpha_threshold or abs(alpha - math.radians(360)) < alpha_threshold
                if alpha_on_target and self.specification_on_target_time is None:
                    self.specification_on_target_time = time.time()
                    print(f"[Specification Test] On target at time: {self.specification_on_target_time-self.specification_settling_time:.2f}s")
                elif not alpha_on_target:
                    self.specification_on_target_time = None

                if self.specification_on_target_time is not None:
                    if (time.time() - self.specification_on_target_time) >= 1:
                        self.specification_finished = True
                    else:
                        print(f"[Specification Test] Currently on target for {time.time() - self.specification_on_target_time:.2f}s")
            
            else:
                rise_time = self.specification_rise_time if self.specification_rise_time is not None else float('inf')
                total_settling_time = self.specification_on_target_time - self.specification_settling_time
                overshoot_pct = (math.degrees(self.specification_overshoot) / self.specification_start_angle) * 100  # Convert overshoot to percentage of starting angle
                print(f"[Specification Test] FINISHED: Rise time: {rise_time:.2f}s, Settling time: {total_settling_time:.2f}s, Overshoot: {overshoot_pct:.2f}%")
                
                # Reset variables
                self.specification_finished = False
                self.specification_rise_time = None
                self.specification_rise_time_start = None
                self.specification_settling_time = None
                self.specification_on_target_time = None
                self.specification_overshoot = 0.0


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

        # Optimal physical values: 35.0, 1.0, 3.0, 0.5
        # Optimal virtual values: 37.1, 1.9, 4.3, 1

        # Wrap alpha to [-π, π] for correct angle error around upright
        alpha_wrapped = math.atan2(math.sin(alpha), math.cos(alpha))
        alpha_target_wrapped = math.atan2(math.sin(alpha_target), math.cos(alpha_target))
        
        # Compute errors relative to targets
        alpha_error = alpha_wrapped - alpha_target_wrapped
        theta_error = theta - theta_target
        
        # State vector: [alpha_error, alpha_dot, theta_error, theta_dot]
        state = [alpha_error, alpha_dot, theta_error, theta_dot]
        
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
    
        # Optimal physical values: 35.0, 1.0, 3.0, 0.5
        # Optimal virtual values: 39.3, 2.56, 3.0, 0.5
        Kp = 39.3  # Proportional gain for angle error
        Kd = 2.56   # Derivative gain for angular velocity
        Kp_theta = 3.0  # Proportional gain for arm angle error
        Kd_theta = 0.5  # Derivative gain for arm angular velocity  
        voltage = (Kp * alpha_error) + (Kd * alpha_dot) + (Kp_theta * theta_error) + (Kd_theta * theta_dot)  

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

        if self.mode == "swingup":
            # Compute swing-up voltage
            voltage = self.swingup.swing_up(theta, theta_dot, alpha, alpha_dot)

            # Check if we are close enough to upright to switch to stabilization
            if self.swingup.is_upright(alpha):
                self.mode = "stabilize"
                if config.DEBUG: print("[Controller] Switching to stabilization mode.")

                # [OPTIONAL] Specification test: Start measuring settling time and overshoot when entering stabilization mode
                if config.SPECIFICATION_TEST_ENABLED:
                    print(f"[Specification Test] Starting specification test...")
                    self.specification_direction = 1 if alpha < math.radians(180) else -1
                    self.specification_settling_time = time.time()
        else:
            # Compute stabilization voltage
            if config.CONTROL_MODERN_STABILIZATION:
                voltage = self.compute_modern_stabilize(theta, theta_dot, alpha, alpha_dot, theta_target, alpha_target)
            else:
                voltage = self.compute_classic_stabilize(theta, theta_dot, alpha, alpha_dot, theta_target, alpha_target)
            
            # Check if pendulum has fallen down during stabilization
            if self.swingup.is_down(alpha):
                self.mode = "swingup"
                if config.DEBUG: print("[Controller] Pendulum fell down. Switching back to swing-up mode.")

            # [OPTIONAL] Specification test: Check for rise-time, settling-time and overshoot
            if config.SPECIFICATION_TEST_ENABLED:
                self.check_specification_test(alpha)

        return voltage, self.mode