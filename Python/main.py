import threading
import time

from Config import config
from tiva_microcontroller.UART import UART
from control_platform import Physical, Virtual
from controller import run_controller


# UART thread
def uart_loop(stop_event):
    print("[Thread] started new thread:", threading.current_thread().name)

    uart = None
    try:
        uart = UART(config.UART_PORT, config.UART_BAUDRATE)
    except Exception as e:
        print(f"Error initializing UART: {e}")

        # ---------- TESTING MODE START ----------
        import math
        import random
        
        def test_thread_func():
            time.sleep(10)  
            while True:
                input("\nPress ENTER to set a new random theta target...\n") # Await for enter to set new target
                theta_target = math.radians(random.uniform(-45, 45))  # Random target between -45 and +45 degrees
                if config.DEBUG: print(f"[Test] Setting theta target to {math.degrees(theta_target):.1f}°")
                #qube.set_target(theta_target, 0.0)
        
        thread = threading.Thread(
            target=test_thread_func,
            name="TestThread",
            daemon=True
        )
        thread.start()
        # ---------- TESTING MODE END ----------

    while not stop_event.is_set():
        try:
            if uart is not None:
                line = uart.read_line()
                if line:
                    if config.DEBUG: print(f"[UART] {line}")

        except Exception as e:
            print(f"[Thread] Error in UART loop: {e}")
            if config.DEBUG:
                import traceback
                traceback.print_exc()

    uart.close()
    print("[Thread] UART stopped")


# Control loop
def control_loop(logger, plotter, stop_event):
    print("[Thread] started new thread:", threading.current_thread().name)

    # Initialize control platform
    if config.QUBE_SIMULATION:
        if config.DEBUG: print("Using Virtual QUBE-Servo 3 (simulation)")
        qube = Virtual()
    else:
        if config.DEBUG: print("Using Physical QUBE-Servo 3 (hardware)")
        qube = Physical()

    # Run control loop (will block until completion or interruption)
    try:
        print("\nStarting control system...")
        with qube:
            run_controller(qube, logger, plotter)

    except KeyboardInterrupt:
        if config.DEBUG: print("\n[Control] Interrupted by user (Ctrl+C)")
    
    except Exception as e:
        print(f"[Control] Error in control loop: {e}")
        if config.DEBUG:
            import traceback
            traceback.print_exc()


# main thread
def main():
    print("Starting on main thread:", threading.current_thread().name)

    # Event to signal thread to stop
    stop_event = threading.Event()

    # Initialize UART thread
    if config.DEBUG: print("Initializing UART thread...")
    uart_thread = threading.Thread(
        target=uart_loop,
        args=(stop_event),
        name="UARTThread",
        daemon=True
    )
    uart_thread.start()

    # Setup data logger and plotter (if enabled)
    logger = None
    plotter = None
    if config.DATA_LOGGING:
        from data import Logger
        logger = Logger()
        if config.DEBUG: print("[Main] Logger initialized.")

        if config.DATA_PLOTTING:
            from data import Plotter
            plotter = Plotter(logger)
            if config.DEBUG: print("[Main] Plotter initialized, main thread can now handle GUI events safely.")

    # Initialize control thread
    if config.DEBUG: print("Initializing Control thread...")
    controller_thread = threading.Thread(
        target=control_loop,
        args=(logger, plotter, stop_event),
        name="ControlThread",
        daemon=False
    )
    controller_thread.start()

    # Main loop
    try:
        while controller_thread.is_alive():
            time.sleep(0.1)

    finally:
        print("[Main] Stopping threads...")
        stop_event.set()
        if uart_thread.is_alive():
            uart_thread.join(timeout=1.0)
        if controller_thread.is_alive():
            controller_thread.join(timeout=1.0)
        
        # Close plotter on main thread (safe for matplotlib)
        if plotter is not None:
            plotter.close()
        
        print("Shutdown complete.")


if __name__ == "__main__":
    main()