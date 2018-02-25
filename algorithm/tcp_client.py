import socket
import multiprocessing
import json
import threading


class TcpClient():
    def __init__(self, ip, port, buffer_size=1024):
        self.ip = ip
        self.port = port
        self.buffer_size = buffer_size
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.send_queue = multiprocessing.Queue()
        self.recv_json_queue = multiprocessing.Queue()
        self.recv_string_queue = multiprocessing.Queue()

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
                self.recv_json_queue.put(data_s)
            else:
                self.recv_string_queue.put(data_s)

    def send(self):
        while self.connected:
            if not self.send_queue.empty():
                try:
                    data = self.send_queue.get()
                    self.client_socket.send(data.encode('utf-8'))
                    print("TcpClient - Sent data: {}".format(data))
                except:
                    print("TcpClient - Error sending data: {}".format(data))
                    self.close_conn()
                    break

    def get_json(self):
        while self.recv_json_queue.empty() and self.connected:
            pass
        return self.recv_json_queue.get()

    def get_string(self):
        while self.recv_string_queue.empty():
            pass
        return self.recv_string_queue.get()

    def send_command(self, command):
        self.send_queue.put(command)

    def send_status(self, status):
        self.send_queue.put(json.dumps({"status": status}))

    def send_robot_pos(self, pos):
        self.send_queue.put(json.dumps({"robotPos": pos}))

    def send_arena(self, arena):
        self.send_queue.put(json.dumps(
            {"gridP1": arena.to_mdf_part1(), "gridP2": arena.to_mdf_part2()}))

    def close_conn(self):
        try:
            self.client_socket.close()
            self.connected = False
            print("TcpClient - Disconnected")
        except:
            pass
