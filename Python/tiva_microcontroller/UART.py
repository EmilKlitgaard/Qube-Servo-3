import math
import time
import threading

import serial
import serial.tools.list_ports

from Config import config

class UART:
    def __init__(self, port: str, baudrate: int = 19200, data_bits: int = 8, parity: str = 'N', stop_bits: int = 1, timeout: float = 1.0):
        print(f"[UART] Connecting to UART port '{port}' with {baudrate} baud...")
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
                print(f"[UART] Error: Port '{port}' not found. Is the device plugged in?")
                list_ports()
            elif "permission denied" in error_msg or "access is denied" in error_msg:
                print(f"[UART] Error: Port '{port}' is occupied or permission denied. Close any other program using the port (e.g. another terminal, IDE serial monitor).")
            else:
                print(f"[UART] Error opening port '{port}': {e}")
            raise 

        self.last_data = None
        if config.DEBUG: print("[UART] UART class initialized\n")
    

    def loop(self, qube, stop_event: threading.Event) -> None:
        """Continuously read and process incoming UART data. Press Ctrl+C to stop."""
        print(f"[UART] Listening on {self.serial.port} at {self.serial.baudrate} baud.")
        try:
            while not stop_event.is_set():
                line = self.read_line()
                if line:
                    # Check if it's a valid control command (integer 0-12)
                    if self.is_valid_int(line):
                        try:
                            cmd = int(line)
                            target = self.format_data(cmd)
                            print(f"[UART] Setting new theta target: {qube.target_theta:.1f}°")
                            qube.set_target(math.radians(target), 0.0)
                        except ValueError:
                            print(f"[UART] Error processing command: {line}")
                    else:
                        # It's a string message, just print it
                        print(f"[UART] {line}")
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n[UART] Stopped.")
        finally:
            self.serial.close()


    def read_line(self) -> str | None:
        """Read one line (decoded as UTF-8, stripped of whitespace)."""
        raw = self.serial.readline()
        if raw:
            self.last_data = raw.decode("utf-8", errors="replace").strip()
            return self.last_data
        return None


    def is_valid_int(self, data: str) -> bool:
        """Check if data is a valid integer command (0-12)."""
        if data is None:
            return False
        try:
            value = int(data)
            return 0 <= value <= 12
        except ValueError:
            return False


    def format_data(self, data: int) -> float:
        """Map control command integer to theta target value.
        
        Mapping: 1,4,7,10 = -20, -40, -60, -80
                 3,6,9,12 = 20, 40, 60, 80
                 0,2,5,8,11 = 0.0
        """
        mapping = {     
            1: -20.0,   2: 0.0,     3: 20.0,    
            4: -40.0,   5: 0.0,     6: 40.0,    
            7: -60.0,   8: 0.0,     9: 60.0,    
            10: -80.0,  11: 0.0,    12: 80.0
        }
        if data in mapping:
            return mapping[data]
        else:
            return 0.0  # Default to 0 if command is out of range
        

    def get_data(self) -> str | None:
        return self.last_data


    def close(self):
        self.serial.close()


def list_ports():
    """Helper to list all available serial ports."""
    print("[UART] Available serial ports:")
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
