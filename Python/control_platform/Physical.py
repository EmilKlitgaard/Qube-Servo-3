import math
import numpy as np

try:
    from quanser.hardware import HIL
    QUANSER_AVAILABLE = True
except ImportError:
    QUANSER_AVAILABLE = False

from Config import config
from .QubeInterface import QubeInterface


# ── DSP helpers ───────────────────────────────────────────────────────────────

def ddt_filter(u: float, state: np.ndarray, A: float, Ts: float):
    """
    Derivative with filtering, Tustin-discretised:  y = A·s / (s + A)

    Parameters
    ----------
    u     : Current input sample.
    state : np.ndarray([u_prev, y_prev], dtype=float64) — mutated in place.
    A     : Filter bandwidth [rad/s].
    Ts    : Sample period [s].
    """
    y = (2*A*u - 2*A*state[0] - state[1]*(A*Ts - 2)) / (A*Ts + 2)
    state[0] = u
    state[1] = y
    return y, state


# ── Channel definitions (QUBE-Servo 3, HIL driver) ───────────────────────────

_ANA_R = np.array([0],               dtype=np.uint32)
_ENC_R = np.array([0, 1],            dtype=np.uint32)
_DIG_R = np.array([0, 1, 2],         dtype=np.uint32)
_OTH_R = np.array([14000, 14001],    dtype=np.uint32)

_ANA_W = np.array([0],               dtype=np.uint32)
_DIG_W = np.array([0],               dtype=np.uint32)
_OTH_W = np.array([11000, 11001, 11002], dtype=np.uint32)

# 512 PPR encoder × 4× quadrature decoding = 2048 counts/rev
COUNTS_TO_RAD = 2.0 * math.pi / 512.0 / 4.0


# ── Physical implementation ───────────────────────────────────────────────────
class Physical(QubeInterface):
    """
    QUBE-Servo 3 interface backed by the real HIL hardware via the
    Quanser Python SDK.

    Parameters
    ----------
    dt        : Control-loop timestep [s].  Drives the derivative filter.
    filter_bw : Derivative filter bandwidth [rad/s]  (default: 100 rad/s).
    """ 

    def __init__(self, dt: float = config.CONTROL_DT):
        self.counts_per_rev = 2048.0
        self.rad_per_count = 2.0 * math.pi / self.counts_per_rev

        # Read channels
        self.encoder_channels = np.array([0, 1], dtype=np.uint32)
        self.other_channels = np.array([14000, 14001], dtype=np.uint32)

        # Write channels
        self.analog_channel = np.array([0], dtype=np.uint32)
        self.digital_channel = np.array([0], dtype=np.uint32)
        self.other_write_channels = np.array([11000, 11001, 11002], dtype=np.uint32)

        # Buffers
        self.encoder_buffer = np.zeros(2, dtype=np.int32)
        self.other_buffer = np.zeros(2, dtype=np.float64)
        self.analog_buffer = np.zeros(1, dtype=np.float64)
        self.digital_buffer = np.zeros(1, dtype=np.int8)
        self.other_write_buffer = np.zeros(3, dtype=np.float64)


    # ── lifecycle ─────────────────────────────────────────────────────────────
    def open(self) -> None:
        if not QUANSER_AVAILABLE:
            raise RuntimeError(
                "The Quanser SDK is not installed on this machine.\n"
                "Physical hardware is only supported on Windows 10/11 (64-bit) and Ubuntu 24.04+.\n"
                "  Windows installer: https://github.com/quanser/quanser_sdk_win64/releases\n"
                "  Linux instructions: https://github.com/quanser/quanser_sdk_linux\n"
                "On macOS, use Virtual() instead."
            )
        
        # Open HIL card
        self.card = HIL("qube_servo3_usb", "0")
        if config.DEBUG: print("[Physical] HIL card opened.")

        # Zero encoders
        self.card.set_encoder_counts(
            self.encoder_channels,
            2,
            np.array([0, 0], dtype=np.int32)
        )

        # Initialize outputs
        self.write(0.0)

        # Set LED to green to indicate ready state
        self.set_led(0, 1, 0)


    def close(self) -> None:
        self.card.write_analog(
            self.analog_channel,
            1,
            np.array([0.0], dtype=np.float64)
        )

        self.card.write_digital(
            self.digital_channel,
            1,
            np.array([0], dtype=np.int8)
        )

        # Set LED to red to indicate shutdown
        self.set_led(1, 0, 0)

        self.card.close()


    # ── initialisation helpers ─────────────────────────────────────────────────
    def reset(self) -> None:
        # Reset parrent class
        super().reset()

        self.enable(False)  # Disable motor
    

    def set_led(self, r: float, g: float, b: float) -> None:
        self.card.write_other(
            self.other_write_channels,
            3,
            np.array([r, g, b], dtype=np.float64)
        )


    def enable(self, on: bool) -> None:
        # Update parrent class state
        super().enable(on) 

        if self.enabled:
            # Enable motor
            self.card.write_digital(
                self.digital_channel,
                1,
                np.array([1], dtype=np.int8)
            )
        else:
            # Disable motor
            self.card.write_digital(
                self.digital_channel,
                1,
                np.array([0], dtype=np.int8)
            )


    # ── control loop ──────────────────────────────────────────────────────────
    def read(self) -> tuple[float, float, float, float]:
        self.card.read(
            None, 0,
            self.encoder_channels, 2,
            None, 0,
            self.other_channels, 2,
            None,
            self.encoder_buffer,
            None,
            self.other_buffer
        )

        theta = self.encoder_buffer[0] * self.rad_per_count
        alpha = self.encoder_buffer[1] * self.rad_per_count
        theta_dot = self.other_buffer[0] * self.rad_per_count
        alpha_dot = self.other_buffer[1] * self.rad_per_count
    

        return theta, alpha, theta_dot, alpha_dot


    def write(self, voltage: float) -> None:
        # update parrent class state
        super().write(voltage)

        self.analog_buffer[0] = self.voltage_demand
        self.card.write_analog(self.analog_channel, 1, self.analog_buffer)

        # Set LED to blue when motor is active
        self.set_led(0, 0, 1) if self.enabled else self.set_led(1, 0, 0)
