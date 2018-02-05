from Map import Map
def getBit(x, i):
    return (x & (1 << i)) >> i

def setBit(x, i):
    return x | (1 << i)

def unsetBit(x, i):
    return x & ~(1 << i)

# test map constructed according to example map in "Map descriptor format.pdf" page 2
def createMapTest():
    file = open("C:\\Users\\nghia\\OneDrive\\CS\\Year 3 sem 2\\CZ3004 MDP\\MazeRunner\\MazeRunner\\algorithm\\mapTest.txt").read()
    file = file.split()
    map = Map()
    for i in range(len(file)):
        s = file[i]
        for j in range(len(s)):
            map.set(i, j, int(s[j]))
    print(map.get2dArr())
    return(map)

if __name__ == "__main__":
    createMapTest()

# 400000001c800000000000700000000800000001f8000070000000002000000000
