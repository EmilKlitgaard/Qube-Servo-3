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

        self.state = "Idle"     # States: Idle/Running
        self.mode = "Numpad"    # Modes: Numpad/Encoder/Potentiometer

        self.last_data = None   # Store last received data

        if config.DEBUG: print("[UART] UART class initialized\n")
    

    def loop(self, qube, stop_event: threading.Event) -> None:
        """Continuously read and process incoming UART data. Press Ctrl+C to stop."""
        if config.DEBUG: print(f"[UART] Listening on {self.serial.port} at {self.serial.baudrate} baud.")
        try:
            while not stop_event.is_set():
                line = self.read_line()
                if line:
                    if self.is_int(line):
                        if self.state == "Running":
                            try:
                                if config.DEBUG: print(f"[UART] Received command: {line}")
                                data = int(line)
                                target = self.format_data(data)
                                target_radians = math.radians(target)
                                if target_radians != qube.target_theta:
                                    if config.DEBUG: print(f"[UART] Setting new theta target: {target:.1f}°")
                                    qube.set_target(target_radians, 0.0)
                            except ValueError:
                                print(f"[UART] Error processing command: {line}")
                    else:
                        if config.DEBUG: print(f"[UART] {line}")
                        self.check_updates(line)
                        if self.state == "Idle":
                            qube.set_target(0.0, 0.0)
                time.sleep(0.1)

        except KeyboardInterrupt:
            if config.DEBUG: print("\n[UART] Stopped.")

        finally:
            self.serial.close()


    def read_line(self) -> str | None:
        """Read one line (decoded as UTF-8, stripped of whitespace)."""
        raw = self.serial.readline()
        if raw:
            self.last_data = raw.decode("utf-8", errors="replace").strip()
            return self.last_data
        return None
    

    def check_updates(self, line: str) -> None:
        if "Idle" in line:
            self.state = "Idle"
            if config.DEBUG: print("[UART] Switched to IDLE state")
        elif "Running" in line:
            self.state = "Running"
            if config.DEBUG: print("[UART] Switched to RUNNING state")
        elif "Numpad" in line:
            self.mode = "Numpad"
            if config.DEBUG: print("[UART] Switched to NUMPAD mode")
        elif "Encoder" in line:
            self.mode = "Encoder"
            if config.DEBUG: print("[UART] Switched to ENCODER mode")
        elif "Potentiometer" in line:
            self.mode = "Potentiometer"
            if config.DEBUG: print("[UART] Switched to POTENTIOMETER mode")


    def is_int(self, data: str) -> bool:
        """Check if data is a valid integer."""
        if data is None:
            return False
        try:
            if data == "0": return True  # Special case for zero
            return int(data)
        except ValueError:
            return False


    def format_data(self, data: int) -> float:
        """Map control command integer to theta target value."""
        if self.mode == "Numpad":
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
        
        elif self.mode == "Encoder" or self.mode == "Potentiometer":
            # Map value (0-100) to theta target (-90 to +90 degrees)
            mapped_data = ((data / 100.0) * 180.0) - 90.0
            return max(-90.0, min(90.0, float(mapped_data)))  # Clamp to [-90, 90]

        else:
            return 0.0  # Default to 0 in unknown mode
        

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
