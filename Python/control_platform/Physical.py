import sys
import math
import numpy as np

try:
    from quanser.hardware import HIL
    _QUANSER_AVAILABLE = True
except ImportError:
    _QUANSER_AVAILABLE = False

from Config import config
from .QubeInterface import QubeInterface


# ── DSP helpers ───────────────────────────────────────────────────────────────

def _ddt_filter(u: float, state: np.ndarray, A: float, Ts: float):
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
_COUNTS_TO_RAD = 2.0 * math.pi / 512.0 / 4.0


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

    def __init__(self, dt: float = config.CONTROL_DT, filter_bw: float = 100.0):
        self._freq    = 1.0 / dt
        self._Ts      = dt
        self._filt_bw = filter_bw

        self._card    = None
        self._task    = None

        # Read buffers
        self._ana_buf = np.zeros(len(_ANA_R), dtype=np.float64)
        self._enc_buf = np.zeros(len(_ENC_R), dtype=np.int32)
        self._dig_buf = np.zeros(len(_DIG_R), dtype=np.int8)
        self._oth_buf = np.zeros(len(_OTH_R), dtype=np.float64)

        # Derivative filter state  [u_prev, y_prev]
        self._ddt_state = np.zeros(2, dtype=np.float64)

        self.theta_target = 0.0


    # ── lifecycle ─────────────────────────────────────────────────────────────
    def open(self) -> None:
        if not _QUANSER_AVAILABLE:
            raise RuntimeError(
                "The Quanser SDK is not installed on this machine.\n"
                "Physical hardware is only supported on Windows 10/11 (64-bit) and Ubuntu 24.04+.\n"
                "  Windows installer: https://github.com/quanser/quanser_sdk_win64/releases\n"
                "  Linux instructions: https://github.com/quanser/quanser_sdk_linux\n"
                "On macOS, use Virtual() instead."
            )
        self._card = HIL("qube_servo3_usb", "0")
        print("[Physical] HIL card opened.")


    def close(self) -> None:
        if self._card is None:
            return
        self.write(0.0)
        self.set_led(1.0, 0.0, 0.0)
        self.enable(False)
        if self._task is not None:
            try:
                self._card.task_stop(self._task)
                self._card.task_delete(self._task)
            except Exception:
                pass
            self._task = None
        self._card.close()
        self._card = None
        print("[Physical] HIL card closed.")


    # ── initialisation helpers ─────────────────────────────────────────────────
    def reset(self) -> None:
        self._card.set_encoder_counts(
            _ENC_R, len(_ENC_R), np.zeros(len(_ENC_R), dtype=np.int32)
        )
        self._ddt_state[:] = 0.0


    def set_target(self, theta: float, alpha: float) -> None:        
        """Set the target state for the controller (not used in this implementation)."""
        # This method is not used in this implementation, but we could write
        # target angles to the OTH_W channels if needed for advanced control strategies.
    

    def set_led(self, r: float, g: float, b: float) -> None:
        self._card.write_other(
            _OTH_W, len(_OTH_W), np.array([r, g, b], dtype=np.float64)
        )


    def enable(self, on: bool) -> None:
        # Always zero the voltage before toggling the amplifier
        self._card.write_analog(
            _ANA_W, len(_ANA_W), np.zeros(len(_ANA_W), dtype=np.float64)
        )
        self._card.write_digital(
            _DIG_W, len(_DIG_W), np.array([1 if on else 0], dtype=np.int8)
        )


    # ── timed task (lazy-start) ────────────────────────────────────────────────
    def _start_task(self, samples: int = 2**32 - 1) -> None:
        self._task = self._card.task_create_reader(
            1000,
            _ANA_R, len(_ANA_R),
            _ENC_R, len(_ENC_R),
            _DIG_R, len(_DIG_R),
            _OTH_R, len(_OTH_R),
        )
        self._card.task_start(self._task, 0, self._freq, samples)


    # ── control loop ──────────────────────────────────────────────────────────
    def read(self) -> tuple[float, float]:
        if self._task is None:
            self._start_task()
        self._card.task_read(
            self._task, 1,
            self._ana_buf, self._enc_buf, self._dig_buf, self._oth_buf,
        )
        theta = _COUNTS_TO_RAD * float(self._enc_buf[0])
        theta_dot, self._ddt_state = _ddt_filter(
            theta, self._ddt_state, self._filt_bw, self._Ts
        )
        return theta, theta_dot


    def write(self, voltage: float) -> None:
        v = max(min(voltage, 18.0), -18.0)
        self._card.write_analog(
            _ANA_W, len(_ANA_W), np.array([v], dtype=np.float64)
        )
