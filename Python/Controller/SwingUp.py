"""
SwingUp.py – State machine swing-up controller for the Qube-Servo 3.

This module implements the swing-up phase of the control strategy using a
multi-step state machine that follows these steps:

1. Move arm to -90 degrees (theta = -π/2)
2. Wait for pendulum swing to settle (alpha_dot < 5 degrees/s)
3. Move arm to +10 degrees at max speed (theta = +10 degrees)
4. Wait for pendulum to reach bottom (alpha = 0)
5. Move arm back to center (theta = 0)
6. Exit when pendulum reaches near upright (alpha between 135-225 degrees)
"""

import math
import time
from Config import config
import numpy as np

class SwingUp:
    """
    State machine swing-up controller for the Qube-Servo 3.
    
    Implements a precise multi-step sequence to swing the pendulum from down to upright:
    1. Position arm at -90° to prepare for initial swing
    2. Wait for pendulum velocity to settle
    3. Move arm rapidly to +10° to impart large impulse
    4. Return arm to center while pendulum swings upward
    5. Transition to stabilization when pendulum reaches near-upright
    
    Parameters
    ----------
    dt : Control timestep [s]. Default: 0.001 s.
    """
    
    PHASE_INIT = 0                # Move to -90 degrees
    PHASE_WAIT_SWING = 1          # Wait for swing to settle
    PHASE_RAPID_MOVE = 2          # Move to +10 degrees
    PHASE_WAIT_BOTTOM = 3         # Wait for alpha to reach target
    PHASE_RETURN_CENTER = 4       # Move back to center
    PHASE_EXIT = 5                # Ready to transition to stabilization

    SWINGUP_SEQUENCE = 1
    
    def __init__(self, dt: float = config.CONTROL_DT):
        self.dt = dt
        self.phase = self.PHASE_INIT
        
        # Phase parameters
        self.alpha_dot_threshold = math.radians(10)         # 10 degrees/s in radians/s
        self.far_up_threshold = 10      # Threshold for considering pendulum upright (degrees from vertical)
        self.up_threshold = 45          # Threshold for considering pendulum down (degrees from vertical)
        self.down_threshold = 10
        self.target_theta = 10          # Target arm angle for swing-up phases (updated dynamically)
    

    def is_far_upright(self, alpha: float) -> bool:
        """Check if pendulum is near upright (within 10 degrees)."""
        # Check if pendulum is near upright (within 10 degrees)
        is_far_upright_position = alpha < math.radians(self.far_up_threshold) or alpha > math.radians(360-self.far_up_threshold)
        return is_far_upright_position
    

    def is_upright(self, alpha: float) -> bool:
        """Check if pendulum is near upright (within 30 degrees)."""
        is_upright_position = alpha < math.radians(self.up_threshold) or alpha > math.radians(360-self.up_threshold)
        return is_upright_position
    

    def is_down(self, alpha: float) -> bool:
        """Check if pendulum is near down."""
        # Check if pendulum is near down (within 10 degrees)
        is_down_position = alpha < math.radians(180+self.down_threshold) and alpha > math.radians(180-self.down_threshold)
        return is_down_position
    

    def compute(self, theta: float, theta_dot: float, alpha: float, alpha_dot: float) -> float:
        """
        State machine swing-up controller.
        
        Executes the following sequence:
        Phase 0 (INIT): Move arm to -90 degrees
        Phase 1 (WAIT_SWING): Wait for pendulum velocity < 5 degrees/s
        Phase 2 (RAPID_MOVE): Move arm to +10 degrees at max speed
        Phase 3 (WAIT_BOTTOM): Wait for pendulum at bottom position
        Phase 4 (RETURN_CENTER): Move arm back to 0 degrees
        Phase 5 (EXIT): Check if upright; if yes, exit to stabilization
        
        Parameters
        ----------
        theta : Arm angle [rad], 0 at center, ±π/2 at limits
        theta_dot : Arm angular velocity [rad/s]
        alpha : Pendulum angle [rad]
        alpha_dot : Pendulum angular velocity [rad/s]
        
        Returns
        -------
        voltage : Motor voltage command [V], saturated to [-18, +18]
        """
        
        voltage = 0.0
        
        if self.SWINGUP_SEQUENCE == 0:
            match self.phase:
                # Phase 0: Move arm to -90 degrees (-π/2 ≈ -1.571 rad)
                case self.PHASE_INIT:
                    target_theta = -math.radians(45)
                    error = target_theta - theta
                    
                    if abs(error) < 0.05:  # Within 0.05 rad of target
                        self.phase = self.PHASE_WAIT_SWING
                        voltage = 0.0
                    else:
                        # Proportional feedback to reach target
                        voltage = 2.0 * error
            
                # Phase 1: Await for pendulum swing to settle, while holding arm at -90 degrees
                case self.PHASE_WAIT_SWING:
                    target_theta = -math.radians(45)
                    error = target_theta - theta
                    
                    # Check if pendulum swing has settled
                    if self.is_down(alpha) and abs(alpha_dot) < self.alpha_dot_threshold:
                        self.phase = self.PHASE_RAPID_MOVE
                        voltage = 0.0
                    else:
                        # Hold position
                        voltage = 2.0 * error
                
                # Phase 2: Rapidly move arm to +10 degrees at max speed
                case self.PHASE_RAPID_MOVE:
                    target_theta = math.radians(45)  # +10 degrees in radians
                    error = target_theta - theta
                    
                    if abs(error) < 0.05:  # Within 0.05 rad of target
                        self.phase = self.PHASE_WAIT_BOTTOM
                        voltage = 0.0
                    else:
                        voltage = 10.0
                
                # Phase 3: Await for pendulum to reach bottom position (alpha close to π)
                case self.PHASE_WAIT_BOTTOM:
                    target_theta = math.radians(45)  # +10 degrees in radians
                    error = target_theta - theta
                    
                    # Wait for pendulum to reach bottom region (alpha close to π)            
                    if self.is_down(alpha):
                        self.phase = self.PHASE_RETURN_CENTER
                        voltage = 0.0
                    else:
                        # Gently move toward center
                        voltage = 2.0 * error
                
                # Phase 4: Return arm to center (theta = 0)
                case self.PHASE_RETURN_CENTER:
                    target_theta = 0.0
                    error = target_theta - theta
                    
                    if abs(error) < 0.05:
                        self.phase = self.PHASE_EXIT
                        voltage = 0.0
                    else:
                        # Return to center
                        voltage = -10.0
                
                # Phase 5: Check if pendulum has reached upright region
                case self.PHASE_EXIT:
                    target_theta = 0.0
                    error = target_theta - theta

                    if self.is_upright(alpha):
                        # Successfully exited swing-up
                        voltage = 0.0
                    else:
                        # If not upright, await pendulum to reach bottom position.
                        voltage = 10.0 * error
                        if self.is_down(alpha) and abs(alpha_dot) < self.alpha_dot_threshold:
                            self.phase = self.PHASE_INIT  # If not upright, go back to waiting for bottom
        
        elif self.SWINGUP_SEQUENCE == 1:
            match self.phase:
                # Phase 0: Rapidly move arm to -10 degrees at max speed
                case self.PHASE_INIT:
                    target_theta = -math.radians(self.target_theta)
                    error = target_theta - theta
                    
                    if abs(error) < 0.05:  # Within 0.005 rad of target
                        self.phase = self.PHASE_WAIT_SWING
                    else:
                        voltage = 10.0 * (error / abs(error)) if error != 0 else 0.0  # Move at max speed in direction of error
            
                # Phase 1: Await for pendulum to reach bottom position (alpha close to π)
                case self.PHASE_WAIT_SWING:
                    target_theta = -math.radians(self.target_theta)
                    error = target_theta - theta
                    
                    # Wait for pendulum to reach bottom region (alpha close to π)            
                    if self.is_down(alpha) and alpha_dot > 0:
                        self.phase = self.PHASE_RAPID_MOVE
                    else:
                        # Gently move toward target (Previus 2.0)
                        voltage = 10.0 * error
                
                # Phase 2: Rapidly move arm to +10 degrees at max speed
                case self.PHASE_RAPID_MOVE:
                    target_theta = math.radians(self.target_theta)
                    error = target_theta - theta
                    
                    if abs(error) < 0.05:  # Within 0.005 rad of target
                        self.phase = self.PHASE_WAIT_BOTTOM
                    else:
                        voltage = 10.0 * (error / abs(error)) if error != 0 else 0.0  # Move at max speed in direction of error
                
                # Phase 3: Await for pendulum to reach bottom position (alpha close to π)
                case self.PHASE_WAIT_BOTTOM:
                    target_theta = math.radians(self.target_theta)
                    error = target_theta - theta
                    
                    # Wait for pendulum to reach bottom region (alpha close to π)            
                    if self.is_down(alpha) and alpha_dot < 0:
                        self.phase = self.PHASE_INIT
                    else:
                        # Gently move toward target (Previus 2.0)
                        voltage = 10.0 * error

        elif self.SWINGUP_SEQUENCE == 2:
            # Parameters 
            self.multiplier = 100
            self.mp = 0.024
            self.lp = 0.129
            self.g = 9.82
            self.jp = (1/3) * self.mp * self.lp**2

            # Energy-based swing-up control
            E = 0.5 * self.jp * alpha_dot**2 + self.mp * self.g * self.lp * (1.0 - math.cos(alpha-math.pi))
            Er = 2.0 * self.mp * self.g * self.lp
            print(f"[SwingUp] Energy: {E:.4f} J, Target Energy: {Er:.4f} J")
            s = alpha_dot * math.cos(alpha-math.pi)
            voltage = self.multiplier * (E - Er) * (-1.0 if s > 0.0 else 1.0)
    
        # Print info for debugging in degrees
        if config.DEBUG: print(f"[SwingUp] Phase: {self.phase}, theta: {math.degrees(theta):.1f}°, theta_dot: {math.degrees(theta_dot):.1f}°/s, alpha: {math.degrees(alpha):.1f}°, alpha_dot: {math.degrees(alpha_dot):.1f}°/s")
        
        #self.theta_dot_lst = np.append(self.theta_dot_lst, math.degrees(theta_dot))
        #print(np.mean(self.theta_dot_lst[-1000:]))  # Print average of last 100 theta_dot values for debugging
        #voltage = 2.0
        return voltage