import time
import threading
import customtkinter as ctk
from abc import ABC, abstractmethod
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from Config import config
from data import Logger, Plotter
from control_platform import QubeInterface


class AppInterface(ctk.CTk, ABC):
    """
    Abstract base class for GUI applications (Dashboard and Graph).
    
    Does NOT inherit from ctk.CTk. Instead creates the window lazily in init_dashboard()
    to avoid conflicts with MuJoCo viewer during simulation.
    """
    
    def __init__(self, qube: QubeInterface, logger: Logger, stop_event: threading.Event):        
        self.qube = qube
        self.logger = logger
        self.stop_event = stop_event

        self.plotter = None
        self.plot_canvas = None
        self.sleep_time = 1 / config.GUI_UPDATE_RATE
        
        # Timeline management - default to 10s if not specified
        self.timeline_max = config.CONTROL_DURATION if config.CONTROL_DURATION else 5.0
        self.last_time_max = 0.0  # Track when we last expanded
        
        if config.DEBUG: print(f"[GUI] {self.__class__.__name__} initialized (window deferred)")
    

    def init_dashboard(self):
        """Initialize the CTk window and dashboard panels (called after simulation ends)."""
        if config.DEBUG: print("[GUI] Initializing CTk window...")
        super().__init__()  # Initialize the CTk window
        
        # Configure window
        if config.DEBUG: print("[GUI] Configuring window properties..")
        self.title("Qube-Servo 3 Control System")
        self.geometry("1400x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Configure main grid layout
        self.grid_columnconfigure(0, weight=0, minsize=300)     # Left panel
        self.grid_columnconfigure(1, weight=1)                  # Right panel
        self.grid_rowconfigure(0, weight=1)
        
        # Set close protocol
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Build GUI panels
        if config.DEBUG: print("[GUI] Building panels..")
        self.create_left_panel()
        if config.DATA_PLOTTING and config.DATA_LOGGING and self.logger is not None:
            self.create_right_panel()
        
        if config.DEBUG: print("[GUI] Dashboard initialization complete")
        #self.mainloop()  # Start the GUI event loop

    
    @abstractmethod
    def run(self):
        """Start the GUI main loop."""        

    
    @abstractmethod
    def create_left_panel(self) -> None:
        """Create left control panel. Must be implemented by subclasses."""
    
    
    def create_right_panel(self) -> None:
        """Create right panel with embedded matplotlib plot."""
        right_panel = ctk.CTkFrame(self, corner_radius=10)
        right_panel.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        right_panel.grid_rowconfigure(0, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)
        
        # Create matplotlib figure with better size for embedded display
        fig = Figure(figsize=(8, 6.5), dpi=80)
        fig.patch.set_facecolor("#212121")
        
        # Create plotter with embedded figure and timeline max
        self.plotter = Plotter(self.logger, figure=fig, embedded=True, timeline_max=self.timeline_max)
        
        # Embed in tkinter canvas
        self.plot_canvas = FigureCanvasTkAgg(fig, master=right_panel)
        self.plot_canvas.draw_idle()
        self.plot_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=10, pady=10)


    @abstractmethod
    def update(self) -> None:
        """Periodic update function to refresh GUI elements (e.g., plot data)."""

    
    @abstractmethod
    def on_closing(self) -> None:
        """Handle window close event."""