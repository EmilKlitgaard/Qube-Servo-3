from qube import qube
from controller import controller
from log import log_recovery

import time
import math

def on_target(theta, alpha, theta_dot, alpha_dot):
    # Define thresholds for being "on target"
    theta_target = 0.0
    alpha_target = math.pi
    target_threshold = math.radians(10)     # 10 degrees
    alpha_dot_threshold = math.radians(10)  # 10 degrees/s
    
    # Small helper: shortest signed angular difference
    def angle_diff(a, b):
        return (a - b + math.pi) % (2.0 * math.pi) - math.pi

    # Check if theta and alpha are within thresholds of target (accounting for wrap)
    theta_on_target = abs(angle_diff(theta, theta_target)) < target_threshold
    alpha_on_target = abs(angle_diff(alpha, alpha_target)) < target_threshold

    # Check if angular velocities are low (near stationary)
    theta_dot_on_target = abs(theta_dot) < alpha_dot_threshold
    alpha_dot_on_target = abs(alpha_dot) < alpha_dot_threshold

    return theta_on_target and alpha_on_target and theta_dot_on_target and alpha_dot_on_target


if __name__ == "__main__":

    q = qube()
    ctrl = controller()

    balance_angle = math.radians(20)
    recovery_start = None
    stable_since = None
    ready_for_knockdown = False
    recovery_active = False

    try:
        while True:
            start = time.perf_counter()

            theta, alpha, theta_dot, alpha_dot = q.read()

            a_wrapped = (alpha + math.pi) % (2.0 * math.pi) - math.pi

            near_upright = abs(abs(a_wrapped) - math.pi) <= balance_angle

            if near_upright:
                V = ctrl.classic_pd( theta,alpha,theta_dot,alpha_dot)
                #V = ctrl.LQR(theta, alpha, theta_dot,alpha_dot)

                now = time.perf_counter()

                if stable_since is None:
                    stable_since = now

                if recovery_active:
                    if on_target(theta, alpha, theta_dot, alpha_dot):
                        recovery_time = now - recovery_start
                        recovery_active = False
                        recovery_start = None
                        stable_since = None
                        ready_for_knockdown = True
                        print(f"Recovered and stabilized in {recovery_time:.3f}s")
                        try:
                            idx = log_recovery(recovery_time)
                            print(f"Logged recovery as #{idx}")
                        except Exception as e:
                            print(f"Failed to log recovery: {e}")

                elif not ready_for_knockdown:
                    if on_target(theta, alpha, theta_dot, alpha_dot):
                        ready_for_knockdown = True
                        print("Pendulum stabilized. Push it to time the next recovery.")

            else:
                stable_since = None

                V = ctrl.swing_up(
                    theta,
                    alpha,
                    theta_dot,
                    alpha_dot
                )

                if ready_for_knockdown and not recovery_active:
                    recovery_active = True
                    recovery_start = time.perf_counter()
                    print("Pendulum knocked down. Timing recovery...")

            q.write(V)

    except KeyboardInterrupt:
        pass

    finally:
        q.close()