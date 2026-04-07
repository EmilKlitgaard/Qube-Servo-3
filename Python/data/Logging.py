import numpy as np
import matplotlib.pyplot as plt

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

        if config.DEBUG: print("[Logger] Logger initialized.")
        

    def log(self, time: float, theta: float, theta_dot: float, alpha: float, alpha_dot: float, voltage: float) -> None:
        """Log a single timestep of simulation data."""
        self.time_history.append(time)
        self.theta_history.append(theta)
        self.theta_dot_history.append(theta_dot)
        self.alpha_history.append(alpha)
        self.alpha_dot_history.append(alpha_dot)
        self.voltage_history.append(voltage)


    def clear(self) -> None:
        """Clear all logged data."""
        self.time_history.clear()
        self.theta_history.clear()
        self.theta_dot_history.clear()
        self.alpha_history.clear()
        self.alpha_dot_history.clear()
        self.voltage_history.clear()


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