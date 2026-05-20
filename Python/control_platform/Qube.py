import math
import time
import numpy as np

try:
    from quanser.hardware import HIL
    QUANSER_AVAILABLE = True
except ImportError:
    QUANSER_AVAILABLE = False

from Config import config


# ── Physical implementation ───────────────────────────────────────────────────
class Qube():
    """
    QUBE-Servo 3 interface backed by the real HIL hardware via the
    Quanser Python SDK.

    Parameters
    ----------
    dt: Control-loop timestep [s].  Drives the derivative filter.
    """ 

    def __init__(self, dt: float = config.CONTROL_DT):
        # Control state
        self.enabled = False
        self.voltage_demand = 0.0
        self.motor_constant = config.PLANT_MOTOR_CONSTANT

        # Target state
        self.target_theta = 0.0
        self.target_alpha = 0.0

        # LED states
        self.led_r = 0.0
        self.led_g = 0.0
        self.led_b = 0.0

        # Timing variables for real-time control
        self.dt = dt
        self.run_time = 0.0
        self.target_time = time.time()   # Target time for next step (enables catch-up if falling behind)

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


    # ── context manager support ────────────────────────────────────────────────
    def __enter__(self):
        self.open()
        return self


    def __exit__(self, *_):
        self.close()


    # ── lifecycle ─────────────────────────────────────────────────────────────
    def open(self) -> None:
        if QUANSER_AVAILABLE:
            if config.DEBUG: print("[Physical] Quanser SDK detected: Initializing physical hardware interface...")
        else:
            raise RuntimeError(
                "The Quanser SDK is not installed on this machine.\n"
                "Physical hardware is only supported on Windows 10/11 (64-bit) and Ubuntu 24.04+.\n"
                "  Windows installer: https://github.com/quanser/quanser_sdk_win64/releases\n"
                "  Linux instructions: https://github.com/quanser/quanser_sdk_linux\n"
                "On macOS, use Virtual() instead."
            )
        
        # Open HIL card
        try:
            self.card = HIL("qube_servo3_usb", "0")
            if config.DEBUG: print("[Physical] HIL card opened.")

        except Exception as e:
            raise RuntimeError(f"[Physical] Failed to initialize HIL card: {e}")

        # Zero encoders
        #self.card.set_encoder_counts(self.encoder_channels, 2, np.array([0, 0], dtype=np.int32))

        # Initialize outputs
        self.write(0.0)

        # Set LED to green to indicate ready state
        self.set_led(0, 1, 0)


    def close(self) -> None:
        # Zero outputs
        self.card.write_analog(self.analog_channel, 1, np.array([0.0], dtype=np.float64))
        self.card.write_digital(self.digital_channel, 1, np.array([0], dtype=np.int8))

        # Set LED to red to indicate shutdown
        self.set_led(1, 0, 0)
        self.card.close()


    # ── initialisation helpers ─────────────────────────────────────────────────
    def reset(self) -> None:
        self.enable(False)  # Disable motor

    
    def await_start(self) -> None:
        input("\nPress ENTER to start control loop...")
        self.reset()
        self.enable(True)
    

    def set_led(self, r: float, g: float, b: float) -> None:
        self.led_r = max(0.0, min(1.0, r))
        self.led_g = max(0.0, min(1.0, g))
        self.led_b = max(0.0, min(1.0, b))
        self.card.write_other(self.other_write_channels, 3, np.array([self.led_r, self.led_g, self.led_b], dtype=np.float64))


    def set_target(self, theta: float, alpha: float) -> None:
        """Set the target state for the controller (not used in this implementation)."""
        self.target_theta = theta
        self.target_alpha = alpha
        if config.DEBUG: print(f"[Virtual] New target: theta={math.degrees(theta):.1f}°, alpha={math.degrees(alpha):.1f}°")


    def enable(self, on: bool) -> None:
        if on:
            # Enable motor
            self.enabled = True
            self.card.write_digital(self.digital_channel, 1, np.array([1], dtype=np.int8))
        else:
            # Disable motor
            self.enabled = False
            self.voltage_demand = 0.0
            self.card.write_digital(self.digital_channel, 1, np.array([0], dtype=np.int8))


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
        
        # Correctly handle alpha angle wrapping (e.g., 359° ≈ -1° for control purposes)
        alpha = abs((alpha + math.radians(180)) % math.radians(360))

        return theta, theta_dot, alpha, alpha_dot


    def write(self, voltage: float) -> None:
        self.voltage_demand = max(config.CONTROL_VOLTAGE_MIN, min(config.CONTROL_VOLTAGE_MAX, voltage))
        self.analog_buffer[0] = self.voltage_demand
        self.card.write_analog(self.analog_channel, 1, self.analog_buffer)