"""
SwingUp.py - State machine swing-up controller for the Qube-Servo 3.
"""

import math
from Config import config

class SwingUp:
    """
    State machine swing-up controller for the Qube-Servo 3.
    
    Parameters
    ----------
    dt : Control timestep [s]. Default: 0.001 s.
    """
    
    def __init__(self, dt: float = config.CONTROL_DT):
        self.dt = dt
        self.phase = self.PHASE_INIT
        
        # Phase parameters
        self.up_threshold = 5       # Threshold for considering pendulum upright (degrees from vertical)
        self.down_threshold = 45    # Threshold for considering pendulum down (degrees from vertical)
        self.target_theta = 10      # Target arm angle for swing-up phases (updated dynamically)
    

    def is_upright(self, alpha: float) -> bool:
        """Check if pendulum is near upright (within 30 degrees)."""
        is_upright_position = alpha < math.radians(self.up_threshold) or alpha > math.radians(360-self.up_threshold)
        return is_upright_position
    

    def is_down(self, alpha: float) -> bool:
        """Check if pendulum is near down."""
        # Check if pendulum is near down (within 10 degrees)
        is_down_position = alpha > math.radians(self.down_threshold) and alpha < math.radians(360-self.down_threshold)
        return is_down_position
    

    def compute(self, theta: float, theta_dot: float, alpha: float, alpha_dot: float) -> float:
        """
        State machine swing-up controller.
        
        Parameters
        ----------
        theta : Arm angle [rad], 0 at center, ±π/2 at limits
        theta_dot : Arm angular velocity [rad/s]
        alpha : Pendulum angle [rad]
        alpha_dot : Pendulum angular velocity [rad/s]
        
        Returns
        -------
        voltage : Motor voltage command [V], saturated to [-10, +10]
        """
        
        voltage = 0.0
        
        # Parameters 
        self.multiplier = 1000
        self.mp = 0.024
        self.lp = 0.129
        self.g = 9.82
        self.jp = (1/3) * self.mp * self.lp**2

        # Energy-based swing-up control
        E = 0.5 * self.jp * alpha_dot**2 + self.mp * self.g * (0.5 * self.lp * (1.0 - math.cos(alpha-math.pi)))
        Er = 2* self.mp * self.g * self.lp
        if config.DEBUG: print(f"[SwingUp] Energy: {E:.4f} J, Target Energy: {Er:.4f} J")
        s = alpha_dot * math.cos(alpha-math.pi)
        voltage = self.multiplier * (E - Er) * (-1.0 if s > 0.0 else 1.0)
    
        # Print info for debugging in degrees
        if config.DEBUG: print(f"[SwingUp] Phase: {self.phase}, theta: {math.degrees(theta):.1f}°, theta_dot: {math.degrees(theta_dot):.1f}°/s, alpha: {math.degrees(alpha):.1f}°, alpha_dot: {math.degrees(alpha_dot):.1f}°/s")
        
        return voltage