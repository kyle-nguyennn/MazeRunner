from arena import CellType
class Sensor():
    def __init__(self, visible_range=3, sensor_pos=1, sensor_direction=0, robot_pos_h=1, robot_pos_w=1, robot_direction=0):
        self.visible_range = visible_range
        self.sensor_pos = sensor_pos
        self.sensor_direction = sensor_direction
        self.robot_pos_h = robot_pos_h
        self.robot_pos_w = robot_pos_w
        self.robot_direction = robot_direction

    def relative_pos(self):
        def rotate(arr, times):
            for time in range(times):
                temp = arr[0]
                del arr[0]
                arr.append(temp)
            return arr
        temp_sensors_offset = [(1,-1), (1,0), (1,1), (0,1), (-1,1), (-1,0), (-1,-1), (0,-1)]
        return rotate(temp_sensors_offset, int(2*self.robot_direction/90))[self.sensor_pos-1]

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
    def get_absolute_direction_mod4(self):
        print("inside sensor: robot direction ", self.robot_direction)
        print("inside sensor: sensor relative direction ", self.sensor_direction)
        print("inside sensor: sensor postition ", self.sensor_pos)
        print("inside sensor: sensor relative postition ", self.relative_pos())
        direction = (self.sensor_direction + self.robot_direction) % 360
        return self.direction_mod4(int(direction))

    def direction_mod4(self, direction):
        return {
            0: 0,
            90: 1,
            180: 2,
            270: 3
        }[direction]

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

        return self.visible_range
