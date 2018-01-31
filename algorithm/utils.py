def getBit(x, i):
    return (x & (1 << i)) >> i

def setBit(x, i):
    return x | (1 << i)

def unsetBit(x, i):
    return x & ~(1 << i)

def createMapTest():
    file = open("C:\\Users\\nghia\\OneDrive\\CS\\Year 3 sem 2\\CZ3004 MDP\\MazeRunner\\MazeRunner\\algorithm\\mapTest.txt").read()
    map = file.split()
    map = "".join(map)
    map = int(map, 2)
    return map

if __name__ == "__main__":
    createMapTest()

# 400000001c800000000000700000000800000001f8000070000000002000000000
