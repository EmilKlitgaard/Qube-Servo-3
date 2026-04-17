
import time
import threading
import customtkinter as ctk

from Config import config
from data import Logger
from interface import AppInterface
from control_platform import QubeInterface

# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD: LIVE MODE (SIMULATION=False)
# ═══════════════════════════════════════════════════════════════════════════════
class Dashboard(AppInterface):
    """
    Professional GUI dashboard for live control.
    
    Features:
    - Control buttons (START, MOTOR, RESET)
    - Real-time status indicators
    - Live plotting of data from Logger
    - Runs when SIMULATION=False
    """
    
    def __init__(self, qube: QubeInterface, logger: Logger, stop_event: threading.Event):
        """Initialize Dashboard."""
        super().__init__(qube, logger, stop_event)
        self.motor_enabled = False

        self.init_dashboard()  # Create the CTk window and panels


    def run(self) -> None:
        """Run the Dashboard event loop with periodic updates."""
        if config.DEBUG: print("[GUI] Starting Dashboard event loop...")
        # Schedule first update
        self.schedule_update()
        # Start the GUI event loop (blocks until window closes)
        self.mainloop()
    
    
    def schedule_update(self) -> None:
        """Schedule the next update via after() callback."""
        try:
            # Call update to refresh plot
            self.update()

            # Schedule next update
            self.after(int(self.sleep_time * 1000), self.schedule_update)
        
        except Exception as e:
            if config.DEBUG:
                print(f"[GUI] Error in scheduled update: {e}")
    
    
    def create_left_panel(self) -> None:
        """Create left control panel with buttons and status indicators."""
        left_panel = ctk.CTkFrame(self, corner_radius=10)
        left_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Configure grid
        left_panel.grid_rowconfigure(0, weight=0)  # Title
        left_panel.grid_rowconfigure(1, weight=0)  # Control buttons
        left_panel.grid_rowconfigure(2, weight=0)  # Status section
        left_panel.grid_rowconfigure(3, weight=1)  # Config section
        left_panel.grid_columnconfigure(0, weight=1)
        
        # Title
        title = ctk.CTkLabel(
            left_panel,
            text="Qube-Servo 3",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.grid(row=0, column=0, padx=15, pady=15, sticky="ew")
        
        # Control frame
        control_frame = ctk.CTkFrame(left_panel, corner_radius=8)
        control_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        control_frame.grid_columnconfigure(0, weight=1)
        
        # Start
        self.btn_start_stop = ctk.CTkButton(
            control_frame,
            text="▶ START CONTROL",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#28a745",
            hover_color="#20c997",
            height=40,
            command=self.start_control
        )
        self.btn_start_stop.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        # Motor Enable/Disable button
        self.btn_motor = ctk.CTkButton(
            control_frame,
            text="⚡ ENABLE MOTOR",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#007bff",
            hover_color="#0056b3",
            height=40,
            command=self.toggle_motor
        )
        self.btn_motor.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        # Reset button (simulation only)
        if config.QUBE_SIMULATION:
            self.btn_reset = ctk.CTkButton(
                control_frame,
                text="🔄 RESET",
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#ffc107",
                hover_color="#e0a800",
                height=40,
                command=self.reset_system
            )
            self.btn_reset.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        # Status frame
        status_frame = ctk.CTkFrame(left_panel, corner_radius=8)
        status_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1)
        
        # Control status
        ctk.CTkLabel(
            status_frame,
            text="Control:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        
        self.status_control = ctk.CTkLabel(
            status_frame,
            text="● STOPPED",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        )
        self.status_control.grid(row=1, column=0, padx=10, pady=0, sticky="w")
        
        # Motor status
        ctk.CTkLabel(
            status_frame,
            text="Motor:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=2, column=0, padx=10, pady=(10, 0), sticky="w")
        
        self.status_motor = ctk.CTkLabel(
            status_frame,
            text="● DISABLED",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        )
        self.status_motor.grid(row=3, column=0, padx=10, pady=0, sticky="w")
        
        # Mode indicator
        ctk.CTkLabel(
            status_frame,
            text="Mode:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=4, column=0, padx=10, pady=(10, 0), sticky="w")
        
        self.mode_indicator = ctk.CTkLabel(
            status_frame,
            text="WAITING",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        )
        self.mode_indicator.grid(row=5, column=0, padx=10, pady=(0, 10), sticky="w")
        
        # Config frame
        config_frame = ctk.CTkFrame(left_panel, corner_radius=8)
        config_frame.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        
        config_text = f"""Platform: {'Simulation' if config.QUBE_SIMULATION else 'Hardware'}
Data: {'ON' if config.DATA_LOGGING else 'OFF'}
Plot: {'ON' if config.DATA_PLOTTING else 'OFF'}
DT: {config.CONTROL_DT*1000:.1f}ms"""
        
        config_label = ctk.CTkLabel(
            config_frame,
            text=config_text,
            font=ctk.CTkFont(size=10, family="monospace"),
            justify="left"
        )
        config_label.pack(padx=10, pady=10)
    
    
    def start_control(self) -> None:
        """Start control loop."""
        self.qube.loop_running = True
        if config.DEBUG: print(f"[GUI] Start loop flag set to: {self.qube.loop_running}")
        self.btn_start_stop.grid_remove()   # Remove button after starting
        time.sleep(0.1)  # Small delay to ensure flag is set before control loop checks it
        self.update_status_display()
    
    
    def toggle_motor(self) -> None:
        """Toggle motor enable/disable."""
        self.qube.enabled = not self.qube.enabled
        if config.DEBUG: print(f"[GUI] Motor toggled: {'ENABLED' if self.qube.enabled else 'DISABLED'}")
        self.update_status_display()
    
    
    def reset_system(self) -> None:
        """Reset system state."""
        self.qube.reset()  # Reset the control platform (simulation only)
        self.qube.enabled = False
        self.update_status_display()
        self.logger.clear()  # Clear all logged data
        if config.DEBUG: print("[GUI] System reset triggered")
    
    
    def update_status_display(self) -> None:
        """Update all status indicators."""
        # Update control status
        if self.qube.loop_running:
            self.status_control.configure(text="● RUNNING", text_color="#28a745")
        else:
            self.status_control.configure(text="● STOPPED", text_color="#888888")
        
        # Update motor status
        if self.qube.enabled:
            self.status_motor.configure(text="● ENABLED", text_color="#28a745")
            self.btn_motor.configure(text="⏸ DISABLE MOTOR", fg_color="#6f42c1", hover_color="#4d2d9e")
        else:
            self.status_motor.configure(text="● DISABLED", text_color="#888888")
            self.btn_motor.configure(text="⚡ ENABLE MOTOR", fg_color="#007bff", hover_color="#0056b3")


    def update(self) -> None:
        """Update plot with latest data and handle timeline expansion."""
        if self.logger is None or self.plotter is None or self.plot_canvas is None:
            return
        
        try:
            # Get current max time from logger
            if self.logger.get_size() > 0:
                current_time = self.logger.time_history[-1]
                
                # Expand timeline if needed (when reaching 95% of current max)
                if current_time > self.timeline_max * 0.95:
                    self.timeline_max *= 1.1  # Expand by 10%
                    self.plotter.timeline_max = self.timeline_max  # Update plotter
                    if config.DEBUG:
                        print(f"[GUI] Timeline expanded to {self.timeline_max:.1f}s")
            
            # Update the plot with all data
            self.plotter.update_frame(frame=0)
            
            # Redraw canvas
            self.plot_canvas.draw_idle()
        except Exception as e:
            if config.DEBUG:
                print(f"[GUI] Error updating plot: {e}")

    
    def on_closing(self):
        """Handle window close event."""
        if config.DEBUG: print("[GUI] Dashboard close requested")
        self.stop_event.set()  # Signal all threads to stop
        self.qube.enable(False)  # Ensure motor is disabled
        self.update_status_display()
        self.destroy()
        if config.DEBUG: print("[GUI] Dashboard closed and stop event set")