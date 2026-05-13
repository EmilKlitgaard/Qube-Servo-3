import math


class controller:
    def __init__(self):
        # PD gains
        self.Kp_alpha = 39.0
        self.Kd_alpha = 2.6

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

        # LQR gain 
        self.K_lqr = [3.0, 35.6839, 0.5, 1]

    def wrap_to_pi(self, x):
        return (x + math.pi) % (2.0 * math.pi) - math.pi

    def saturate(self, V):
        return max(min(V, self.max_voltage), -self.max_voltage)

    def LQR(self, theta, alpha, theta_dot, alpha_dot):
        alpha_err = self.wrap_to_pi(alpha - math.pi)

        x = [theta, alpha_err, theta_dot, alpha_dot]

        # u = -Kx
        V = (
            self.K_lqr[0] * x[0]
            + self.K_lqr[1] * x[1]
            + self.K_lqr[2] * x[2]
            + self.K_lqr[3] * x[3]
        )

        return self.saturate(V)

    def classic_pd(self, theta, alpha, theta_dot, alpha_dot):
        alpha_err = self.wrap_to_pi(alpha - math.pi)

        V = (
            self.Kp_alpha * alpha_err
            + self.Kd_alpha * alpha_dot
            + self.Kp_theta * theta
            + self.Kd_theta * theta_dot
        )

        return self.saturate(V)
    
    def swing_up(self, theta, alpha, theta_dot, alpha_dot):
        alpha = self.wrap_to_pi(alpha)
    
        E = 0.5 * self.jp * alpha_dot**2 + self.mp * self.g * self.lp * (1.0 - math.cos(alpha))
        Er = 2.0 * self.mp * self.g * self.lp

        s = alpha_dot * math.cos(alpha)

        if s > 0.0:
            direction = -1.0
        else:
            direction = 1.0

        V = self.Ke * (E - Er) * direction                

        return self.saturate(V)
    
    def pid(self, theta, alpha, theta_dot, alpha_dot, dt):
        Kp = 30
        Kd = 1
        Ki = 1
        dt += 0.001

        alpha_err = self.wrap_to_pi(alpha - math.pi)

        if not hasattr(self, "int_alpha"):
            self.int_alpha = 0.0

        self.int_alpha += alpha_err * dt
        self.int_alpha = max(min(self.int_alpha, 0.5), -0.5)

        V = (
            Kp * alpha_err
            + Kd * alpha_dot
            + Ki * self.int_alpha
            + self.Kp_theta * theta
            + self.Kd_theta * theta_dot
        )

        return self.saturate(V)