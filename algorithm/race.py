from Map import Map
import utils

def readInput():
    # for demonstration purpose, read input from console. For real system, this might read input from some connection
    input1 = input() # raw input with padding
    input2 = input()
    return Map(input1, input2) # TODO: implement constructor for merging 2 inputs in Map.py

def getDirection(map, x, y, robotsize=(3,3)):
    map.print()
    instruction = ""

    return instruction

def dijkstra():
    
if __name__ == "__main__":
    #map = readInput()
    map = utils.createMapTest()
    map = Map(map)
    instruction = getDirection(map, 5, 6)
    print(instruction)