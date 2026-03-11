import threading
import time

from tiva_microcontroller.UART import UART
from platform import Physical, Virtual
from Config import config
from controller.Controller import PendulumController

# UART thread
def uart_loop(uart, stop_event):
    print("[Thread] started new thread:", threading.current_thread().name)

    while not stop_event.is_set():
        try:
            line = uart.read_line()
            if line:
                print(f"[UART] {line}")

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

    # Main controller thread
    print("Starting main loop...")
    try:
        if config.QUBE_SIMULATION:
            if config.DEBUG: print("Using Virtual QUBE-Servo 3 (simulation)")
            qube = Virtual(speed=config.QUBE_SIMULATION_SPEED)
        else:
            if config.DEBUG: print("Using Physical QUBE-Servo 3 (hardware)")
            qube = Physical()

        ctrl = PendulumController()
        with qube:
            input("\nPress ENTER to start control loop...") # Await for enter to start control loop
            qube.reset()
            qube.set_led(0, 1, 0)
            qube.enable(True)
            try:
                while True:
                    voltage = ctrl.step(*qube.read())
                    qube.write(voltage)
            except KeyboardInterrupt:
                print("\nStopped.")

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