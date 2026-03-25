import threading
import time

from Config import config
from tiva_microcontroller.UART import UART
from control_platform import Physical, Virtual
from controller import run_controller

# UART thread
def uart_loop(uart, stop_event):
    print("[Thread] started new thread:", threading.current_thread().name)

    while not stop_event.is_set():
        try:
            line = uart.read_line()
            if line:
                if config.DEBUG: print(f"[UART] {line}")

        except KeyboardInterrupt:
            print("\n[Thread] Ctrl+C detected in thread")
            break

        except Exception as e:
            print(f"[Thread] Error in UART loop: {e}")
            if config.DEBUG:
                import traceback
                traceback.print_exc()

    print("[Thread] UART stopped")

# main thread
def main():
    print("Starting on main thread:", threading.current_thread().name)

    # Event to signal thread to stop
    stop_event = threading.Event()

    # Initialize control platform
    if config.QUBE_SIMULATION:
        if config.DEBUG: print("Using Virtual QUBE-Servo 3 (simulation)")
        qube = Virtual()
    else:
        if config.DEBUG: print("Using Physical QUBE-Servo 3 (hardware)")
        qube = Physical()

    # Initialize UART thread
    print("Initializing UART thread...")
    try:
        uart = UART(config.UART_PORT, config.UART_BAUDRATE)
    except Exception as e:
        print(f"Error initializing UART: {e}")
        uart = None

    if uart:
        thread = threading.Thread(
            target=uart_loop,
            args=(uart, stop_event),
            name="UARTThread",
            daemon=True
        )
        thread.start() # Start uart thread
    else:
        print("[UART] Testing mode: Will set random theta targets every 10 seconds")
        import math
        import random
        
        def test_thread_func():
            """Set random theta targets every 10 seconds until controller finishes."""
            time.sleep(10)  
            while True:
                input("\nPress ENTER to set a new random theta target...") # Await for enter to set new target
                theta_target = math.radians(random.uniform(-45, 45))  # Random target between -45 and +45 degrees
                if config.DEBUG: print(f"[Test] Setting theta target to {math.degrees(theta_target):.1f}°")
                qube.set_target(theta_target, 0.0)
        
        thread = threading.Thread(
            target=test_thread_func,
            name="TestThread",
            daemon=True
        )
        thread.start()

    # Main controller
    print("\nStarting main loop...")
    try:
        with qube:
            run_controller(qube, duration=config.CONTROL_duration)

    except KeyboardInterrupt:
        print("\nCtrl+C pressed in main thread")

    finally:
        stop_event.set()
        if uart:
            thread.join()
            uart.close()
        print("Shutdown complete.")


if __name__ == "__main__":
    main()