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

from Config import config

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
    
    def __init__(self, dt: float = 0.001):
        self.dt = dt
        self.phase = self.PHASE_INIT
        self.phase_time = 0.0
        
        # Phase parameters
        self.alpha_dot_threshold = math.radians(10)         # 10 degrees/s in radians/s
    

    def is_upright(self, alpha: float) -> bool:
        """
        Check if pendulum is in the upright region for exiting swing-up.
        
        Pendulum is considered upright when:
        - |alpha| < 0.5 rad (within ~28 degrees of upright)
        - |alpha_dot| < 2.0 rad/s (moving slowly)
        
        Parameters
        ----------
        alpha : Pendulum angle [rad]
        alpha_dot : Pendulum angular velocity [rad/s]
        
        Returns
        -------
        bool : True if ready to exit swing-up and go to stabilization
        """
        # Check if pendulum is near upright (within 45 degrees)
        is_upright_position = alpha < math.radians(25) or alpha > math.radians(335)
        
        return is_upright_position
    

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
        
        self.phase_time += self.dt
        voltage = 0.0
        
        match self.phase:
            # Phase 0: Move arm to -90 degrees (-π/2 ≈ -1.571 rad)
            case self.PHASE_INIT:
                target_theta = -math.radians(90)
                error = target_theta - theta
                
                if abs(error) < 0.05:  # Within 0.05 rad of target
                    self.phase = self.PHASE_WAIT_SWING
                    self.phase_time = 0.0
                    voltage = 0.0
                else:
                    # Proportional feedback to reach target
                    voltage = 2.0 * error
        
            # Phase 1: Await for pendulum swing to settle, while holding arm at -90 degrees
            case self.PHASE_WAIT_SWING:
                target_theta = -math.radians(90)
                error = target_theta - theta
                
                # Check if pendulum swing has settled
                if alpha < math.radians(185) and alpha > math.radians(175) and abs(alpha_dot) < self.alpha_dot_threshold:
                    self.phase = self.PHASE_RAPID_MOVE
                    self.phase_time = 0.0
                    voltage = 0.0
                else:
                    # Hold position
                    voltage = 2.0 * error
            
            # Phase 2: Rapidly move arm to +10 degrees at max speed
            case self.PHASE_RAPID_MOVE:
                target_theta = math.radians(10)  # +10 degrees in radians
                error = target_theta - theta
                
                if abs(error) < 0.05:  # Within 0.05 rad of target
                    self.phase = self.PHASE_WAIT_BOTTOM
                    self.phase_time = 0.0
                    voltage = 0.0
                else:
                    voltage = 8.0
            
            # Phase 3: Await for pendulum to reach bottom position (alpha close to π)
            case self.PHASE_WAIT_BOTTOM:
                target_theta = math.radians(10)  # +10 degrees in radians
                error = target_theta - theta
                
                # Wait for pendulum to reach bottom region (alpha close to π)            
                if alpha < math.radians(185) and alpha > math.radians(175):
                    self.phase = self.PHASE_RETURN_CENTER
                    self.phase_time = 0.0
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
                    self.phase_time = 0.0
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
                    voltage = 10.0 * error
                    if alpha < math.radians(185) and alpha > math.radians(175) and abs(alpha_dot) < self.alpha_dot_threshold:
                        self.phase = self.PHASE_INIT  # If not upright, go back to waiting for bottom
            
        # Saturate voltage to amplifier limits
        voltage = max(-10.0, min(10.0, voltage))

        # print info for debugging in degrees
        print(f"[SwingUp] Phase: {self.phase}, theta: {math.degrees(theta):.1f}°, alpha: {math.degrees(alpha):.1f}°, alpha_dot: {math.degrees(alpha_dot):.1f}°/s")
        
        return voltage