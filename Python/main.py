# ╔═══════════════════════════════════════════════════╗
# ║                      IMPORTS                      ║
# ╚═══════════════════════════════════════════════════╝
import time
import threading

from Config import config
from controller import run_controller
from tiva_microcontroller.UART import UART
from control_platform import Physical, Virtual


# ╔═══════════════════════════════════════════════════╗
# ║                  HELPER FUNCTIONS                 ║
# ╚═══════════════════════════════════════════════════╝

def validate_environment():
    # ── Check if we need mjpython for MuJoCo viewer ──
    if config.QUBE_SIMULATION and config.QUBE_VISUALIZE:
        import os
        
        # Check if we're already running under mjpython (via environment variable)
        is_mjpython = os.environ.get("MJPYTHON_LAUNCHER", "false").lower() == "true"
        
        if not is_mjpython:
            import sys
            import subprocess

            if config.DEBUG: print("[Main] MuJoCo visualization enabled: Relaunching with mjpython...\n")

            # Relaunch this script with mjpython, setting environment variable
            env = os.environ.copy()
            env["MJPYTHON_LAUNCHER"] = "true"

            try:
                result = subprocess.run(['mjpython', __file__], env=env, check=False)
                sys.exit(result.returncode)

            except FileNotFoundError:
                print("[Main] ERROR: mjpython not found. Install MuJoCo or disable QUBE_VISUALIZE in Config.yaml")
                sys.exit(1)


# ╔═══════════════════════════════════════════════════╗
# ║                      THREADS                      ║
# ╚═══════════════════════════════════════════════════╝

# ── UART Thread ────────────────────────────────────────────────────────────
def uart_loop(stop_event: threading.Event) -> None:
    print("[Thread] started new thread:", threading.current_thread().name)

    uart = None
    try:
        uart = UART(config.UART_PORT, config.UART_BAUDRATE)
    except Exception as e:
        print(f"[Thread] Error initializing UART: {e}")

        # ---------- TESTING MODE START ----------
        # Skip test mode if GUI is enabled (to avoid stdin conflicts on macOS)
        if not config.GUI_ENABLED:
            import math
            import random
            
            def test_thread_func():
                time.sleep(10)
                while not stop_event.is_set():
                    input("\nPress ENTER to set a new random theta target...\n")
                    theta_target = math.radians(random.uniform(-45, 45))
                    if config.DEBUG: print(f"[Test] Setting theta target to {math.degrees(theta_target):.1f}°")
                    time.sleep(0.1)
            
            thread = threading.Thread(
                target=test_thread_func,
                name="TestThread",
                daemon=True
            )
            thread.start()
        elif config.DEBUG:
            print("[UART] GUI enabled: Skipping interactive test mode (use GUI controls instead)")
        # ---------- TESTING MODE END ----------

    try:
        while not stop_event.is_set():
            if uart is not None:
                line = uart.read_line()
                if line:
                    if config.DEBUG: print(f"[UART] {line}")
            time.sleep(0.1)

    except Exception as e:
        print(f"[Thread] Error in UART loop: {e}")
        if config.DEBUG:
            import traceback
            traceback.print_exc()

    finally:
        # Cleanup
        if uart is not None:
            uart.close()
    
    print("[Thread] UART stopped")


# ── Control Thread ────────────────────────────────────────────────────────────
def control_loop(qube, logger, stop_event: threading.Event) -> None:
    print("[Thread] started new thread:", threading.current_thread().name)

    #validate_environment()

    # Run control loop (will block until completion or interruption)
    try:
        with qube:
            # Update GUI status when control starts
            #if gui: gui.update_status(control_running=True, motor_enabled=False, mode="WAITING")
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
        #if gui: gui.update_status(control_running=False, motor_enabled=False, mode="WAITING")
        print("[Control] Control loop stopped")


# ╔════════════════════════════════════════════════╗
# ║                      MAIN                      ║
# ╚════════════════════════════════════════════════╝

# ── Main thread ────────────────────────────────────────────────────────────
def main():
    print("[Main] Starting on main thread:", threading.current_thread().name)

    # Validate environment to handle MuJoCo viewer (if needed)
    validate_environment()

    # Event to signal threads to stop
    stop_event = threading.Event()

    # Set up QUBE-Servo 3 interface (physical or virtual) based on config
    if config.QUBE_SIMULATION:
        if config.DEBUG: print("[Control] Using Virtual QUBE-Servo 3 (simulation)")
        qube = Virtual()
    else:
        if config.DEBUG: print("[Control] Using Physical QUBE-Servo 3 (hardware)")
        qube = Physical()

    # Setup data logger (plotter created inside app)
    logger = None
    if config.DATA_LOGGING:
        from data import Logger
        logger = Logger()

    # Initialize UART thread
    if config.DEBUG: print("[Main] Initializing UART thread...")
    uart_thread = threading.Thread(
        target=uart_loop,
        args=(stop_event,),
        name="UARTThread",
        daemon=True
    )
    uart_thread.start()

    # Initialize control thread
    if config.DEBUG: print("[Main] Initializing Control thread...")
    controller_thread = threading.Thread(
        target=control_loop,
        args=(qube, logger, stop_event,),
        name="ControlThread",
        daemon=True
    )
    controller_thread.start()

    # Determine what to run in main thread based on config
    main_app = None
    try:
        if config.GUI_ENABLED and not config.QUBE_VISUALIZE:
            from interface import Dashboard
            main_app = Dashboard(qube, logger, stop_event)
        elif config.QUBE_VISUALIZE and config.DATA_PLOTTING:
            from interface import Graph
            main_app = Graph(qube, logger, stop_event)

    except Exception as e:
        print(f"[Main] Error initializing main app: {e}")
        import traceback
        traceback.print_exc()
        main_app = None

    # Run GUI on main thread (if enabled)
    try:
        # Start main app loop (GUI or Graph if enabled, otherwise just wait for stop event)
        if main_app is not None:
            if config.DEBUG: print("[Main] Starting main app loop...")            
            main_app.run()
        else:
            # Wait until stop_event is set
            if config.DEBUG: print("[Main] GUI disabled or running in simulation: Waiting for stop event...")
            while not stop_event.is_set():
                time.sleep(0.1)

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
        if controller_thread.is_alive():
            if config.DEBUG: print("[Thread] Waiting for control thread to terminate...")
            controller_thread.join(timeout=timeout)
            if controller_thread.is_alive():
                print("[Thread] WARNING: Control thread did not terminate in time")
            else:
                if config.DEBUG: print("[Thread] Control thread terminated successfully.")
        
        print("[Main] Shutdown complete.")


if __name__ == "__main__":
    main()