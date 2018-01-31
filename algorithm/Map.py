import logging
logging.basicConfig(filename=__file__+".log" ,level=logging.DEBUG)
import utils
class Map():
    # already have a internal map
    def __init__ (self, map, row=20, col=15):
        self._row = row
        self._col = col
        self._map = map

    @classmethod
    def constructMap(cls, part1, part2, row=20, col=15):
        self._row = row
        self._col = col
        bitStr1 = str(bin(int(part1, 16)))[2:] # exlcude the "0b" in front of the bit strings
        bitStr2 = str(bin(int(part2, 16)))[2:]
        # TODO: construct an integer representation of map from bitStr1 and bitStr2
        map = 0
        return cls(map)


    def toHexString(self, withPadding=True):
        map = self._map
        if withPadding:
            binStr = str(bin(self._map))[2:]
            binStr = "11"+binStr+"11"
            map = int(binStr, 2)
        return str(hex(map))[2:].upper() # exclude the "0x" in front of the hex string

    def print(self):
        binstring = str(bin(self._map))[2:]
        while len(binstring) < self._row*self._col:
            binstring = '0'+binstring
        for i in range (self._row):
            row = binstring[i*self._col:(i+1)*self._col]
            for j in range (self._col):
                print(row[j], end=" ")
            print()

    # read the content in position (x, y). map is the integer representation of the 300-bit string (20x15)
    def get(self, x, y):
        if x < 1 | x > self._row | y < 1 | y < self._col:
            print("ERROR: index out of range.")
            return -1
        offset = self._row*self._col-(self._col*(x-1)+y)
        val = utils.getBit(self._map, offset)
        print("Bin array representation of map:")
        self.print()
        print("Value at ({},{}): ".format(x,y) + str(val))
        return val

    def set(self, x, y):
        if x < 1 | x > self._row | y < 1 | y < self._col:
            print("ERROR: index out of range.")
            return -1
        print("Before set:")
        self.print()
        offset = self._row*self._col-(self._col*(x-1)+y)
        self._map = utils.setBit(self._map, offset)
        print("After set:")
        self.print()

    def unset(self, x, y):
        if x < 1 | x > self._row | y < 1 | y < self._col:
            print("ERROR: index out of range.")
            return -1
        print("Before unset:")
        self.print()
        offset = self._row*self._col-(self._col*(x-1)+y)
        self._map = utils.unsetBit(self._map, offset)
        print("After unset:")
        self.print()

#test program with 3x4 map
if __name__ == "__main__":
    map = Map("BCF", 3, 4, False)
    map.get(2,3)
    map.print()
    map.set(2,3)
    map.unset(2,3)
    newMap = Map("EF3F", 3, 4) # with padding as default
    newMap.get(2,3)
    print(newMap.toHexString())