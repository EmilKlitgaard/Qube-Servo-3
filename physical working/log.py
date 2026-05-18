import math
import csv
from datetime import datetime


class StepMetrics:

    def __init__(
        self,
        tol=0.05,
        settle_hold=0.5
    ):

        self.tol = tol
        self.settle_hold = settle_hold

        # Create unique filename for each run
        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        self.filename = f"metrics_{timestamp}.csv"

        self._create_file()

        self.reset()

    def _create_file(self):

        with open(self.filename, "w", newline="") as file:

            writer = csv.writer(file)

            writer.writerow([
                "timestamp",
                "rise_time_s",
                "settling_time_s",
                "overshoot_percent",
                "overshoot_deg"
            ])

        print(f"Logging metrics to: {self.filename}")

    def reset(self):

        self.active = False

        self.t0 = None
        self.initial_error = None

        self.peak_opposite_error = 0.0

        self.rise_time = None
        self.settling_time = None

        self.in_band_since = None

    def start(self, t, error):

        self.reset()

        self.active = True

        self.t0 = t
        self.initial_error = error

        print("\nBalance metrics started")

    def stop(self):

        if self.active:
            print("Exited balance mode")

        self.active = False

    def log_to_file(
        self,
        rise_time,
        settling_time,
        overshoot_percent,
        overshoot_deg
    ):

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        with open(self.filename, "a", newline="") as file:

            writer = csv.writer(file)

            writer.writerow([
                timestamp,
                f"{rise_time:.4f}",
                f"{settling_time:.4f}",
                f"{overshoot_percent:.2f}",
                f"{overshoot_deg:.2f}"
            ])

    def update(self, t, error):

        if not self.active:
            return

        elapsed = t - self.t0

        e0 = abs(self.initial_error)

        # Rise time
        if (
            self.rise_time is None
            and e0 > 1e-6
            and abs(error) <= 0.1 * e0
        ):

            self.rise_time = elapsed

            print(
                f"Rise time: "
                f"{self.rise_time:.3f} s"
            )

        # Overshoot
        if error * self.initial_error < 0:

            self.peak_opposite_error = max(
                self.peak_opposite_error,
                abs(error)
            )

        # Settling time
        if abs(error) <= self.tol:

            if self.in_band_since is None:

                self.in_band_since = elapsed

            elif (
                self.settling_time is None
                and elapsed - self.in_band_since >= self.settle_hold
            ):

                self.settling_time = self.in_band_since

                if e0 > 1e-6:

                    overshoot_percent = (
                        self.peak_opposite_error / e0
                    ) * 100.0

                else:

                    overshoot_percent = 0.0

                overshoot_deg = math.degrees(
                    self.peak_opposite_error
                )

                print(
                    f"Settling time: "
                    f"{self.settling_time:.3f} s"
                )

                print(
                    f"Overshoot: "
                    f"{overshoot_percent:.2f}% "
                    f"({overshoot_deg:.2f} deg)"
                )

                self.log_to_file(
                    self.rise_time,
                    self.settling_time,
                    overshoot_percent,
                    overshoot_deg
                )

        else:

            self.in_band_since = None