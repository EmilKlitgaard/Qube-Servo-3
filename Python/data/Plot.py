import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.gridspec as gridspec

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
    
    Can run as standalone window or embedded in tkinter GUI.
    """
    
    def __init__(self, logger: Logger, figsize=(14, 10), update_interval_ms=100, figure=None, embedded=False, timeline_max=None):
        """
        Initialize plotter with live animation.
        
        Parameters
        ----------
        logger : Logger instance to read data from (shared with control thread)
        figsize : Figure size in inches. Default: (14, 10)
        update_interval_ms : Animation update interval in milliseconds. Default: 100ms (~10Hz)
        figure : matplotlib Figure, optional. If provided, use this figure (for embedding in tkinter)
        embedded : bool, optional. If True, use Agg backend and skip plt.show() (for GUI integration)
        timeline_max : float, optional. Maximum time to show on x-axis. Expands as needed.
        """
        if config.DEBUG: print("[Plotter] Initializing plotter...")

        self.logger = logger
        self.figsize = figsize
        self.update_interval_ms = update_interval_ms
        self.is_running = True  # Flag for worker thread to signal stop
        self.embedded = embedded
        self.timeline_max = timeline_max if timeline_max else 5.0  # Default 5s
        self.frame_count = 0  # For less frequent autoscaling
        
        # Use appropriate matplotlib backend
        if not embedded:
            matplotlib.use('Agg')
            plt.ion()
        
        # Create figure and axes with GridSpec for custom layout
        if figure is not None:
            # Use provided figure (embedded mode)
            self.fig = figure
            gs = gridspec.GridSpec(3, 2, figure=self.fig, height_ratios=[1, 1, 0.8])
        else:
            # Create new figure (standalone mode)
            self.fig = plt.figure(figsize=self.figsize)
            gs = gridspec.GridSpec(3, 2, figure=self.fig, height_ratios=[1, 1, 0.8])
        
        # Create axes using GridSpec
        ax_theta = self.fig.add_subplot(gs[0, 0])
        ax_theta_dot = self.fig.add_subplot(gs[0, 1])
        ax_alpha = self.fig.add_subplot(gs[1, 0])
        ax_alpha_dot = self.fig.add_subplot(gs[1, 1])
        ax_voltage = self.fig.add_subplot(gs[2, :])
        
        self.axes = np.array([[ax_theta, ax_theta_dot], [ax_alpha, ax_alpha_dot]])
        self.ax_voltage = ax_voltage
        
        self.fig.suptitle('Qube-Servo 3 Live Simulation', fontsize=16, fontweight='bold')
        
        # Initialize empty Line2D objects for each plot
        self.lines = {
            'theta': ax_theta.plot([], [], 'b-', linewidth=2, label='θ (arm)')[0],
            'theta_dot': ax_theta_dot.plot([], [], 'g-', linewidth=2, label='θ̇ (arm)')[0],
            'alpha': ax_alpha.plot([], [], 'r-', linewidth=2, label='α (pendulum)')[0],
            'alpha_dot': ax_alpha_dot.plot([], [], 'c-', linewidth=2, label='α̇ (pendulum)')[0],
            'voltage': ax_voltage.plot([], [], 'orange', linewidth=2.5, label='Motor Voltage')[0],
        }
        
        # Setup axes formatting
        self.setup_axes()
        
        # Create animation (runs on main thread, calls update_frame periodically)
        self.anim = animation.FuncAnimation(
            self.fig, 
            self.update_frame, 
            interval=self.update_interval_ms,
            blit=False,
            cache_frame_data=False  # Important: don't cache, read fresh data each frame
        )
        
        plt.tight_layout()
        self.is_running = True
        
        if config.DEBUG: print(f"[Plotter] Plotter initialized (embedded={embedded}).")
    
    
    def setup_axes(self):
        """Configure all subplots with labels, grids, and formatting."""
        # Set initial xlim for all axes (0 to timeline_max)
        for ax in self.axes.flat:
            ax.set_xlim(0, self.timeline_max)
        self.ax_voltage.set_xlim(0, self.timeline_max)
        
        # ─ Top-left: Theta (arm angle) ─
        ax = self.axes[0, 0]
        ax.set_ylabel('Angle [°]', fontsize=11, fontweight='bold', color='b')
        ax.tick_params(axis='y', labelcolor='b')
        ax.set_title('Arm Angle (θ)', fontsize=12, fontweight='bold', color='b')
        ax.axhline(y=0, color='b', linestyle='--', alpha=0.3, linewidth=0.8)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left', fontsize=9)
        ax.set_ylim(-95, 95)
        
        # ─ Top-right: Theta_dot (arm velocity) ─
        ax = self.axes[0, 1]
        ax.set_ylabel('Angular Velocity [rad/s]', fontsize=11, fontweight='bold', color='g')
        ax.tick_params(axis='y', labelcolor='g')
        ax.set_title('Arm Velocity (θ̇)', fontsize=12, fontweight='bold', color='g')
        ax.axhline(y=0, color='g', linestyle='--', alpha=0.3, linewidth=0.8)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left', fontsize=9)
        
        # ─ Bottom-left: Alpha (pendulum angle) ─
        ax = self.axes[1, 0]
        ax.set_xlabel('Time [s]', fontsize=11, fontweight='bold', color='white')
        ax.set_ylabel('Angle [°]', fontsize=11, fontweight='bold', color='r')
        ax.tick_params(axis='y', labelcolor='r')
        ax.set_title('Pendulum Angle (α)', fontsize=12, fontweight='bold', color='r')
        # ax.axhline(y=0, color='r', linestyle='--', alpha=0.5, linewidth=0.8, label='Upright (0°)')            # Original (before inversion)
        # ax.axhline(y=180, color='orange', linestyle='--', alpha=0.5, linewidth=0.8, label='Down (180°)')      # Original (before inversion)
        ax.axhline(y=0, color='orange', linestyle='--', alpha=0.5, linewidth=0.8, label='Down (0°)')            # Inverted: 0°=down, 180°=up
        ax.axhline(y=180, color='r', linestyle='--', alpha=0.5, linewidth=0.8, label='Upright (180°)')          # Inverted: 0/360=down, 180=up
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left', fontsize=9)
        ax.set_ylim(-10, 370)
        
        # ─ Bottom-right: Alpha_dot (pendulum velocity) ─
        ax = self.axes[1, 1]
        ax.set_xlabel('Time [s]', fontsize=11, fontweight='bold', color='white')
        ax.set_ylabel('Angular Velocity [rad/s]', fontsize=11, fontweight='bold', color='c')
        ax.tick_params(axis='y', labelcolor='c')
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.3, linewidth=0.8)
        ax.set_title('Pendulum Velocity (α̇)', fontsize=12, fontweight='bold', color='c')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left', fontsize=9)
        
        # ─ Bottom: Motor Voltage ─
        ax = self.ax_voltage
        ax.set_xlabel('Time [s]', fontsize=11, fontweight='bold', color='white')
        ax.set_ylabel('Voltage [V]', fontsize=11, fontweight='bold', color='orange')
        ax.tick_params(axis='y', labelcolor='orange')
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.3, linewidth=0.8)
        ax.set_title('Motor Voltage', fontsize=12, fontweight='bold', color='white')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left', fontsize=9)
    
    
    def update_frame(self, frame):
        """
        Update plot with current logger data.
        
        THREAD-SAFE: Safely reads from logger by taking snapshots of list lengths first.
        """
        # Safely read data from logger - take snapshot of size first to prevent mismatch
        try:
            size = self.logger.get_size()
            if size == 0:
                return list(self.lines.values())
            
            # Create consistent snapshots of all arrays at same moment
            time_data = self.logger.time_history[:size]
            theta_data = self.logger.theta_history[:size]
            theta_dot_data = self.logger.theta_dot_history[:size]
            alpha_data = self.logger.alpha_history[:size]
            alpha_dot_data = self.logger.alpha_dot_history[:size]
            voltage_data = self.logger.voltage_history[:size]
            
            # Convert to numpy arrays
            time = np.array(time_data)
            theta = np.degrees(np.array(theta_data))
            theta_dot = np.array(theta_dot_data)
            # alpha = np.degrees(np.array(alpha_data))  # Original (before inversion)
            alpha = (180 - np.degrees(np.array(alpha_data))) % 360  # Invert: 0/360=down, 180=up
            alpha_dot = np.array(alpha_dot_data)
            voltage = np.array(voltage_data)
            
            # Verify all arrays have same length before proceeding
            if not (len(time) == len(theta) == len(theta_dot) == len(alpha) == len(alpha_dot) == len(voltage)):
                if config.DEBUG:
                    print(f"[Plotter] WARNING: Array length mismatch, skipping frame")
                return list(self.lines.values())
            
        except Exception as e:
            if config.DEBUG:
                print(f"[Plotter] Error reading logger data: {e}")
            return list(self.lines.values())
                
        # Update line data
        self.lines['theta'].set_data(time, theta)
        self.lines['theta_dot'].set_data(time, theta_dot)
        self.lines['alpha'].set_data(time, alpha)
        self.lines['alpha_dot'].set_data(time, alpha_dot)
        self.lines['voltage'].set_data(time, voltage)
        
        # Auto-scale axes only every 5 updates (less expensive)
        self.frame_count += 1
        if self.frame_count % 5 == 0:
            self.autoscale_axes(time, theta, theta_dot, alpha, alpha_dot)
        
        return list(self.lines.values())
    
    
    def autoscale_axes(self, time, theta, theta_dot, alpha, alpha_dot):
        """Auto-scale axes to fit data with smart padding and managed timeline."""
        if len(time) == 0:
            return
        
        # Time axis: use timeline_max or max time in data
        time_max = max(time[-1] if len(time) > 0 else self.timeline_max, self.timeline_max)
        for ax in self.axes.flat:
            ax.set_xlim(0, time_max)
        # Also set xlim for voltage axis
        self.ax_voltage.set_xlim(0, time_max)
        
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
        if len(time) > 0:
            voltage = np.array(self.logger.voltage_history[-len(time):])
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