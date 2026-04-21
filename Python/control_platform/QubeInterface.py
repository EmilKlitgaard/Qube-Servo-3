import math
import time
from abc import ABC, abstractmethod

from Config import config


class QubeInterface(ABC):
    """
    Abstract interface for the Quanser QUBE-Servo 3.

    Both Physical and Virtual implement every method identically so they are drop-in replacements for each other.

    Typical usage
    -------------
    with Physical() as qube:          # or Virtual()
        qube.reset()
        qube.set_led(0, 1, 0)
        qube.enable(True)
        while running:
            theta, theta_dot, alpha, alpha_dot = qube.read()
            voltage = my_controller(theta, theta_dot, alpha, alpha_dot)
            qube.write(voltage)
    """
    def __init__(self, dt: float, motor_constant: float = config.PLANT_MOTOR_CONSTANT) -> None:
        """Initialize parrent class."""
        # Control state
        self.enabled = False
        self.voltage_demand = 0.0
        self.motor_constant = motor_constant

        # Timing variables for real-time control
        self.dt = dt
        self.run_time = 0.0
        self.tick_time = self.dt / config.QUBE_SIMULATION_SPEED
        self.target_time = time.time()   # Target time for next step (enables catch-up if falling behind)

        # Target state
        self.target_theta = 0.0
        self.target_alpha = 0.0

        # LED states
        self.led_r = 0.0
        self.led_g = 0.0
        self.led_b = 0.0

        # Flag for starting control loop (used in GUI mode to wait for user input)
        self.loop_running = False

        if config.DEBUG: print(f"[QubeInterface] Parrent class initialized...")
        

    # ── context manager support ────────────────────────────────────────────────
    def __enter__(self):
        self.open()
        return self


    def __exit__(self, *_):
        self.close()


    # ── lifecycle ─────────────────────────────────────────────────────────────
    @abstractmethod
    def open(self) -> None:
        """Open / initialise the hardware or simulator."""


    @abstractmethod
    def close(self) -> None:
        """Shut down cleanly — zero voltage, release all resources."""


    # ── initialisation helpers ─────────────────────────────────────────────────
    @abstractmethod
    def reset(self) -> None:
        """Zero encoder counts (Physical) or simulation state (Virtual)."""

    
    def await_start(self) -> None:
        """Wait for user input to start control loop."""
        if config.GUI_ENABLED and not config.QUBE_VISUALIZE:
            while not self.loop_running:
                if config.DEBUG: print("[QubeInterface] Waiting for GUI start command...")
                time.sleep(0.1)
        else:
            input("\nPress ENTER to start control loop...")

        # Initialize hardware
        self.reset()
        self.enable(True)


    def set_target(self, theta: float, alpha: float) -> None:
        """Set the target state for the controller (not used in this implementation)."""
        self.target_theta = theta
        self.target_alpha = alpha
        if config.DEBUG: print(f"[Virtual] New target: theta={math.degrees(theta):.1f}°, alpha={math.degrees(alpha):.1f}°")


    @abstractmethod
    def enable(self, on: bool) -> None:
        """Enable (True) or disable (False) the motor amplifier."""


    @abstractmethod
    def set_led(self, r: float, g: float, b: float) -> None:
        """Set the RGB LED."""
        self.led_r = max(0.0, min(1.0, r))
        self.led_g = max(0.0, min(1.0, g))
        self.led_b = max(0.0, min(1.0, b))


    # ── control loop ──────────────────────────────────────────────────────────
    @abstractmethod
    def read(self) -> tuple[float, float, float, float]:
        """
        Sample the current state.

        Returns
        -------
        theta     : float   Arm angle                      [rad]
        theta_dot : float   Arm angular velocity           [rad/s]
        alpha     : float   Pendulum angle (0=down, π=up)  [rad]
        alpha_dot : float   Pendulum angular velocity      [rad/s]
        """


    @abstractmethod
    def write(self, voltage: float) -> None:
        """
        Apply a motor voltage.

        The implementation saturates the value to ±18 V (amplifier limit).
        """

        # Store and saturate voltage to amplifier limit
        self.voltage_demand = max(config.CONTROL_VOLTAGE_MIN, min(config.CONTROL_VOLTAGE_MAX, voltage))

        # Update real-time timing with active catch-up
        self.run_time += self.dt
        self.target_time += self.tick_time
        self.sleep_time = self.target_time - time.time()
        if self.sleep_time > 0:
            # Ahead of schedule: Sleep to maintain timing
            time.sleep(self.sleep_time)
        elif config.DEBUG and self.sleep_time < -self.tick_time * 0.1:
            # Behind schedule: Report lag and skip sleep to catch up on next iteration
            print(f"[Control] Behind: {-self.sleep_time*1000:.1f}ms (catching up...)")
