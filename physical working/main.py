from qube import qube
from controller import controller

import time
import math

T = 0.002
settle_hold = 0.5


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
                    if now - stable_since >= settle_hold:
                        recovery_time = now - recovery_start

                        print(
                            f"Recovered and stabilized in "
                            f"{recovery_time:.3f} s"
                        )

                        recovery_active = False
                        recovery_start = None
                        stable_since = None
                        ready_for_knockdown = True

                elif not ready_for_knockdown:
                    if now - stable_since >= settle_hold:
                        ready_for_knockdown = True

                        print(
                            "Pendulum stabilized. "
                            "Push it to time the next recovery."
                        )

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

            elapsed = time.perf_counter() - start
            remaining = T - elapsed

            if remaining > 0:
                time.sleep(remaining)
            else:
                print("Loop overran")

    except KeyboardInterrupt:
        pass

    finally:
        q.close()