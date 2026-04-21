"""
GUI for Qube-Servo 3 Control System.

Architecture:
- AppInterface (ABC): Defines common interface for Dashboard and Graph
- Dashboard: Live mode (SIMULATION=False) - interactive with control buttons
- Graph: Historical mode (SIMULATION=True) - displays completed simulation data

Both use Plot.py for visualization, pulling data from Logger via periodic updates.
"""

import time
import threading
import customtkinter as ctk

from Config import config
from data import Logger
from interface import AppInterface
from control_platform import QubeInterface

# ═══════════════════════════════════════════════════════════════════════════════
# GRAPH: STATIC MODE (SIMULATION=True)
# ═══════════════════════════════════════════════════════════════════════════════

class Graph(AppInterface):
    """
    Post-simulation plot viewer for historical data.
    
    Features:
    - Static display of completed simulation
    - No control buttons
    - Shows final logged data via Plot.py
    - Runs when SIMULATION=True and simulation has ended
    """
    
    def __init__(self, qube: QubeInterface, logger: Logger, stop_event: threading.Event):
        """Initialize Graph for historical data display."""
        super().__init__(qube, logger, stop_event)
        # For graph, use the actual logged time as max (will be set from data)
        self.data_plotted = False
    

    def run(self) -> None:
        """Wait for simulation to complete, then display results."""
        # Wait for simulation to finish
        while not self.stop_event.is_set():
            try:
                time.sleep(0.1)
            except Exception as e:
                if config.DEBUG: print(f"[GUI] Error waiting for simulation: {e}")
        
        # Simulation complete - get elapsed time and set timeline
        self.timeline_max = self.logger.time_history[-1]
        if config.DEBUG: print(f"[Graph] Simulation ended at {self.timeline_max:.2f}s")
        
        # Initialize dashboard and plot
        self.init_dashboard()
        self.update()  # Plot all historical data once before exiting
        self.mainloop()  # Start the GUI event loop until user closes the window


    def create_left_panel(self) -> None:
        """Create simplified left panel (no controls, just info)."""
        left_panel = ctk.CTkFrame(self, corner_radius=10)
        left_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Configure grid
        left_panel.grid_rowconfigure(0, weight=0)  # Title
        left_panel.grid_rowconfigure(1, weight=1)  # Info section
        left_panel.grid_columnconfigure(0, weight=1)
        
        # Title
        title = ctk.CTkLabel(
            left_panel,
            text="Qube-Servo 3",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.grid(row=0, column=0, padx=15, pady=15, sticky="ew")
        
        # Info frame
        info_frame = ctk.CTkFrame(left_panel, corner_radius=8)
        info_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        info_text = """Simulation Complete

Data Analysis:
- Final state logged
- Plot generated
- Ready for export

Close window to exit"""
        
        info_label = ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        info_label.pack(padx=10, pady=10)
    
    
    def update(self) -> None:
        """Plot all historical data with actual elapsed time."""
        if self.logger is None or self.plotter is None or self.plot_canvas is None:
            return
        
        try:
            # Get elapsed time from logger
            if self.logger.get_size() > 0:
                elapsed_time = self.logger.time_history[-1]
                self.timeline_max = elapsed_time
                self.plotter.timeline_max = elapsed_time
                
                if config.DEBUG and not self.data_plotted:
                    print(f"[Graph] Plotting {self.logger.get_size()} data points over {elapsed_time:.2f}s")
            
            # Update the plot with all data
            self.plotter.update_frame(frame=0)
            
            # Redraw canvas
            self.plot_canvas.draw_idle()
            
            self.data_plotted = True
        except Exception as e:
            if config.DEBUG:
                print(f"[GUI] Error updating plot: {e}")
    
    
    def on_closing(self):
        """Handle window close event."""
        if config.DEBUG: print("[Graph] Close requested by user")
        
        # Set stop event
        if self.stop_event:
            self.stop_event.set()
        
        # Clean up plotter resources
        if self.plotter is not None:
            try:
                self.plotter.close()
            except Exception as e:
                if config.DEBUG: print(f"[GUI] Error closing plotter: {e}")
        
        # Destroy window and exit
        self.destroy()
        if config.DEBUG: print("[Graph] Window closed, exiting GUI")
