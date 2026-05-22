from qube import qube
from controller import controller
from log import StepMetrics
from time import sleep

import time
import math

T = 0.002
loops = 30  # HUSK AT SÆTTE DENNE
log = True


if __name__ == "__main__":

    q = qube()
    ctrl = controller()

    if log:
        metrics = StepMetrics(
            tol=0.05,
            settle_hold=2.0,
            loop_count_max=loops
        )
    else:
        metrics = None

    balance_angle = math.radians(20)

    try:
        while True:

            start = time.perf_counter()

            theta, alpha, theta_dot, alpha_dot = q.read()

            a_wrapped = (alpha + math.pi) % (2.0 * math.pi) - math.pi

            near_upright = abs(abs(a_wrapped) - math.pi) <= balance_angle

            if near_upright:

                V = ctrl.classic_pd( theta,alpha,theta_dot,alpha_dot)
                #V = ctrl.LQR(theta, alpha, theta_dot,alpha_dot)

                if log:
                    target = math.pi if a_wrapped > 0 else -math.pi
                    alpha_error = a_wrapped - target

                    now = time.perf_counter()

                    if not metrics.active:
                        metrics.start(now, alpha_error)

                    done = metrics.update(now, alpha_error)
                    if done:
                        q.write(0.0)
                        sleep(1)  
                        

            else:

                if log and metrics.active:
                    metrics.stop()

                V = ctrl.swing_up(
                    theta,
                    alpha,
                    theta_dot,
                    alpha_dot
                )

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