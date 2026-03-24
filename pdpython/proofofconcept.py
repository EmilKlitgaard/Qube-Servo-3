from quanser.hardware import HIL
import math
import numpy as np
import threading
import sys


def wrap_to_pi(x):
    return (x + math.pi) % (2.0 * math.pi) - math.pi


def clamp(x, lo, hi):
    return max(min(x, hi), lo)


theta_ref = 0.0
running = True


def keyboard_thread():
    global theta_ref, running
    print("\nControls:")
    print("  a = decrease arm reference")
    print("  d = increase arm reference")
    print("  q = quit\n")

    while running:
        key = sys.stdin.read(1)
        if key == 'a':
            theta_ref -= 0.1
            print(f"theta_ref = {theta_ref:.2f} rad")
        elif key == 'd':
            theta_ref += 0.1
            print(f"theta_ref = {theta_ref:.2f} rad")
        elif key == 'q':
            running = False


def qube_pendulum_pd_upright_from_down():
    global theta_ref, running

    frequency = 500.0
    max_voltage = 4.0

    ARM_SIGN = 1.0
    PEND_SIGN = 1.0

    counts_per_rev = 2048.0
    rad_per_count = 2.0 * math.pi / counts_per_rev

    # Classical PD gains
    Kp_alpha = 35.0
    Kd_alpha = 3.0
    Kp_theta = 2.0
    Kd_theta = 1.0

    print("Classical PD upright controller")
    print("Start with pendulum hanging DOWN.")
    print("Then pull it up toward upright; controller balances around 180 degrees.")
    print("Press q to quit.")

    card = HIL("qube_servo3_usb", "0")

    analog_channels_read = np.array([0], dtype=np.uint32)
    encoder_channels_read = np.array([0, 1], dtype=np.uint32)
    digital_channels_read = np.array([0, 1, 2], dtype=np.uint32)
    other_channels_read = np.array([14000, 14001], dtype=np.uint32)

    analog_channels_write = np.array([0], dtype=np.uint32)
    digital_channels_write = np.array([0], dtype=np.uint32)
    other_channels_write = np.array([11000, 11001, 11002], dtype=np.uint32)

    analog_buffer = np.zeros(1, dtype=np.float64)
    encoder_buffer = np.zeros(2, dtype=np.int32)
    digital_buffer = np.zeros(3, dtype=np.int8)
    other_buffer = np.zeros(2, dtype=np.float64)

    card.write_analog(analog_channels_write, 1, np.array([0.0], dtype=np.float64))
    card.write_digital(digital_channels_write, 1, np.array([0], dtype=np.int8))
    card.write_other(other_channels_write, 3, np.array([1, 1, 0], dtype=np.float64))

    # Zero encoders while pendulum is DOWN
    card.set_encoder_counts(
        encoder_channels_read, 2,
        np.array([0, 0], dtype=np.int32)
    )

    card.write_digital(digital_channels_write, 1, np.array([1], dtype=np.int8))

    task = card.task_create_reader(
        1000,
        analog_channels_read, 1,
        encoder_channels_read, 2,
        digital_channels_read, 3,
        other_channels_read, 2
    )

    card.task_start(task, 0, frequency, 2**32 - 1)

    thread = threading.Thread(target=keyboard_thread, daemon=True)
    thread.start()

    try:
        k = 0
        while running:
            card.task_read(task, 1, analog_buffer, encoder_buffer, digital_buffer, other_buffer)

            theta = ARM_SIGN * encoder_buffer[0] * rad_per_count
            alpha = PEND_SIGN * encoder_buffer[1] * rad_per_count

            theta_dot = ARM_SIGN * other_buffer[0] * rad_per_count
            alpha_dot = PEND_SIGN * other_buffer[1] * rad_per_count

            # Pendulum error relative to UPRIGHT = pi rad from the down position
            alpha_err = wrap_to_pi(alpha - math.pi)

            # Classical PD controller
            V = (
                Kp_alpha * alpha_err
                + Kd_alpha * alpha_dot
                + Kp_theta * (theta - theta_ref)
                + Kd_theta * theta_dot
            )

            V = clamp(V, -max_voltage, max_voltage)

            card.write_analog(analog_channels_write, 1, np.array([V], dtype=np.float64))
            card.write_other(other_channels_write, 3, np.array([0, 1, 0], dtype=np.float64))

            if k % 50 == 0:
                print(
                    f"t={k/frequency:5.2f}  "
                    f"theta={theta: .3f}  theta_ref={theta_ref: .3f}  "
                    f"alpha={alpha: .3f}  alpha_err={alpha_err: .3f}  "
                    f"theta_dot={theta_dot: .3f}  alpha_dot={alpha_dot: .3f}  "
                    f"V={V: .3f}"
                )
            k += 1

    except KeyboardInterrupt:
        print("Stopping...")

    finally:
        card.write_analog(analog_channels_write, 1, np.array([0.0], dtype=np.float64))
        card.write_digital(digital_channels_write, 1, np.array([0], dtype=np.int8))
        card.write_other(other_channels_write, 3, np.array([1, 0, 0], dtype=np.float64))
        card.task_stop(task)
        card.task_delete(task)
        card.close()


if __name__ == "__main__":
    qube_pendulum_pd_upright_from_down()