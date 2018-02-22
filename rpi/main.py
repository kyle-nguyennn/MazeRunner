import threading
import time
from tcp_server import TcpServer
from bt_server import BtServer
from serial_client import SerialClient


def run_tcp_server(ip, port):
    global running
    global pc_conn
    global android_conn
    global arduino_conn
    pc_conn = TcpServer(ip, port)
    pc_conn.run()
    while(running):
        pc_conn.accept()
        while(running):
            data = pc_conn.recv()
            if data is None:
                break
            if data[0] == "{":
                android_conn.send(data)
            else:
                arduino_conn.send(data)
        pc_conn.close_client()
    pc_conn.close_server()


def run_bt_server(channel):
    global running
    global pc_conn
    global android_conn
    global arduino_conn
    android_conn = BtServer(channel)
    android_conn.run()
    while(running):
        android_conn.accept()
        while(running):
            data = android_conn.recv()
            if data is None:
                break
            if data[0] == "{":
                pc_conn.send(data)
            else:
                arduino_conn.send(data)
        android_conn.close_client()
    android_conn.close_server()


def run_serial_client(port, baud_rate):
    global running
    global pc_conn
    global android_conn
    global arduino_conn
    arduino_conn = SerialClient(port, baud_rate)
    while(running):
        arduino_conn.connect()
        while(running):
            data = arduino_conn.recv()
            if data is None:
                break
            pc_conn.send(data)
        arduino_conn.close_conn()


if __name__ == "__main__":
    global running
    running = True
    t1 = threading.Thread(target=run_bt_server, args=(4,))
    t1.start()
    t2 = threading.Thread(target=run_tcp_server, args=("0.0.0.0", 77))
    t2.start()
    t3 = threading.Thread(target=run_serial_client, args=("/dev/ttyACM0", 9600))
    t3.start()
    try:
        time.sleep(1)
        raw_input("Press enter to quit \n")
        running = False
    except KeyboardInterrupt:
        running = False
    t1.join()
    t2.join()
    t3.join()
