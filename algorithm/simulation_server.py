from socket_server import TCPServer, TCPServerChild
from Map import Map, CellType
import time


class SimulatorServer(TCPServerChild):

    def run(self):
        self._map = Map()
        self._sensor = []
        self._sensor.append(Sensor(3, 1, 0))
        self._sensor.append(Sensor(3, 2, 0))
        self._sensor.append(Sensor(3, 3, 0))
        self._sensor.append(Sensor(3, 3, 90))
        self._sensor.append(Sensor(3, 5, 90))
        self._sensor.append(Sensor(8, 7, 270))
        self._robotPos = [1, 1, 0]
        self._map.fromMDFStrings("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF",
                                 "000000000400000001C800000000000700000000800000001F80000700000000020000000000")
        self._map.print()
        started = False
        while started == False:
            data = self.recv()
            if data.decode('utf-8') == "startExplore":
                started = True
                self.startExplore()

    def setMap(self, map):
        map.print()
        self._map = map

    def startExplore(self):
        end = False
        while end == False:
            self.socket.send(self.getReadings().encode('utf-8'))
            data = self.recv()
            command = data.decode('utf-8')
            print(command)
            for char in command:
                self.moveRobot(char)
            time.sleep(0.5)

    def moveRobot(self, action):

        if action == 'F':
            if self._robotPos[2] == 0:
                self._robotPos[0] += 1
            elif self._robotPos[2] == 90:
                self._robotPos[1] += 1
            elif self._robotPos[2] == 180:
                self._robotPos[0] -= 1
            elif self._robotPos[2] == 270:
                self._robotPos[1] -= 1

        if action == 'B':
            if self._robotPos[2] == 0:
                self._robotPos[0] -= 1
            elif self._robotPos[2] == 90:
                self._robotPos[1] -= 1
            elif self._robotPos[2] == 180:
                self._robotPos[0] += 1
            elif self._robotPos[2] == 270:
                self._robotPos[1] += 1

        elif action == 'R':
            self._robotPos[2] += 90

        elif action == 'L':
            self._robotPos[2] -= 90

        if self._robotPos[2] < 0:
            self._robotPos[2] += 360

        self._robotPos[2] = self._robotPos[2] % 360

    def getReadings(self):
        response = ""
        for sensor in self._sensor:
            sensor.setRobot(self._robotPos[0],
                            self._robotPos[1], self._robotPos[2])
            response += str(sensor.getReading(self._map))
        return response


class Sensor():
    def __init__(self, visible_range=3, sensor_pos=0, sensor_direction=0, robot_pos_h=1, robot_pos_w=1, robot_direction=0):
        self._visible_range = visible_range
        self._sensor_pos = sensor_pos
        self._sensor_direction = sensor_direction
        self._robot_pos_h = robot_pos_h
        self._robot_pos_w = robot_pos_w
        self._robot_direction = robot_direction

    def setRobot(self, robot_pos_h=1, robot_pos_w=1, robot_direction=0):
        self._robot_pos_h = robot_pos_h
        self._robot_pos_w = robot_pos_w
        self._robot_direction = robot_direction

    def getH(self):
        if self._robot_direction == 0:
            if self._sensor_pos == 1 or self._sensor_pos == 2 or self._sensor_pos == 3:
                return self._robot_pos_h + 1
            elif self._sensor_pos == 4 or self._sensor_pos == 8:
                return self._robot_pos_h
            elif self._sensor_pos == 5 or self._sensor_pos == 6 or self._sensor_pos == 7:
                return self._robot_pos_h - 1
        elif self._robot_direction == 90:
            if self._sensor_pos == 1 or self._sensor_pos == 7 or self._sensor_pos == 8:
                return self._robot_pos_h + 1
            elif self._sensor_pos == 2 or self._sensor_pos == 6:
                return self._robot_pos_h
            elif self._sensor_pos == 3 or self._sensor_pos == 4 or self._sensor_pos == 5:
                return self._robot_pos_h - 1
        elif self._robot_direction == 180:
            if self._sensor_pos == 1 or self._sensor_pos == 2 or self._sensor_pos == 3:
                return self._robot_pos_h - 1
            elif self._sensor_pos == 4 or self._sensor_pos == 8:
                return self._robot_pos_h
            elif self._sensor_pos == 5 or self._sensor_pos == 6 or self._sensor_pos == 7:
                return self._robot_pos_h + 1
        elif self._robot_direction == 270:
            if self._sensor_pos == 1 or self._sensor_pos == 7 or self._sensor_pos == 8:
                return self._robot_pos_h - 1
            elif self._sensor_pos == 2 or self._sensor_pos == 6:
                return self._robot_pos_h
            elif self._sensor_pos == 3 or self._sensor_pos == 4 or self._sensor_pos == 5:
                return self._robot_pos_h + 1

    def getW(self):
        if self._robot_direction == 0:
            if self._sensor_pos == 1 or self._sensor_pos == 7 or self._sensor_pos == 8:
                return self._robot_pos_w - 1
            elif self._sensor_pos == 2 or self._sensor_pos == 6:
                return self._robot_pos_w
            elif self._sensor_pos == 3 or self._sensor_pos == 4 or self._sensor_pos == 5:
                return self._robot_pos_w + 1
        elif self._robot_direction == 90:
            if self._sensor_pos == 1 or self._sensor_pos == 2 or self._sensor_pos == 3:
                return self._robot_pos_w + 1
            elif self._sensor_pos == 4 or self._sensor_pos == 8:
                return self._robot_pos_w
            elif self._sensor_pos == 5 or self._sensor_pos == 6 or self._sensor_pos == 7:
                return self._robot_pos_w - 1
        elif self._robot_direction == 180:
            if self._sensor_pos == 1 or self._sensor_pos == 7 or self._sensor_pos == 8:
                return self._robot_pos_w + 1
            elif self._sensor_pos == 2 or self._sensor_pos == 6:
                return self._robot_pos_w
            elif self._sensor_pos == 3 or self._sensor_pos == 4 or self._sensor_pos == 5:
                return self._robot_pos_w - 1
        elif self._robot_direction == 270:
            if self._sensor_pos == 1 or self._sensor_pos == 2 or self._sensor_pos == 3:
                return self._robot_pos_w - 1
            elif self._sensor_pos == 4 or self._sensor_pos == 8:
                return self._robot_pos_w
            elif self._sensor_pos == 5 or self._sensor_pos == 6 or self._sensor_pos == 7:
                return self._robot_pos_w + 1

    def getDirection(self):
        direction = self._sensor_direction + self._robot_direction
        return direction % 360

    def getReading(self, map):

        for x in range(self._visible_range):
            if self.getDirection() == 0:
                blockH = self.getH()+x+1
                blockW = self.getW()
            elif self.getDirection() == 90:
                blockH = self.getH()
                blockW = self.getW()+x+1
            elif self.getDirection() == 180:
                blockH = self.getH()-x-1
                blockW = self.getW()
            elif self.getDirection() == 270:
                blockH = self.getH()
                blockW = self.getW()-x-1

            if blockH < 0 or blockW < 0 or blockH > 19 or blockW > 14:
                return x
            elif map.get(blockH, blockW) == CellType.OBSTACLE:
                return x

        return 'Z'
