import threading
import time
from tcp_server import TcpServer
from bt_server import BtServer
from serial_client import SerialClient
import Queue

pc_queue = Queue.Queue()
android_queue = Queue.Queue()
arduino_queue = Queue.Queue()


def run_tcp_server(ip, port):
    global running
    global pc_conn
    global android_queue
    global arduino_queue
    pc_conn = TcpServer(ip, port)
    pc_conn.run()
    while running:
        pc_conn.accept()
        while running:
            data = pc_conn.recv()
            if data is None:
                break
            data_arr = data.splitlines()
            for data_s in data_arr:
                if data_s[0] == "{":
                    android_queue.put(data_s)
                else:
                    arduino_queue.put(data_s)
        pc_conn.close_client()
    pc_conn.close_server()


def run_bt_server(channel):
    global running
    global android_conn
    global pc_queue
    global arduino_queue
    android_conn = BtServer(channel)
    android_conn.run()
    while running:
        android_conn.accept()
        while running:
            data = android_conn.recv()
            if data is None:
                break
            data_arr = data.splitlines()
            for data_s in data_arr:
                if data_s[0] == "{":
                    pc_queue.put(data_s)
                else:
                    arduino_queue.put(data_s)
        android_conn.close_client()
    android_conn.close_server()


def run_serial_client(port, baud_rate):
    global running
    global arduino_conn
    global pc_queue
    arduino_conn = SerialClient(port, baud_rate)
    while running:
        connected = False
        while not connected and running:
            connected = arduino_conn.connect()
        while running:
            data = arduino_conn.recv()
            if data is None:
                break
            data_arr = data.splitlines()
            for data_s in data_arr:
                pc_queue.put(data_s)
        arduino_conn.close_conn()


def send_tcp_server():
    global running
    global pc_conn
    global pc_queue
    while running:
        if not pc_queue.empty():
            pc_conn.send(pc_queue.get())


def send_bt_server():
    global running
    global android_conn
    global android_queue
    while running:
        if not android_queue.empty():
            android_conn.send(android_queue.get())


def send_serial_client():
    global running
    global arduino_conn
    global arduino_queue
    while running:
        if not arduino_queue.empty():
            arduino_conn.send(arduino_queue.get())


if __name__ == "__main__":
    global running
    running = True
    t1 = threading.Thread(target=run_bt_server, args=(4,))
    t2 = threading.Thread(target=run_tcp_server, args=("0.0.0.0", 77))
    t3 = threading.Thread(target=run_serial_client,
                          # args=("/dev/ttyACM0", 9600))
                          args=("/dev/ttyAMA0", 9600))
    t4 = threading.Thread(target=send_tcp_server)
    t5 = threading.Thread(target=send_bt_server)
    t6 = threading.Thread(target=send_serial_client)
    # t1.setDaemon(True)
    # t2.setDaemon(True)
    # t3.setDaemon(True)
    # t4.setDaemon(True)
    # t5.setDaemon(True)
    # t6.setDaemon(True)
    t1.start()
    t2.start()
    t3.start()
    t4.start()
    t5.start()
    t6.start()

    try:
        time.sleep(1)
        raw_input("Press Enter / Ctrl-C to quit. \n")
        running = False
    except KeyboardInterrupt:
        running = False

    t1.join()
    t2.join()
    t3.join()
    t4.join()
    t5.join()
    t6.join()
