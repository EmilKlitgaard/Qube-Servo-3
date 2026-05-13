from qube import qube
from controller import controller
import time
from time import sleep
import math

T = 0.002
if __name__ == "__main__":
    q = qube()
    ctrl = controller()

    try:
        while True:
            
            start = time.perf_counter()  # start timing
            theta, alpha, theta_dot, alpha_dot = q.read() # read states
            """print(
                f"theta={theta: .3f}  alpha={alpha: .3f}  "
                f"theta_dot={theta_dot: .3f}  alpha_dot={alpha_dot: .3f}"
            )"""
            
            a_wrapped = (alpha + math.pi) % (2.0 * math.pi) - math.pi # warp pi to -pi
            #print(a_wrapped)
            if a_wrapped > 2.5 or a_wrapped < -2.5: # if pendulum is near upright
                #print("Balance controller")
                #V = ctrl.classic_pd(theta, alpha, theta_dot, alpha_dot) # control
                V = ctrl.LQR(theta, alpha, theta_dot, alpha_dot)
            else:
                #print("Swing-up controller")
                V = ctrl.swing_up(theta, alpha, theta_dot, alpha_dot) # swingup
                #V = ctrl.swing_up_work(theta, alpha, theta_dot, alpha_dot)

            #print(f"V={V:.3f}")

            q.write(V)
            
            end = time.perf_counter()  # end timing
            elapsed = end - start
            remaining = T - elapsed
            if remaining > 0:
                time.sleep(remaining)
            else:
                print("Loop overran")
          

    except KeyboardInterrupt:
        pass

    finally:
        q.close()