import math
import csv
from datetime import datetime
"""Simple recovery logger: record stabilization times persistently.

This module only provides a lightweight CSV logger that appends a
monotonic sample index, timestamp and recovery time (seconds). It
continues the sample index across runs by reading the last line of
the CSV if it exists.
"""

from datetime import datetime
import csv
import os


class RecoveryLogger:
    def __init__(self, filename="recovery_times.csv"):
        self.filename = filename
        self.next_index = 1

        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", newline="") as f:
                    # find last non-empty line
                    last = None
                    for line in f:
                        line = line.strip()
                        if line:
                            last = line
                    if last and not last.startswith("index"):
                        parts = last.split(",")
                        try:
                            self.next_index = int(parts[0]) + 1
                        except Exception:
                            self.next_index = 1
            except Exception:
                self.next_index = 1
        else:
            # create file with header
            with open(self.filename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["index", "timestamp", "recovery_time_s"])

    def log(self, recovery_time_s):
        """Append a recovery time (seconds) to the CSV and flush.

        Returns the written index.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        idx = self.next_index
        with open(self.filename, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([idx, timestamp, f"{recovery_time_s:.6f}"])
            f.flush()

        self.next_index += 1
        return idx


# module-level logger and convenience function
_logger = RecoveryLogger()


def log_recovery(recovery_time_s):
    """Log a recovery time in seconds and return the sample index."""
    return _logger.log(recovery_time_s)


__all__ = ["log_recovery", "RecoveryLogger"]