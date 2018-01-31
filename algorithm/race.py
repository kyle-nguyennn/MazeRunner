from Map import Map
import utils

def readInput():
    # for demonstration purpose, read input from console. For real system, this might read input from some connection
    input1 = input() # raw input with padding
    input2 = input()
    return Map(input1, input2) # TODO: implement constructor for merging 2 inputs in Map.py

if __name__ == "__main__":
    #map = readInput()
    map = utils.createMapTest()
    map = Map(map)
    map.get(6,2)