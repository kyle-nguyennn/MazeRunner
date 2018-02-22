import socket
from arena import Arena, CellType
from random import randint
from tcp_client import TcpClient
import time


class ExplorationExample():
    def __init__(self, tcp_conn):
        self.running = False
        self.arena = Arena()
        self.robot = [1, 1, 0]
        self.tcp_conn = tcp_conn

    def run(self):
        self.running = True
        self.tcp_conn.send("startExplore")
        for i in range(10):

            self.tcp_conn.recv()
            self.random_state()
            self.tcp_conn.send("F")

            self.tcp_conn.recv()
            self.random_state()
            self.tcp_conn.send("R")

            self.tcp_conn.recv()
            self.random_state()
            self.tcp_conn.send("F")

            self.tcp_conn.recv()
            self.random_state()
            self.tcp_conn.send("L")

            self.tcp_conn.recv()
            self.random_state()
            self.tcp_conn.send("B")

            self.tcp_conn.recv()
            self.random_state()
            self.tcp_conn.send("L")

            self.tcp_conn.recv()
            self.random_state()
            self.tcp_conn.send("F")

            self.tcp_conn.recv()
            self.random_state()
            self.tcp_conn.send("R")

        self.tcp_conn.send("endExplore")
        self.running = False
        #self.close_conn()

    def random_state(self):
        self.arena.set(randint(0, 19), randint(0, 14), CellType(randint(0, 1)))
        self.robot = [randint(1, 18), randint(1, 13), randint(0, 3)*90]

    def get_arena(self):
        if self.running:
            return self.arena
        else:
            return None

    def get_robot(self):
        return self.robot
