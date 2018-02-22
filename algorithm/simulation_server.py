import socket
from arena import Arena, CellType
import time
import json


class SimulatorServer():

    def __init__(self, tcp_ip, tcp_port, arena_obj, speed, buffer_size=1024):

        self.arena = arena_obj
        self.sensor = []
        self.sensor.append(Sensor(3, 1, 0))
        self.sensor.append(Sensor(3, 2, 0))
        self.sensor.append(Sensor(3, 3, 0))
        self.sensor.append(Sensor(3, 3, 90))
        self.sensor.append(Sensor(3, 5, 90))
        self.sensor.append(Sensor(8, 7, 270))
        self.robot_pos = [1, 1, 0]

        self.speed = speed
        self.tcp_ip = tcp_ip
        self.tcp_port = tcp_port
        self.buffer_size = buffer_size
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        self.server_socket.bind((self.tcp_ip, self.tcp_port))
        self.server_socket.listen(1)
        print("SimulatorServer - Listening on {}:{}".format(self.tcp_ip, self.tcp_port))
        self.client_conn, addr = self.server_socket.accept()
        print(
            "SimulatorServer - Accepted connection from {}:{}".format(addr[0], addr[1]))
        started = False
        self.send_data(json.dumps({"command": "beginExplore"}))
        while not started:
            data = self.recv_data()
            if data == "startExplore":
                started = True
                self.start_explore()

    def recv_data(self):
        data = self.client_conn.recv(self.buffer_size)
        if not data:
            return None
        data_s = data.decode('utf-8')
        print("SimulatorServer - Received data: {}".format(data_s))
        return data_s

    def send_data(self, data):
        self.client_conn.send(data.encode('utf-8'))

    def close_conn(self):
        self.client_conn.close()
        self.server_socket.close()
        print("SimulatorServer - Connection cloased")

    def set_arena(self, arena):
        arena.print()
        self.arena = arena

    def start_explore(self):
        end = False
        while end == False:
            self.send_data(self.getReadings())
            command = self.recv_data()
            if command == None or command == "endExplore":
                self.close_conn()
                end = True
            else:
                for char in command:
                    self.move_robot(char)
                time.sleep(self.speed)

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


class Sensor():
    def __init__(self, visible_range=3, sensor_pos=0, sensor_direction=0, robot_pos_h=1, robot_pos_w=1, robot_direction=0):
        self.visible_range = visible_range
        self.sensor_pos = sensor_pos
        self.sensor_direction = sensor_direction
        self.robot_pos_h = robot_pos_h
        self.robot_pos_w = robot_pos_w
        self.robot_direction = robot_direction

    def set_robot(self, robot_pos_h=1, robot_pos_w=1, robot_direction=0):
        self.robot_pos_h = robot_pos_h
        self.robot_pos_w = robot_pos_w
        self.robot_direction = robot_direction

    def get_h(self):
        if self.robot_direction == 0:
            if self.sensor_pos == 1 or self.sensor_pos == 2 or self.sensor_pos == 3:
                return self.robot_pos_h + 1
            elif self.sensor_pos == 4 or self.sensor_pos == 8:
                return self.robot_pos_h
            elif self.sensor_pos == 5 or self.sensor_pos == 6 or self.sensor_pos == 7:
                return self.robot_pos_h - 1
        elif self.robot_direction == 90:
            if self.sensor_pos == 1 or self.sensor_pos == 7 or self.sensor_pos == 8:
                return self.robot_pos_h + 1
            elif self.sensor_pos == 2 or self.sensor_pos == 6:
                return self.robot_pos_h
            elif self.sensor_pos == 3 or self.sensor_pos == 4 or self.sensor_pos == 5:
                return self.robot_pos_h - 1
        elif self.robot_direction == 180:
            if self.sensor_pos == 1 or self.sensor_pos == 2 or self.sensor_pos == 3:
                return self.robot_pos_h - 1
            elif self.sensor_pos == 4 or self.sensor_pos == 8:
                return self.robot_pos_h
            elif self.sensor_pos == 5 or self.sensor_pos == 6 or self.sensor_pos == 7:
                return self.robot_pos_h + 1
        elif self.robot_direction == 270:
            if self.sensor_pos == 1 or self.sensor_pos == 7 or self.sensor_pos == 8:
                return self.robot_pos_h - 1
            elif self.sensor_pos == 2 or self.sensor_pos == 6:
                return self.robot_pos_h
            elif self.sensor_pos == 3 or self.sensor_pos == 4 or self.sensor_pos == 5:
                return self.robot_pos_h + 1

    def get_w(self):
        if self.robot_direction == 0:
            if self.sensor_pos == 1 or self.sensor_pos == 7 or self.sensor_pos == 8:
                return self.robot_pos_w - 1
            elif self.sensor_pos == 2 or self.sensor_pos == 6:
                return self.robot_pos_w
            elif self.sensor_pos == 3 or self.sensor_pos == 4 or self.sensor_pos == 5:
                return self.robot_pos_w + 1
        elif self.robot_direction == 90:
            if self.sensor_pos == 1 or self.sensor_pos == 2 or self.sensor_pos == 3:
                return self.robot_pos_w + 1
            elif self.sensor_pos == 4 or self.sensor_pos == 8:
                return self.robot_pos_w
            elif self.sensor_pos == 5 or self.sensor_pos == 6 or self.sensor_pos == 7:
                return self.robot_pos_w - 1
        elif self.robot_direction == 180:
            if self.sensor_pos == 1 or self.sensor_pos == 7 or self.sensor_pos == 8:
                return self.robot_pos_w + 1
            elif self.sensor_pos == 2 or self.sensor_pos == 6:
                return self.robot_pos_w
            elif self.sensor_pos == 3 or self.sensor_pos == 4 or self.sensor_pos == 5:
                return self.robot_pos_w - 1
        elif self.robot_direction == 270:
            if self.sensor_pos == 1 or self.sensor_pos == 2 or self.sensor_pos == 3:
                return self.robot_pos_w - 1
            elif self.sensor_pos == 4 or self.sensor_pos == 8:
                return self.robot_pos_w
            elif self.sensor_pos == 5 or self.sensor_pos == 6 or self.sensor_pos == 7:
                return self.robot_pos_w + 1

    def get_direction(self):
        direction = self.sensor_direction + self.robot_direction
        return direction % 360

    def get_reading(self, map):

        for x in range(self.visible_range):
            if self.get_direction() == 0:
                block_h = self.get_h()+x+1
                block_w = self.get_w()
            elif self.get_direction() == 90:
                block_h = self.get_h()
                block_w = self.get_w()+x+1
            elif self.get_direction() == 180:
                block_h = self.get_h()-x-1
                block_w = self.get_w()
            elif self.get_direction() == 270:
                block_h = self.get_h()
                block_w = self.get_w()-x-1

            if block_h < 0 or block_w < 0 or block_h > 19 or block_w > 14:
                return x
            elif map.get(block_h, block_w) == CellType.OBSTACLE:
                return x

        return 'Z'
