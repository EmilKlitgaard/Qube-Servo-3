import threading
import time

from tiva_microcontroller.UART import UART
from Config import config

# UART thread
def uart_loop(uart, stop_event):
    print("[Thread] started new thread:", threading.current_thread().name)

    while not stop_event.is_set():
        try:
            uart.loop()

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

    # Configuration and init objects
    uart = UART(config.UART_PORT, config.UART_BAUDRATE)

    # Event to signal thread to stop
    stop_event = threading.Event()

    # Start uart thread
    thread = threading.Thread(
        target=uart_loop,
        args=(uart, stop_event),
        name="UARTThread",
        daemon=True
    )
    thread.start()

    # Dummy controller loop (main thread) — TODO: replace with real controller
    print("Starting main loop...")
    try:
        while True:
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nCtrl+C pressed in main thread")

    finally:
        stop_event.set()
        thread.join()
        uart.close()
        print("Shutdown complete.")


if __name__ == "__main__":
    main()