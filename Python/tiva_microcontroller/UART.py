import serial
import serial.tools.list_ports

from Config import config

class UART:
    def __init__(self, port: str, baudrate: int = 19200, data_bits: int = 8, parity: str = 'N', stop_bits: int = 1, timeout: float = 1.0):
        print(f"Connecting to UART port '{port}' with {baudrate} baud...")
        try:
            self.serial = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=data_bits,
                parity=parity,
                stopbits=stop_bits,
                timeout=timeout,
            )
        except serial.SerialException as e:
            error_msg = str(e).lower()
            if "no such file" in error_msg or "could not open port" in error_msg:
                print(f"Error: Port '{port}' not found. Is the device plugged in?")
                list_ports()
            elif "permission denied" in error_msg or "access is denied" in error_msg:
                print(f"Error: Port '{port}' is occupied or permission denied.")
                print("Close any other program using the port (e.g. another terminal, IDE serial monitor).")
            else:
                print(f"Error opening port '{port}': {e}")
            raise SystemExit(1)
        self.last_data = None
        if config.DEBUG: print("[UART class initialized]\n")

    def read_line(self) -> str | None:
        """Read one line (decoded as UTF-8, stripped of whitespace)."""
        raw = self.serial.readline()
        if raw:
            self.last_data = raw.decode("utf-8", errors="replace").strip()
            return self.last_data
        return None

    def loop(self):
        """Continuously print incoming UART data. Press Ctrl+C to stop."""
        print(f"Listening on {self.serial.port} at {self.serial.baudrate} baud.")
        try:
            while True:
                line = self.read_line()
                if line:
                    print(f"[UART] Received: {line}")
        except KeyboardInterrupt:
            print("\nStopped.")
        finally:
            self.serial.close()

    def get_data(self) -> str | None:
        return self.last_data

    def close(self):
        self.serial.close()


def list_ports():
    """Helper to list all available serial ports."""
    print("Available serial ports:")
    ports = serial.tools.list_ports.comports()
    for p in ports:
        print(f"  {p.device} — {p.description}")
    print("")


# Example usage
if __name__ == "__main__":
    list_ports()

    # Change this to match your device, e.g. '/dev/cu.usbmodem14101'
    PORT = "/dev/cu.usbmodem0E2208FC1"
    BAUDRATE = 19200

    uart = UART(port=PORT, baudrate=BAUDRATE)
    uart.loop()
