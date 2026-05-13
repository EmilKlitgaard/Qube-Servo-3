from quanser.hardware import HIL
import numpy as np
import math


class qube:
    def __init__(self):
        self.counts_per_rev = 2048.0
        self.rad_per_count = 2.0 * math.pi / self.counts_per_rev

        self.card = HIL("qube_servo3_usb", "0")

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

        # Zero encoders
        self.card.set_encoder_counts(
            self.encoder_channels,
            2,
            np.array([0, 0], dtype=np.int32)
        )

        # Initialize outputs
        self.write(0.0)

        # Put board in the same output mode as working script
        self.card.write_other(
            self.other_write_channels,
            3,
            np.array([1, 1, 0], dtype=np.float64)
        )

        # Enable motor
        self.card.write_digital(
            self.digital_channel,
            1,
            np.array([1], dtype=np.int8)
        )

    def read(self):
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

    def write(self, voltage):
        voltage = max(min(voltage, 10.0), -10.0)
        self.analog_buffer[0] = voltage
        self.card.write_analog(self.analog_channel, 1, self.analog_buffer)

        # Keep output mode active
        self.card.write_other(
            self.other_write_channels,
            3,
            np.array([0, 1, 0], dtype=np.float64)
        )

    def close(self):
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

        self.card.write_other(
            self.other_write_channels,
            3,
            np.array([1, 0, 0], dtype=np.float64)
        )

        self.card.close()