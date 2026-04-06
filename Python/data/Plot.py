import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from Config import config
from .Logging import Logger


# ── 2D Plotter with Live Animation ──────────────────────────────────────
class Plotter:
    """
    Live interactive 2D plotter using matplotlib animation.
    
    ARCHITECTURE: Runs on main thread with FuncAnimation timer.
    - Main thread: GUI event loop (safe for MacOSX backend)
    - Worker thread: Control loop writing to shared logger
    - Thread safety: List.append() is atomic (GIL), no locks needed
    """
    
    def __init__(self, logger: Logger, figsize=(14, 10), update_interval_ms=100):
        """
        Initialize plotter with live animation.
        
        Parameters
        ----------
        logger : Logger instance to read data from (shared with control thread)
        figsize : Figure size in inches. Default: (14, 10)
        update_interval_ms : Animation update interval in milliseconds. Default: 100ms (~10Hz)
        """
        if config.DEBUG: print("[Plotter] Initializing plotter...")

        self.logger = logger
        self.figsize = figsize
        self.update_interval_ms = update_interval_ms
        self.is_running = True  # Flag for worker thread to signal stop
        
        # Enable interactive mode
        matplotlib.use('Agg')
        plt.ion()
        
        # Create figure and axes (on main thread, safe for MacOSX)
        self.fig, self.axes = plt.subplots(2, 2, figsize=self.figsize)
        self.fig.suptitle('Qube-Servo 3 Live Simulation', fontsize=16, fontweight='bold')
        
        # Initialize empty Line2D objects for each plot
        self.lines = {
            'theta': self.axes[0, 0].plot([], [], 'b-', linewidth=2, label='θ (arm)')[0],
            'theta_dot': self.axes[0, 1].plot([], [], 'g-', linewidth=2, label='θ̇ (arm)')[0],
            'alpha': self.axes[1, 0].plot([], [], 'r-', linewidth=2, label='α (pendulum)')[0],
            'alpha_dot': self.axes[1, 1].plot([], [], 'c-', linewidth=2, label='α̇ (pendulum)')[0],
        }
        
        # Setup axes formatting
        self.setup_axes()
        
        # Create secondary axis for voltage on bottom-right
        self.ax_voltage = self.axes[1, 1].twinx()
        self.ax_voltage.set_ylabel('Voltage [V]', fontsize=11, fontweight='bold', color='orange')
        self.ax_voltage.tick_params(axis='y', labelcolor='orange')
        self.lines['voltage'] = None
        
        # Create animation (runs on main thread, calls _update_frame periodically)
        self.anim = animation.FuncAnimation(
            self.fig, 
            self.update_frame, 
            interval=self.update_interval_ms,
            blit=False,
            cache_frame_data=False  # Important: don't cache, read fresh data each frame
        )
        
        plt.tight_layout()
        plt.show(block=False)  # Non-blocking display
        self.is_running = True
        
        if config.DEBUG: print(f"[Plotter] Plotter initialized.")
    
    
    def setup_axes(self):
        """Configure all subplots with labels, grids, and formatting."""
        # ─ Top-left: Theta (arm angle) ─
        ax = self.axes[0, 0]
        ax.set_ylabel('Angle [°]', fontsize=11, fontweight='bold')
        ax.set_title('Arm Angle (θ)', fontsize=12, fontweight='bold')
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.3, linewidth=0.8)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', fontsize=9)
        ax.set_ylim(-95, 95)
        
        # ─ Top-right: Theta_dot (arm velocity) ─
        ax = self.axes[0, 1]
        ax.set_ylabel('Angular Velocity [rad/s]', fontsize=11, fontweight='bold')
        ax.set_title('Arm Velocity (θ̇)', fontsize=12, fontweight='bold')
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.3, linewidth=0.8)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', fontsize=9)
        
        # ─ Bottom-left: Alpha (pendulum angle) ─
        ax = self.axes[1, 0]
        ax.set_xlabel('Time [s]', fontsize=11, fontweight='bold')
        ax.set_ylabel('Angle [°]', fontsize=11, fontweight='bold')
        ax.set_title('Pendulum Angle (α)', fontsize=12, fontweight='bold')
        ax.axhline(y=0, color='r', linestyle='--', alpha=0.5, linewidth=0.8, label='Upright (0°)')
        ax.axhline(y=180, color='orange', linestyle='--', alpha=0.5, linewidth=0.8, label='Down (180°)')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', fontsize=9)
        ax.set_ylim(-10, 370)
        
        # ─ Bottom-right: Alpha_dot (pendulum velocity) + Voltage ─
        ax = self.axes[1, 1]
        ax.set_xlabel('Time [s]', fontsize=11, fontweight='bold')
        ax.set_ylabel('Angular Velocity [rad/s]', fontsize=11, fontweight='bold', color='c')
        ax.tick_params(axis='y', labelcolor='c')
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.3, linewidth=0.8)
        ax.set_title('Pendulum Velocity (α̇) + Motor Voltage', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left', fontsize=9)
    
    
    def update_frame(self, frame):
        """
        Animation frame callback (called by FuncAnimation on main thread).
        
        THREAD-SAFE: Only reads from logger. List operations (time_history, etc.)
        are atomic in Python due to GIL, safe even with worker thread writing.
        """
        if self.logger.get_size() == 0:
            return list(self.lines.values())
        
        # Thread-safe read: get data from logger (atomic list reads)
        time = np.array(self.logger.time_history)
        theta = np.degrees(np.array(self.logger.theta_history))
        theta_dot = np.array(self.logger.theta_dot_history)
        alpha = np.degrees(np.array(self.logger.alpha_history))
        alpha_dot = np.array(self.logger.alpha_dot_history)
        voltage = np.array(self.logger.voltage_history)
        
        # Show only last N points for rendering efficiency
        max_points = 500
        if len(time) > max_points:
            idx = len(time) - max_points
            time = time[idx:]
            theta = theta[idx:]
            theta_dot = theta_dot[idx:]
            alpha = alpha[idx:]
            alpha_dot = alpha_dot[idx:]
            voltage = voltage[idx:]
        
        # Update line data
        self.lines['theta'].set_data(time, theta)
        self.lines['theta_dot'].set_data(time, theta_dot)
        self.lines['alpha'].set_data(time, alpha)
        self.lines['alpha_dot'].set_data(time, alpha_dot)
        
        # Update voltage line
        if self.lines['voltage'] is None:
            self.lines['voltage'] = self.ax_voltage.plot(time, voltage, 'orange', linewidth=2.5, alpha=0.7, label='Motor Voltage')[0]
            self.ax_voltage.legend(loc='upper right', fontsize=9)
        else:
            self.lines['voltage'].set_data(time, voltage)
        
        # Auto-scale axes
        self.autoscale_axes(time, theta, theta_dot, alpha, alpha_dot)
        
        return list(self.lines.values())
    
    
    def autoscale_axes(self, time, theta, theta_dot, alpha, alpha_dot):
        """Auto-scale axes to fit data with smart padding."""
        if len(time) == 0:
            return
        
        # Time axis: always from 0 to max
        for ax in self.axes.flat:
            ax.set_xlim(0, time[-1])
        
        # Theta: auto-scale with padding
        if len(theta) > 0:
            theta_min, theta_max = np.min(theta), np.max(theta)
            theta_pad = (theta_max - theta_min) * 0.1 if theta_max > theta_min else 10
            self.axes[0, 0].set_ylim(theta_min - theta_pad, theta_max + theta_pad)
        
        # Theta_dot: auto-scale with padding
        if len(theta_dot) > 0:
            td_min, td_max = np.min(theta_dot), np.max(theta_dot)
            td_pad = (td_max - td_min) * 0.1 if td_max > td_min else 0.5
            self.axes[0, 1].set_ylim(td_min - td_pad, td_max + td_pad)
        
        # Alpha_dot: auto-scale with padding
        if len(alpha_dot) > 0:
            ad_min, ad_max = np.min(alpha_dot), np.max(alpha_dot)
            ad_pad = (ad_max - ad_min) * 0.1 if ad_max > ad_min else 0.5
            self.axes[1, 1].set_ylim(ad_min - ad_pad, ad_max + ad_pad)
        
        # Voltage: auto-scale
        if len(self.logger.voltage_history) > 0:
            voltage = np.array(self.logger.voltage_history)
            v_min, v_max = np.min(voltage), np.max(voltage)
            v_pad = (v_max - v_min) * 0.1 if v_max > v_min else 1.0
            self.ax_voltage.set_ylim(v_min - v_pad, v_max + v_pad)
    
    
    def close(self):
        """Close and cleanup the plotter (ONLY call from main thread).
        
        This method must be called from the main thread, never from the worker thread,
        because matplotlib GUI operations (fig closing) are not thread-safe on macOS.
        """
        try:
            # Stop animation
            if self.anim is not None:
                try:
                    self.anim.event_source.stop()
                except:
                    pass
            
            # Print statistics
            self.print_statistics()
            
            # Close figure (must be on main thread for matplotlib)
            if self.fig is not None:
                plt.close(self.fig)
            
            self.is_running = False
            
            if config.DEBUG:
                print("[Plotter] Closed")
        except Exception as e:
            if config.DEBUG:
                print(f"[Plotter] Warning during close: {e}")
    
    
    def print_statistics(self):
        """Print simulation statistics."""
        if self.logger.get_size() == 0:
            return
        
        time = np.array(self.logger.time_history)
        theta = np.degrees(np.array(self.logger.theta_history))
        alpha = np.degrees(np.array(self.logger.alpha_history))
        theta_dot = np.array(self.logger.theta_dot_history)
        alpha_dot = np.array(self.logger.alpha_dot_history)
        voltage = np.array(self.logger.voltage_history)
        
        if config.DEBUG:
            print(f"\n[Plotter] Simulation Statistics:")
            print(f"  Duration: {time[-1]:.2f} s ({len(time)} steps)")
            print(f"  θ range: [{np.min(theta):.1f}°, {np.max(theta):.1f}°]")
            print(f"  α range: [{np.min(alpha):.1f}°, {np.max(alpha):.1f}°]")
            print(f"  θ̇ range: [{np.min(theta_dot):.2f}, {np.max(theta_dot):.2f}] rad/s")
            print(f"  α̇ range: [{np.min(alpha_dot):.2f}, {np.max(alpha_dot):.2f}] rad/s")
            print(f"  V range: [{np.min(voltage):.2f}, {np.max(voltage):.2f}] V\n")