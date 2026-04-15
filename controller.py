import math


class controller:
    def __init__(self):
        # PD gains
        self.Kp_alpha = 35.0
        self.Kd_alpha = 2.0

        self.Kp_theta = 3.0
        self.Kd_theta = 0.5

        self.max_voltage = 10.0
        
        # swing-up gain
        self.Ke = 50.0
        
        # parameters
        self.mp = 0.024          
        self.lp = 0.129        
        self.g = 9.81           
        self.jp = (1/3) * self.mp * self.lp**2

    def wrap_to_pi(self, x): # warp to [-pi, pi]
        return (x + math.pi) % (2.0 * math.pi) - math.pi

    def classic_pd(self, theta, alpha, theta_dot, alpha_dot):
        # error relative to upright
        alpha_err = self.wrap_to_pi(alpha - math.pi)

        # PD control 
        V = (
            self.Kp_alpha * alpha_err
            + self.Kd_alpha * alpha_dot
            + self.Kp_theta * theta
            + self.Kd_theta * theta_dot
        )

        # clamp voltage
        V = max(min(V, self.max_voltage), -self.max_voltage)

        return V
    
    def swing_up(self, theta, alpha, theta_dot, alpha_dot):

        alpha = self.wrap_to_pi(alpha)
        
        if abs(alpha) > 0.2 and abs(alpha_dot) > 0.01:
            

            # Pendulum energy:
            E = 0.5 * self.jp * alpha_dot**2 + self.mp * self.g * self.lp * (1.0 - math.cos(alpha))

            # Reference energy at upright
            Er = 2.0 * self.mp * self.g * self.lp

            direction = 0.0
            s = alpha_dot * math.cos(alpha)
            if s > 0.0:
                direction = -1.0
            elif s < 0.0:
                direction = 1.0

            V = self.Ke * (E - Er) * direction

        else:
            if theta <= 0.0:
                V = 5.0
            elif theta > 0.0:
                V = -5.0
                

        return max(min(V, self.max_voltage), -self.max_voltage)
    
    