from platform import Physical, Virtual
from controller.Controller import PendulumController

ctrl = PendulumController()

# qube = Physical()                   # Real hardware
qube = Virtual(speed=0.1)             # Simulation (0.1 = 10× slower)

with qube:
    qube.reset()
    qube.set_led(0, 1, 0)
    qube.enable(True)
    try:
        while True:
            voltage = ctrl.step(*qube.read())
            qube.write(voltage)
    except KeyboardInterrupt:
        print("\nStopped.")