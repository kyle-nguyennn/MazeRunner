import socket
import multiprocessing
import threading
from arena import Arena, CellType
import time
import json
from sensor import Sensor
from utils import parse_robot_config

class SimulatorServer():

    def __init__(self, tcp_ip, tcp_port, arena_obj, robot_pos, speed, buffer_size=1024):

        self.arena = arena_obj
        self.sensor = []
        sensors = parse_robot_config("./robot.conf")
        for sensor in sensors["sensors"]:
            self.sensor.append(Sensor(sensor["max_range"], sensor["position"], sensor["orientation"]))
        self.robot_pos = robot_pos

        self.speed = speed
        self.tcp_ip = tcp_ip
        self.tcp_port = tcp_port
        self.buffer_size = buffer_size
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.recv_queue = multiprocessing.Queue()

    def run(self):
        self.running = True
        self.server_socket.bind((self.tcp_ip, self.tcp_port))
        self.server_socket.listen(1)
        print("SimulatorServer - Listening on {}:{}".format(self.tcp_ip, self.tcp_port))
        self.client_conn, addr = self.server_socket.accept()
        print(
            "SimulatorServer - Accepted connection from {}:{}".format(addr[0], addr[1]))
        started = False
        recv_thread = threading.Thread(target=self.recv_data)
        recv_thread.start()
        self.send_data(json.dumps(
            {"command": "beginExplore", "robotPos": self.robot_pos}))
        # self.send_data(json.dumps({"command": "autoStart"}))
        while not started:
            data = self.get_command()
            if data == "ES":
                started = True
                self.start_explore()

    def recv_data(self):
        while self.running:
            try:
                data = self.client_conn.recv(self.buffer_size)
            except:
                self.close_conn()
                break
            if not data:
                self.close_conn()
                break
            data_s = data.decode('utf-8')
            print("SimulatorServer - Received data: {}".format(data_s))
            if data_s[0] != "{":
                self.recv_queue.put(data_s)

    def send_data(self, data):
        self.client_conn.send(data.encode('utf-8'))

    def close_conn(self):
        self.running = False
        self.client_conn.close()
        self.server_socket.close()
        print("SimulatorServer - Connection closed")

    def get_command(self):
        while self.recv_queue.empty():
            pass
        return self.recv_queue.get()

    def set_arena(self, arena):
        arena.print()
        self.arena = arena

    def start_explore(self):
        self.send_data(self.getReadings())
        while self.running:
            command = self.get_command()
            if command == None or command == "EE":
                self.close_conn()
            elif command[0] == "C":
                pass
            elif command == "N":
                self.send_data(self.getReadings())
                pass
            else:
                for char in command:
                    self.move_robot(char)
                    time.sleep(self.speed)
                    self.send_data(self.getReadings())

    def move_robot(self, action):

        if action == 'F':
            if self.robot_pos[2] == 0:
                self.robot_pos[0] += 1
            elif self.robot_pos[2] == 90:
                self.robot_pos[1] += 1
            elif self.robot_pos[2] == 180:
                self.robot_pos[0] -= 1
            elif self.robot_pos[2] == 270:
                self.robot_pos[1] -= 1

        if action == 'B':
            if self.robot_pos[2] == 0:
                self.robot_pos[0] -= 1
            elif self.robot_pos[2] == 90:
                self.robot_pos[1] -= 1
            elif self.robot_pos[2] == 180:
                self.robot_pos[0] += 1
            elif self.robot_pos[2] == 270:
                self.robot_pos[1] += 1

        elif action == 'R':
            self.robot_pos[2] += 90

        elif action == 'L':
            self.robot_pos[2] -= 90

        if self.robot_pos[2] < 0:
            self.robot_pos[2] += 360

        self.robot_pos[2] = self.robot_pos[2] % 360

    def getReadings(self):
        response = ""
        for sensor in self.sensor:
            sensor.set_robot(self.robot_pos[0],
                             self.robot_pos[1], self.robot_pos[2])
            response += str(sensor.get_reading(self.arena))
        return response

    def get_robot(self):
        if self.running:
            return self.robot_pos
        return None