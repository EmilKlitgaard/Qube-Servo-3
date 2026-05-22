# ╔═══════════════════════════════════════════════════╗
# ║                      IMPORTS                      ║
# ╚═══════════════════════════════════════════════════╝
import time
import threading

from Config import config
from tiva_microcontroller.UART import UART
from control_platform.Qube import Qube
from controller.ControlLoop import run_controller


# ╔═══════════════════════════════════════════════════╗
# ║                      THREADS                      ║
# ╚═══════════════════════════════════════════════════╝

# ── UART Thread ────────────────────────────────────────────────────────────
def uart_loop(qube: Qube, stop_event: threading.Event) -> None:
    print("[Thread] started new thread:", threading.current_thread().name)

    try:
        uart = UART(config.UART_PORT, config.UART_BAUDRATE)
        uart.loop(qube, stop_event)
        uart.close()

    except Exception as e:
        print(f"[Thread] Error initializing UART: {e}")
    
    finally:
        print("[Thread] UART stopped")


# ── Control Thread ────────────────────────────────────────────────────────────
def control_loop(qube: Qube, logger, stop_event: threading.Event) -> None:
    print("[Thread] started new thread:", threading.current_thread().name)

    # Run control loop (will block until completion or interruption)
    try:
        with qube:
            # Update GUI status when control starts
            run_controller(qube, logger, stop_event)

    except KeyboardInterrupt:
        if config.DEBUG: print("\n[Control] Interrupted by user (Ctrl+C)")
    
    except Exception as e:
        print(f"[Control] Error in control loop: {e}")
        if config.DEBUG:
            import traceback
            traceback.print_exc()
    
    finally:
        # Update GUI status when control stops
        print("[Control] Control loop stopped")


# ╔════════════════════════════════════════════════╗
# ║                      MAIN                      ║
# ╚════════════════════════════════════════════════╝

# ── Main thread ────────────────────────────────────────────────────────────
def main():
    print("[Main] Starting on main thread:", threading.current_thread().name)

    # Event to signal threads to stop
    stop_event = threading.Event()

    # Initialize QUBE
    qube = Qube()

    # Setup data logger (plotter created inside app)
    logger = None
    if config.DATA_LOGGING:
        from data.Log import Logger
        logger = Logger()

    # Initialize UART thread
    if config.DEBUG: print("[Main] Initializing UART thread...")
    uart_thread = threading.Thread(
        target=uart_loop,
        args=(qube, stop_event,),
        name="UARTThread",
        daemon=True
    )
    uart_thread.start()

    # Determine what to run in main thread based on config
    if config.GUI_ENABLED and config.DATA_PLOTTING:
        from interface import Graph
        main_app = Graph(qube, logger, stop_event)
    elif config.GUI_ENABLED:
        from interface import Dashboard
        main_app = Dashboard(qube, logger, stop_event)
    else:
        main_app = None # No GUI, run control loop in main thread

    try:
        # Start main app loop (GUI or Graph if enabled, otherwise just wait for stop event)
        if main_app is not None:
            print("[Main] Starting main app loop...")            
            main_app.run()

            # Initialize control loop in thread
            print("[Main] Initializing Control loop as thread...")
            controller_thread = threading.Thread(
                target=control_loop,
                args=(qube, logger, stop_event,),
                name="ControlThread",
                daemon=True
            )
            controller_thread.start()
        else:
            # Start control loop in main thread if no GUI (headless mode)
            print("[Main] GUI disabled. Running control loop in main thread...")
            control_loop(qube, logger, stop_event)
            controller_thread = None

    except Exception as e:
        print(f"[Main] Error in main loop: {e}")

    finally:
        print("\n[Main] Stopping all threads...")
        
        # Signal stop event to all threads
        stop_event.set()
        
        # Wait for threads to stop gracefully
        timeout = 10.0
        
        # Gracefully terminate UART thread (daemon will be forcefully killed on exit)
        if uart_thread.is_alive():
            if config.DEBUG: print("[Thread] Waiting for UART thread to terminate...")
            uart_thread.join(timeout=timeout)
            if uart_thread.is_alive():
                print("[Thread] WARNING: UART thread did not terminate in time")
            else:
                if config.DEBUG: print("[Thread] UART thread terminated successfully.")
        
        # Gracefully terminate Control thread
        if controller_thread is not None and controller_thread.is_alive():
            if config.DEBUG: print("[Thread] Waiting for control thread to terminate...")
            controller_thread.join(timeout=timeout)
            if controller_thread.is_alive():
                print("[Thread] WARNING: Control thread did not terminate in time")
            else:
                if config.DEBUG: print("[Thread] Control thread terminated successfully.")
        
        print("[Main] Shutdown complete.")


if __name__ == "__main__":
    main()