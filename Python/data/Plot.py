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
        self.delay_artists = []
        self.time_offset = 0.0
        
        # Use appropriate matplotlib backend
        if not embedded:
            matplotlib.use('Agg')
            plt.ion()
        
        # Create figure and axes with GridSpec for custom layout
        if figure is not None:
            # Use provided figure (embedded mode)
            self.fig = figure
            gs = gridspec.GridSpec(3, 1, figure=self.fig, height_ratios=[1, 1, 1])
        else:
            # Create new figure (standalone mode)
            self.fig = plt.figure(figsize=self.figsize)
            gs = gridspec.GridSpec(3, 1, figure=self.fig, height_ratios=[1, 1, 1])
        
        # Create axes using GridSpec
        ax_theta = self.fig.add_subplot(gs[0, 0])
        ax_theta_target = self.fig.add_subplot(gs[1, 0])
        ax_alpha = self.fig.add_subplot(gs[2, 0])
        
        self.axes = [ax_theta, ax_theta_target, ax_alpha]
        self.ax_theta = ax_theta
        self.ax_theta_target = ax_theta_target
        self.ax_alpha = ax_alpha
        
        self.fig.suptitle('Qube-Servo 3 Tracking', fontsize=16, fontweight='bold')
        
        # Initialize empty Line2D objects for each plot
        self.lines = {
            'theta': ax_theta.plot([], [], color='#2b6cb0', linewidth=2.0, label='θ actual')[0],
            'theta_target': ax_theta_target.plot([], [], color='#c05621', linewidth=2.0, label='θ target')[0],
            'alpha': ax_alpha.plot([], [], color='#2f855a', linewidth=2.0, label='α wrapped')[0],
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
        
        self.fig.tight_layout(pad=1.2, h_pad=1.2)
        self.is_running = True
        
        if config.DEBUG: print(f"[Plotter] Plotter initialized (embedded={embedded}).")
    
    
    def setup_axes(self):
        """Configure subplots with labels, grids, and fixed references."""
        for ax in self.axes:
            ax.set_xlim(0, self.timeline_max)
            ax.grid(True, alpha=0.3)
            ax.set_xlabel('Time [s]', fontsize=11, fontweight='bold', color='#e2e8f0')
            ax.tick_params(axis='x', colors='#e2e8f0', labelcolor='#e2e8f0')

        self.ax_theta.set_ylabel('Angle [deg]', fontsize=11, fontweight='bold', color='#2b6cb0')
        self.ax_theta.tick_params(axis='y', labelcolor='#2b6cb0')
        self.ax_theta.ticklabel_format(axis='y', style='plain', useOffset=False)
        self.ax_theta.yaxis.get_major_formatter().set_scientific(False)
        self.ax_theta.set_title('Arm Angle θ (Actual)', fontsize=12, fontweight='bold', color='#e2e8f0')
        self.ax_theta.axhline(y=0.0, color='#2b6cb0', linestyle='--', alpha=0.4, linewidth=0.8)
        self.ax_theta.legend(loc='upper left', fontsize=9)

        self.ax_theta_target.set_ylabel('Angle [deg]', fontsize=11, fontweight='bold', color='#c05621')
        self.ax_theta_target.tick_params(axis='y', labelcolor='#c05621')
        self.ax_theta_target.set_title('Theta Target', fontsize=12, fontweight='bold', color='#e2e8f0')
        self.ax_theta_target.axhline(y=0.0, color='#c05621', linestyle='--', alpha=0.4, linewidth=0.8)
        self.ax_theta_target.legend(loc='upper left', fontsize=9)

        self.ax_alpha.set_ylabel('Angle [deg]', fontsize=11, fontweight='bold', color='#2f855a')
        self.ax_alpha.tick_params(axis='y', labelcolor='#2f855a')
        self.ax_alpha.set_title('Pendulum Angle α (Wrapped at 2π)', fontsize=12, fontweight='bold', color='#e2e8f0')
        self.ax_alpha.axhline(y=-180.0, color='#718096', linestyle=':', alpha=0.5, linewidth=0.8)
        self.ax_alpha.set_ylim(-190.0, 190.0)
        self.ax_alpha.legend(loc='upper left', fontsize=9)


    def _wrap_alpha_center(self, alpha_rad: np.ndarray) -> np.ndarray:
        """Wrap alpha to [-180, 180] so 0/360 stays visually centered."""
        alpha_deg = np.degrees(alpha_rad)
        return ((alpha_deg + 180.0) % 360.0) - 180.0


    def _compute_delay_events(self, time_arr: np.ndarray, theta: np.ndarray, theta_target: np.ndarray, threshold_deg: float = 2.0):
        """Find delay from each theta-target change to first target hit."""
        if len(time_arr) < 2:
            return []

        change_indices = [0]
        target_changes = np.where(np.abs(np.diff(theta_target)) > 1e-9)[0] + 1
        change_indices.extend(target_changes.tolist())

        events = []
        for start_idx in change_indices:
            hit_idx = None
            for idx in range(start_idx, len(theta)):
                if abs(theta[idx] - theta_target[idx]) <= threshold_deg:
                    hit_idx = idx
                    break

            if hit_idx is not None and hit_idx > start_idx:
                events.append((start_idx, hit_idx, time_arr[hit_idx] - time_arr[start_idx]))

        return events


    def _draw_delay_overlays(self, time_arr: np.ndarray, theta: np.ndarray, theta_target: np.ndarray) -> None:
        """Draw delay spans and markers across theta-target and alpha axes."""
        self.clear_delay_overlays()

        events = self._compute_delay_events(time_arr, theta, theta_target)
        if not events:
            return

        max_events = 8
        for start_idx, hit_idx, delay_s in events[-max_events:]:
            t_start = time_arr[start_idx]
            t_hit = time_arr[hit_idx]
            t_mid = 0.5 * (t_start + t_hit)

            self.delay_artists.append(self.ax_theta_target.axvspan(t_start, t_hit, color='#f6ad55', alpha=0.18))
            self.delay_artists.append(self.ax_theta_target.axvline(t_hit, color='#38a169', linestyle='--', linewidth=1.0, alpha=0.7))
            self.delay_artists.append(self.ax_alpha.axvline(t_hit, color='#38a169', linestyle='--', linewidth=1.0, alpha=0.45))

            y_top = self.ax_theta_target.get_ylim()[1]
            self.delay_artists.append(
                self.ax_theta_target.text(
                    t_mid,
                    y_top * 0.92,
                    f'{delay_s:.2f}s',
                    color='#744210',
                    fontsize=8,
                    ha='center',
                    va='top',
                )
            )


    def clear_delay_overlays(self) -> None:
        """Remove delay overlay artists from the figure."""
        for artist in self.delay_artists:
            try:
                artist.remove()
            except Exception:
                pass
        self.delay_artists = []


    def set_time_offset(self, time_offset: float) -> None:
        """Set display-time origin so plotted time starts from zero at the given absolute time."""
        self.time_offset = float(time_offset)


    def clear_plot(self) -> None:
        """Clear visible line data and reset x-axis to current timeline window."""
        for line in self.lines.values():
            line.set_data([], [])
        self.clear_delay_overlays()
        for ax in self.axes:
            ax.set_xlim(0, self.timeline_max)
    
    
    def update_frame(self, frame):
        """
        Update plot with current logger data.
        
        THREAD-SAFE: Safely reads from logger by taking snapshots of list lengths first.
        """
        # Safely read data from logger - take snapshot of size first to prevent mismatch
        try:
            size = self.logger.get_size()
            if size == 0:
                self.clear_plot()
                return list(self.lines.values()) + self.delay_artists
            
            # Create consistent snapshots of all arrays at same moment
            time_data = self.logger.time_history[:size]
            theta_data = self.logger.theta_history[:size]
            alpha_data = self.logger.alpha_history[:size]
            if len(self.logger.theta_target_history) >= size:
                theta_target_data = self.logger.theta_target_history[:size]
            else:
                theta_target_data = [0.0] * size
            
            # Convert to numpy arrays
            time = np.array(time_data, dtype=float)
            time = time - self.time_offset
            theta = np.degrees(np.array(theta_data, dtype=float))
            theta_target = np.degrees(np.array(theta_target_data, dtype=float))
            alpha = self._wrap_alpha_center(np.array(alpha_data, dtype=float))
            
            # Verify all arrays have same length before proceeding
            if not (len(time) == len(theta) == len(theta_target) == len(alpha)):
                if config.DEBUG:
                    print(f"[Plotter] WARNING: Array length mismatch, skipping frame")
                return list(self.lines.values()) + self.delay_artists
            
        except Exception as e:
            if config.DEBUG:
                print(f"[Plotter] Error reading logger data: {e}")
            return list(self.lines.values()) + self.delay_artists
                
        # Update line data
        self.lines['theta'].set_data(time, theta)
        self.lines['theta_target'].set_data(time, theta_target)
        self.lines['alpha'].set_data(time, alpha)
        
        # Auto-scale axes periodically
        self.frame_count += 1
        if self.frame_count % 3 == 0:
            self.autoscale_axes(time, theta, theta_target)

        self._draw_delay_overlays(time, theta, theta_target)
        
        return list(self.lines.values()) + self.delay_artists
    
    
    def autoscale_axes(self, time, theta, theta_target):
        """Auto-scale axes with timeline management."""
        if len(time) == 0:
            return
        
        # Time axis: use timeline_max or max time in data
        time_max = max(time[-1] if len(time) > 0 else self.timeline_max, self.timeline_max)
        for ax in self.axes:
            ax.set_xlim(0, time_max)
        
        if len(theta) > 0 and len(theta_target) > 0:
            theta_combined = np.concatenate([theta, theta_target])
            theta_min, theta_max = np.min(theta_combined), np.max(theta_combined)
            theta_pad = (theta_max - theta_min) * 0.1 if theta_max > theta_min else 5.0
            self.ax_theta.set_ylim(theta_min - theta_pad, theta_max + theta_pad)

        if len(theta_target) > 0:
            tt_min, tt_max = np.min(theta_target), np.max(theta_target)
            tt_pad = (tt_max - tt_min) * 0.1 if tt_max > tt_min else 5.0
            self.ax_theta_target.set_ylim(tt_min - tt_pad, tt_max + tt_pad)
    
    
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
        alpha = self._wrap_alpha_center(np.array(self.logger.alpha_history))
        
        if config.DEBUG:
            print(f"\n[Plotter] Simulation Statistics:")
            print(f"  Duration: {time[-1]:.2f} s ({len(time)} steps)")
            print(f"  theta range: [{np.min(theta):.1f}, {np.max(theta):.1f}] deg")
            print(f"  alpha wrapped range: [{np.min(alpha):.1f}, {np.max(alpha):.1f}] deg\n")