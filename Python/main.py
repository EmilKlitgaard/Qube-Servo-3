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

    # Main controller
    print("\nStarting main loop...")
    try:
        if config.QUBE_SIMULATION:
            if config.DEBUG: print("Using Virtual QUBE-Servo 3 (simulation)")
            qube = Virtual()
        else:
            if config.DEBUG: print("Using Physical QUBE-Servo 3 (hardware)")
            qube = Physical()

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