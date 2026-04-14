import json
import os
import sqlite3
from datetime import datetime, timezone

from Config import config


# ── State Logger ──────────────────────────────────────────────────────────
class Logger:
    """
    Logs simulation state variables over time for post-simulation plotting.
    
    Tracks: time, theta, theta_dot, alpha, alpha_dot, voltage_demand
    """
    def __init__(self) -> None:
        self.time_history = []
        self.theta_history = []
        self.theta_dot_history = []
        self.alpha_history = []
        self.alpha_dot_history = []
        self.voltage_history = []

        # Optional persistent logging backend (SQLite)
        self.db_enabled = bool(getattr(config, "DATA_DB_LOGGING", False))
        self.db_path = str(getattr(config, "DATA_DB_PATH", "data/logs.db"))
        self.db_commit_interval = max(1, int(getattr(config, "DATA_DB_COMMIT_INTERVAL", 100)))
        self._db_connection = None
        self._db_cursor = None
        self._run_id = None
        self._pending_writes = 0

        if self.db_enabled:
            self._open_database()

        if config.DEBUG: print("[Logger] Logger initialized.")


    def _resolve_db_path(self) -> str:
        if os.path.isabs(self.db_path):
            return self.db_path

        # Resolve relative DB paths from Python/ root
        python_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.normpath(os.path.join(python_root, self.db_path))


    def _config_snapshot(self) -> dict:
        snapshot = {}
        for key, value in vars(config).items():
            if key.startswith("_"):
                continue
            if callable(value):
                continue
            snapshot[key] = value
        return snapshot


    def _open_database(self) -> None:
        db_file = self._resolve_db_path()
        db_dir = os.path.dirname(db_file)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        self._db_connection = sqlite3.connect(db_file, check_same_thread=False)
        self._db_cursor = self._db_connection.cursor()

        # Better write throughput for high-frequency control logging
        self._db_cursor.execute("PRAGMA journal_mode=WAL;")
        self._db_cursor.execute("PRAGMA synchronous=NORMAL;")

        self._db_cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at_utc TEXT NOT NULL,
                simulation INTEGER NOT NULL,
                config_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS log_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                timestamp REAL NOT NULL,
                wall_time_utc TEXT NOT NULL,
                theta REAL NOT NULL,
                theta_dot REAL NOT NULL,
                alpha REAL NOT NULL,
                alpha_dot REAL NOT NULL,
                voltage_demand REAL NOT NULL,
                FOREIGN KEY (run_id) REFERENCES runs(id)
            );

            CREATE INDEX IF NOT EXISTS idx_log_entries_run_id ON log_entries(run_id);
            CREATE INDEX IF NOT EXISTS idx_log_entries_timestamp ON log_entries(timestamp);
            """
        )

        started_at_utc = datetime.now(timezone.utc).isoformat()
        simulation = 1 if bool(getattr(config, "QUBE_SIMULATION", False)) else 0
        config_json = json.dumps(self._config_snapshot(), default=str, sort_keys=True)

        self._db_cursor.execute(
            """
            INSERT INTO runs (started_at_utc, simulation, config_json)
            VALUES (?, ?, ?)
            """,
            (started_at_utc, simulation, config_json),
        )

        self._run_id = self._db_cursor.lastrowid
        self._db_connection.commit()

        if config.DEBUG:
            print(f"[Logger] Database logging enabled: {db_file} (run_id={self._run_id})")
        

    def log(self, time: float, theta: float, theta_dot: float, alpha: float, alpha_dot: float, voltage: float) -> None:
        """Log a single timestep of simulation data."""
        self.time_history.append(time)
        self.theta_history.append(theta)
        self.theta_dot_history.append(theta_dot)
        self.alpha_history.append(alpha)
        self.alpha_dot_history.append(alpha_dot)
        self.voltage_history.append(voltage)

        if self.db_enabled and self._db_cursor is not None and self._run_id is not None:
            self._db_cursor.execute(
                """
                INSERT INTO log_entries (
                    run_id, timestamp, wall_time_utc, theta, theta_dot, alpha, alpha_dot, voltage_demand
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self._run_id,
                    float(time),
                    datetime.now(timezone.utc).isoformat(),
                    float(theta),
                    float(theta_dot),
                    float(alpha),
                    float(alpha_dot),
                    float(voltage),
                ),
            )
            self._pending_writes += 1

            if self._pending_writes >= self.db_commit_interval:
                self._db_connection.commit()
                self._pending_writes = 0


    def clear(self) -> None:
        """Clear in-memory logged data used by plotting."""
        self.time_history.clear()
        self.theta_history.clear()
        self.theta_dot_history.clear()
        self.alpha_history.clear()
        self.alpha_dot_history.clear()
        self.voltage_history.clear()


    def close(self) -> None:
        """Flush and close database connection if enabled."""
        if self._db_connection is None:
            return

        if self._pending_writes > 0:
            self._db_connection.commit()
            self._pending_writes = 0

        self._db_connection.close()
        self._db_connection = None
        self._db_cursor = None

        if config.DEBUG:
            print("[Logger] Database connection closed.")


    def __del__(self):
        try:
            self.close()
        except Exception:
            # Avoid noisy destructor errors during interpreter shutdown
            pass


    def get_size(self) -> int:
        """Return number of logged timesteps."""
        return len(self.time_history)
    
    
    def get_data_slice(self, start_index: int = 0) -> dict:
        """Get data slice from start_index to end (for incremental plotting)."""
        return {
            'time': self.time_history[start_index:],
            'theta': self.theta_history[start_index:],
            'theta_dot': self.theta_dot_history[start_index:],
            'alpha': self.alpha_history[start_index:],
            'alpha_dot': self.alpha_dot_history[start_index:],
            'voltage': self.voltage_history[start_index:]
        }


    def get_data(self) -> dict:
        """Get logged data as a dictionary."""
        return {
            'time': self.time_history,
            'theta': self.theta_history,
            'theta_dot': self.theta_dot_history,
            'alpha': self.alpha_history,
            'alpha_dot': self.alpha_dot_history,
            'voltage': self.voltage_history,
        }