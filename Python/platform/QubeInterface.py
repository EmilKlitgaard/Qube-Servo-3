from abc import ABC, abstractmethod


class QubeInterface(ABC):
    """
    Abstract interface for the Quanser QUBE-Servo 3.

    Both Physical and Virtual implement every method identically so they
    are drop-in replacements for each other.

    Typical usage
    -------------
    with Physical() as qube:          # or Virtual()
        qube.reset()
        qube.set_led(0, 1, 0)
        qube.enable(True)
        while running:
            theta, theta_dot = qube.read()
            voltage = my_controller(theta, theta_dot)
            qube.write(voltage)
    """

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

    @abstractmethod
    def set_led(self, r: float, g: float, b: float) -> None:
        """
        Set the RGB LED.

        Parameters
        ----------
        r, g, b : float
            Each channel in the range 0.0 – 1.0.
        """

    @abstractmethod
    def enable(self, on: bool) -> None:
        """Enable (True) or disable (False) the motor amplifier."""

    # ── control loop ──────────────────────────────────────────────────────────

    @abstractmethod
    def read(self) -> tuple[float, float]:
        """
        Sample the current state.

        Returns
        -------
        theta     : float   Motor shaft angle [rad]
        theta_dot : float   Motor shaft angular velocity [rad/s]
        """

    @abstractmethod
    def write(self, voltage: float) -> None:
        """
        Apply a motor voltage.

        The implementation saturates the value to ±18 V (amplifier limit).
        """
