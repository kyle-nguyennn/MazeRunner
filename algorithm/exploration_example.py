import socket
from arena import Arena, CellType
from random import randint
import time


class ExplorationExample():
    def __init__(self, tcp_ip, tcp_port, buffer_size=1024):

        self.arena = Arena()

        self.tcp_ip = tcp_ip
        self.tcp_port = tcp_port
        self.buffer_size = buffer_size
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        self.client_socket.connect((self.tcp_ip, self.tcp_port))
        print(
            "ExplorationExample - Connected to {}:{}".format(self.tcp_ip, self.tcp_port))
        self.send_data("startExplore")
        for i in range(10):

            self.recv_data()
            self.arena.set(randint(0, 19), randint(
                0, 14), CellType(randint(0, 1)))
            self.send_data("F")

            self.recv_data()
            self.arena.set(randint(0, 19), randint(
                0, 14), CellType(randint(0, 1)))
            self.send_data("R")

            self.recv_data()
            self.arena.set(randint(0, 19), randint(
                0, 14), CellType(randint(0, 1)))
            self.send_data("F")

            self.recv_data()
            self.arena.set(randint(0, 19), randint(
                0, 14), CellType(randint(0, 1)))
            self.send_data("L")

            self.recv_data()
            self.arena.set(randint(0, 19), randint(
                0, 14), CellType(randint(0, 1)))
            self.send_data("B")

            self.recv_data()
            self.arena.set(randint(0, 19), randint(
                0, 14), CellType(randint(0, 1)))
            self.send_data("L")

            self.recv_data()
            self.arena.set(randint(0, 19), randint(
                0, 14), CellType(
                    randint(0, 1)))
            self.send_data("F")
            self.recv_data()
            self.arena.set(randint(0, 19), randint(
                0, 14), CellType(randint(0, 1)))
            self.send_data("R")
        self.send_data("endExplore")  
        self.close_conn()

    def recv_data(self):
        data = self.client_socket.recv(self.buffer_size)
        data_s = data.decode('utf-8')
        print("ExplorationExample - Received data: {}".format(data_s))
        return data_s

    def send_data(self, data):
        self.client_socket.send(data.encode('utf-8'))

    def close_conn(self):
        self.client_socket.close()
        print("ExplorationExample - Connection cloased")

    def get_arena(self):
        return self.arena
