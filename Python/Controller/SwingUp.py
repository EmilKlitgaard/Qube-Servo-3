"""
SwingUp.py – State machine swing-up controller for the Qube-Servo 3.

"""

import math
import time
from Config import config
import numpy as np

class SwingUp:
    """
    Energy based swing-up controller for the Qube-Servo 3.
    """
    
    def __init__(self):
        # Phase parameters
        self.up_threshold = 5      # Threshold for considering pendulum upright (degrees from vertical)
        self.down_threshold = 45    # Threshold for considering pendulum down (degrees from vertical)
        self.force_start = True


    def is_upright(self, alpha: float) -> bool:
        """Check if pendulum is near upright (within 30 degrees)."""
        is_upright_position = alpha < math.radians(self.up_threshold) or alpha > math.radians(360-self.up_threshold)
        return is_upright_position
    

    def is_down(self, alpha: float) -> bool:
        """Check if pendulum is near down."""
        is_down_position = alpha < math.radians(self.down_threshold) or alpha > math.radians(360-self.down_threshold)
        return not is_down_position


    def wrap_to_pi(self, x):
        return (x + math.pi) % (2.0 * math.pi) - math.pi


    def swing_up(self, theta: float, theta_dot: float, alpha: float, alpha_dot: float) -> float:
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
        
        # Parameters 
        self.multiplier = 70
        self.mp = 0.024
        self.lp = 0.129
        self.g = 9.82
        self.jp = (1/3) * self.mp * self.lp**2
        
        alpha1 = self.wrap_to_pi(alpha)
        alpha1 = alpha1 - math.pi
    
        E = 0.5 * self.jp * alpha_dot**2 + self.mp * self.g * self.lp * (1.0 - math.cos(alpha1))
        Er = 2.0 * self.mp * self.g * self.lp

        s = alpha_dot * math.cos(alpha1)
        if theta < math.radians(-10) or theta > math.radians(10):
            self.force_start = False

        if s > -0.01 or self.force_start:
            direction = -1.0
        else:
            direction = 1.0
        
        V = self.multiplier * (E - Er) * direction
                        
        voltage = max(min(V, config.CONTROL_VOLTAGE_MAX), config.CONTROL_VOLTAGE_MIN)
            
        #print(f"voltage: {voltage:.2f}")
        return voltage 