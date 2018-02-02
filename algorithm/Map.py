import logging
from enum import Enum
import algorithm.utils

if __name__ == "__main__":
    logging.basicConfig(filename=__file__+".log", level=logging.DEBUG)


class Map():
    # already have a internal map
    def __init__(self, height=20, width=15):
        self._map = [[-1 for y in range(width)] for x in range(height)]

    def fromMDFStrings(self, part1, part2):

        b1Size = len(part1) * 4
        bitStr1 = (bin(int(part1, 16))[4:b1Size]).zfill(b1Size-4)

        b2Size = len(part2) * 4
        bitStr2 = (bin(int(part2, 16))[2:b2Size]).zfill(b2Size)

        for x in range(len(self._map)):
            for y in range(len(self._map[x])):
                if bitStr1[(x*len(self._map[x]))+y] == "0":
                    self._map[x][y] = -1
                else:
                    self._map[x][y] = 0

        bitCount = 0

        for x in range(len(self._map)):
            for y in range(len(self._map[x])):
                if self._map[x][y] == 0:
                    self._map[x][y] = int(bitStr2[bitCount])
                    bitCount += 1

        return

    def toMDFPart1(self, withPadding=True):
        map = self._map

        bitStr = ""

        for x in range(len(map)):
            for y in range(len(map[x])):
                if map[x][y] == -1:
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
                if map[x][y] == 0:
                    bitStr += "0"
                elif map[x][y] == 1:
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
                print(self._map[x][y], end=" ")
            print()

    def get(self, x, y):
        return self._map[x][y]

    def set(self, x, y, value):
        self._map[x][y] = value


# test program with 3x4 map
if __name__ == "__main__":
    map = Map("BCF", 3, 4, False)
    map.get(2, 3)
    map.print()
    map.set(2, 3)
    map.unset(2, 3)
    newMap = Map("EF3F", 3, 4)  # with padding as default
    newMap.get(2, 3)
    print(newMap.toHexString())
