from arena import Arena
import json

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
    map = Arena()
    for i in range(len(file)):
        s = file[i]
        for j in range(len(s)):
            map.set(i, j, int(s[j]))
    print(map.get_2d_arr())
    return(map)
# 400000001c800000000000700000000800000001f8000070000000002000000000

def parse_robot_config(path_to_config_file):
    file = open(path_to_config_file).read()
    return json.loads(file)

if __name__ == "__main__":
    a = parse_robot_config("./robot.conf")
    print(type(a))
    for sensor in a["sensors"]:
        print(sensor)


