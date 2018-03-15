import threading
import time
from bt_server import BtServer


def run_bt_server(android_conn, running):
    android_conn.run()
    while running:
        android_conn.accept()
        while running:
            data = android_conn.recv()
            if data is None:
                break
        android_conn.close_client()
    android_conn.close_server()


if __name__ == "__main__":
    running = True

    android_conn = BtServer(4)
    t2 = threading.Thread(target=run_bt_server,
                          args=(android_conn, running))

    t2.start()

    while running:
        msg = raw_input("Enter message: ")
        android_conn.send(msg)
