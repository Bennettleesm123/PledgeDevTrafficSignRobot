"""
Milestone 2: Brain-to-Muscle Handshake - Python Serial Controller
==================================================================
Sends single-character commands to the Arduino over USB Serial.

Serial Protocol:
    F = Forward   B = Backward
    L = Left      R = Right
    S = Stop

Requirements:
    pip install pyserial

Usage:
    # Manual keyboard control (great for testing the connection):
    python arduino_controller.py --port COM3          # Windows
    python arduino_controller.py --port /dev/ttyACM0  # Linux/Mac

    # Import as a module from your vision script:
    from arduino_controller import RobotController
    robot = RobotController(port="COM3")
    robot.forward()
    robot.stop()
    robot.close()

Finding your port:
    Windows  → Device Manager → Ports (COM & LPT)
    Linux    → ls /dev/tty*   (usually /dev/ttyACM0 or /dev/ttyUSB0)
    Mac      → ls /dev/tty.*  (usually /dev/tty.usbmodem...)
"""

import serial
import serial.tools.list_ports
import time
import sys
import argparse

COMMANDS = {
    "forward":  "F",
    "backward": "B",
    "left":     "L",
    "right":    "R",
    "stop":     "S",
}

BAUD_RATE    = 9600
STARTUP_WAIT = 2.0  


class RobotController:
    """
    Simple interface to the Arduino motor controller.

    Example:
        robot = RobotController(port="COM3")
        robot.forward()
        time.sleep(1)
        robot.stop()
        robot.close()
    """

    def __init__(self, port: str, baud: int = BAUD_RATE, timeout: float = 1.0):
        self.port = port
        try:
            self.ser = serial.Serial(port, baud, timeout=timeout)
            time.sleep(STARTUP_WAIT)     
            self._flush_startup()
            print(f"[Robot] Connected on {port} at {baud} baud.")
        except serial.SerialException as e:
            print(f"[Robot] ERROR: Could not open {port}: {e}")
            print("[Robot] Available ports:")
            for p in serial.tools.list_ports.comports():
                print(f"         {p.device}  –  {p.description}")
            raise

    def _flush_startup(self):
        """Read and print any startup messages from Arduino (e.g. 'READY')."""
        while self.ser.in_waiting:
            line = self.ser.readline().decode("utf-8", errors="ignore").strip()
            if line:
                print(f"[Arduino] {line}")

    def _send(self, char: str) -> str:
        """Send a single character and return the Arduino's ACK line."""
        if not self.ser or not self.ser.is_open:
            print("[Robot] Serial port not open!")
            return ""
        self.ser.write(char.encode())
        time.sleep(0.05)  
        response = ""
        while self.ser.in_waiting:
            response = self.ser.readline().decode("utf-8", errors="ignore").strip()
            print(f"[Arduino] {response}")
        return response

    # ── Public command methods ────────────────────────────────────────────────
    def forward(self):
        return self._send(COMMANDS["forward"])

    def backward(self):
        return self._send(COMMANDS["backward"])

    def left(self):
        return self._send(COMMANDS["left"])

    def right(self):
        return self._send(COMMANDS["right"])

    def stop(self):
        return self._send(COMMANDS["stop"])

    def send_raw(self, char: str):
        """Send any raw character (for testing)."""
        return self._send(char.upper())

    def close(self):
        if self.ser and self.ser.is_open:
            self.stop()          # safety: always stop before disconnecting
            self.ser.close()
            print("[Robot] Serial port closed.")

class SafeRobot:
    """
    Use as a context manager so the robot always stops, even on crash.

        with SafeRobot(port="COM3") as robot:
            robot.forward()
            time.sleep(1)
            # If exception occurs here, stop() is still called automatically
    """
    def __init__(self, port, baud=BAUD_RATE):
        self._port = port
        self._baud = baud
        self.robot = None

    def __enter__(self):
        self.robot = RobotController(self._port, self._baud)
        return self.robot

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.robot:
            self.robot.close()
        if exc_type:
            print(f"[SafeRobot] Stopped due to exception: {exc_val}")
        return False   # don't suppress exceptions

def keyboard_control(port: str):
    """
    Simple WASD to manually test the robot. like gaming type shi
    """
    print("\n── Manual Control Mode ──────────────────────────────")
    print("  W = Forward    P = Stop")
    print("  A = Left       D = Right")
    print("  S = Backward")
    print("  Q = Quit")
    print("─────────────────────────────────────────────────────\n")

    with SafeRobot(port) as robot:
        while True:
            try:
                raw = input("Command > ").strip().upper()
            except (EOFError, KeyboardInterrupt):
                print("\n[Control] Exiting.")
                break

            if not raw:
                continue

            key = raw[0]

            if key in ("W"):
                robot.forward()
            elif key in ("S"):
                robot.backward()
            elif key in ("A"):
                robot.left()
            elif key in ("D"):
                robot.right()
            elif key in ("P"):
                robot.stop()
            elif key == "Q":
                print("[Control] Quitting.")
                break
            else:
                print(f"[Control] Unknown key: '{key}'")

def milestone2_demo(port: str):
    """
    Demonstrates the milestone requirement:
    'Sending a 1 from Python makes the Arduino spin a motor.'
    Maps '1' → Forward for demo purposes.
    """
    print("[Demo] Sending '1' → Forward for 2 seconds, then Stop.")
    with SafeRobot(port) as robot:
        robot.send_raw("F")   # '1' maps to Forward in this demo
        time.sleep(2)
        robot.stop()
    print("[Demo] Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Arduino Robot Serial Controller")
    parser.add_argument("--port", required=True,
                        help="Serial port (e.g. COM3 or /dev/ttyACM0)")
    parser.add_argument("--demo", action="store_true",
                        help="Run Milestone 2 demo (send '1' → spin motor)")
    args = parser.parse_args()

    if args.demo:
        milestone2_demo(args.port)
    else:
        keyboard_control(args.port)
