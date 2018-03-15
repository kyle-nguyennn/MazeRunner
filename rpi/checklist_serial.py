import threading
import time
from serial_client import SerialClient


def run_serial_client(arduino_conn, running):
    while running:
        connected = False
        while not connected and running:
            connected = arduino_conn.connect()
        while running:
            data = arduino_conn.recv()
            if data is None:
                break
        arduino_conn.close_conn()


if __name__ == "__main__":
    running = True

    arduino_conn = SerialClient("/dev/ttyACM0", 9600)

    t3 = threading.Thread(target=run_serial_client,
                          args=(arduino_conn, running))
    t3.start()

    while running:
        msg = raw_input("Enter message: ")
        arduino_conn.send(msg)
