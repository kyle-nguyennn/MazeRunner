import logging
from enum import Enum

if __name__ == "__main__":
    logging.basicConfig(filename=__file__+".log", level=logging.DEBUG)


class Map():
    # already have a internal map
    def __init__(self, height=20, width=15):
        self._map = [[CellType.UNKNOWN
                      for y in range(width)]
                     for x in range(height)]

    def fromMDFStrings(self, part1, part2):

        b1Size = len(part1) * 4
        bitStr1 = (bin(int(part1, 16))[4:b1Size]).zfill(b1Size-4)

        b2Size = len(part2) * 4
        bitStr2 = (bin(int(part2, 16))[2:b2Size]).zfill(b2Size-2)

        for x in range(len(self._map)):
            for y in range(len(self._map[x])):
                if bitStr1[(x*len(self._map[x]))+y] == "0":
                    self._map[x][y] = CellType.UNKNOWN
                else:
                    self._map[x][y] = CellType.EMPTY

        bitCount = 0

        for x in range(len(self._map)):
            for y in range(len(self._map[x])):
                if self._map[x][y] == CellType.EMPTY:
                    self._map[x][y] = CellType(int(bitStr2[bitCount]))
                    bitCount += 1

        return

    def toMDFPart1(self, withPadding=True):
        map = self._map

        bitStr = ""

        for x in range(len(map)):
            for y in range(len(map[x])):
                if map[x][y] == CellType.UNKNOWN:
                    bitStr += "0"
                else:
                    bitStr += "1"

        if withPadding:
            bitStr = "11" + bitStr + "11"

        return '{:0{}X}'.format(int(bitStr, 2), len(bitStr) // 4)

    def toMDFPart2(self, withPadding=True):
        map = self._map

        bitStr = ""

        for x in range(len(map)):
            for y in range(len(map[x])):
                if map[x][y] == CellType.EMPTY:
                    bitStr += "0"
                elif map[x][y] == CellType.OBSTACLE:
                    bitStr += "1"

        if withPadding:
            toPad = 8 - len(bitStr) % 8
            for i in range(toPad):
                bitStr += "0"

        return '{:0{}X}'.format(int(bitStr, 2), len(bitStr) // 4)

    def get2dArr(self):
        return self._map

    def print(self):
        for x in range(len(self._map)):
            for y in range(len(self._map[x])):
                print(self._map[x][y].value, end=" ")
            print()

    def get(self, x, y):
        return self._map[x][y]

    def set(self, x, y, value):
        self._map[x][y] = value


class CellType(Enum):
    UNKNOWN = -1
    EMPTY = 0
    OBSTACLE = 1
