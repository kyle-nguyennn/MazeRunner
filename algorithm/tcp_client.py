import socket
import multiprocessing
import json
import threading

send_queue = multiprocessing.Queue()
recv_json_queue = multiprocessing.Queue()
recv_string_queue = multiprocessing.Queue()


class TcpClient():
    def __init__(self, ip, port, buffer_size=1024):
        self.ip = ip
        self.port = port
        self.buffer_size = buffer_size
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        self.connect()
        send_thread = threading.Thread(target=self.send)
        send_thread.start()
        recv_thread = threading.Thread(target=self.recv)
        recv_thread.start()

    def connect(self):
        self.client_socket.connect((self.ip, self.port))
        self.connected = True
        print("TcpClient - Connected on {}:{}".format(self.ip, self.port))

    def recv(self):
        global recv_json_queue
        global recv_string_queue
        while self.connected:
            try:
                data = self.client_socket.recv(self.buffer_size)
            except:
                self.close_conn()
                break
            if not data:
                self.close_conn()
                break
            data_s = data.decode('utf-8')
            print("TcpClient - Received data: {}".format(data_s))
            if data_s[0] == "{":
                recv_json_queue.put(data_s)
            else:
                recv_string_queue.put(data_s)

    def send(self):
        global send_queue
        while self.connected:
            if not send_queue.empty():
                try:
                    data = send_queue.get()
                    self.client_socket.send(data.encode('utf-8'))
                    print("TcpClient - Sent data: {}".format(data))
                except:
                    print("TcpClient - Error sending data: {}".format(data))
                    self.close_conn()
                    break

    def get_json(self):
        global recv_json_queue
        while recv_json_queue.empty() and self.connected:
            pass
        return recv_json_queue.get()

    def get_string(self):
        global recv_string_queue
        while recv_string_queue.empty():
            pass
        return recv_string_queue.get()

    def send_command(self, command):
        global send_queue
        send_queue.put(command)

    def send_status(self, status):
        global send_queue
        send_queue.put(json.dumps({"status": status}))

    def close_conn(self):
        try:
            self.client_socket.close()
            self.connected = False
            print("TcpClient - Disconnected")
        except:
            pass
