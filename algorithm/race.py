from arena import Arena, CellType
import utils

def detectCollision(mymap, pos, robotsize=(3,3)): #take care of robot size in here, outside of this function the robot is treated as a 1x1 object
    # pos is the middle cell (for 3x3) that the robot takes
    # treat the system as the collecitons of all the point that the robot covers
    (x,y) = pos
    system = [pos, (x+1, y), (x+1, y+1), (x, y+1), (x-1, y+1), (x-1, y), (x-1, y-1), (x, y-1), (x+1, y-1)]
    for p in system:
        # collide with walls
        if p[0] < 0 or p[0] >= len(mymap) or p[1] < 0 or p[1] >= len(mymap[0]):
            return True
        # there is obstacle at p
        if mymap[p[0]][p[1]] == CellType.OBSTACLE: 
            return True
    return False

def neighbors(mymap, cur): # cur is (x,y,d)
    '''
    return a list of neightbor
    each neighbor have the data structure: (neighborPos, moveCost, move)
    '''
    def elementWiseAdd(a, b):
        return tuple([sum(x) for x in zip(a, b)])
    x, y, d = cur
    offsets_n = [(1,0), (0,1), (-1,0), (0,-1)]
    offsets_e = [(0,1), (-1,0), (0,-1), (1,0)]
    offsets_s = [(-1,0), (0,-1), (1,0), (0,1)]
    offsets_w = [(0,-1), (1,0), (0,1), (-1,0)]
    offsets = {
        0: offsets_n,
        1: offsets_e,
        2: offsets_s,
        3: offsets_w
    }[d]

    neighbors = []
    for i in range(1,4): # add states can achieved by stand still and turn
        neighbor_pos = (x,y, (d+i)%4)
        if i == 2:
            moveCost = 2
        else:
            moveCost = 1
        move = {
            1: "R",
            2: "RR",
            3: "L"
        }[i]
        neighbors.append((neighbor_pos, moveCost, move))
    ############## TODO: add states achieved by moving to neighbor cells and optional turn
    for i in range(len(offsets)):
        (neighborX, neighborY) = elementWiseAdd((x,y), offsets[i])
        if i != 2:
            neighborD = (d+i)%4
        else:
            neighborD = d
        neighborPos = (neighborX, neighborY, neighborD)
        (moveCost, move) = {
            0: (1, "F"),
            1: (2, "RF"),
            2: (1, "B"),
            3: (2, "LF")
        }[i]
        if i == 0 or i == 2: # only allow moving forward or backward
            neighbors.append((neighborPos, moveCost, move))
    return neighbors

def popMin(costs):
    k = min(costs, key=costs.get)
    cur = k
    curCost = costs[k]
    del costs[k]
    return (cur, curCost)
def dijkstra(mymap, start, end, endOrientationImportant = False):
    ''' 
    return: tuple of instruction string with the final orientation of the robot after executing these instructions
    param:
        mymap: 2d array of CellType representing the map
        start: triple of the start position including x,y coordinates and the orientation
        end: end position, same data structure as start
    '''
    costs = {}  # a dict storing with key is the state and value is the cost of the path that leads to it
                # structure of each element is: (x,y,d):cost
    prev = {}   # k:v == (x,y,d): ((xx, yy, dd), move_to_go_next),
                # where from (xx, yy, dd) the robot takes move_to_go_next and end up in (x, y, d)
    # initialise(costs, start)  # set all the costs to infinity, except for the start state
    for x in range(len(mymap)):
        for y in range(len(mymap[0])):
            for d in range(4):
                costs[(x,y,d)] = 1000
    costs[start] = 0
    if endOrientationImportant:
        compareEndUntil = None
    else:
        compareEndUntil = -1
    while True:
        cur, curCost = popMin(costs)    # get the item with min cost and remove it from the dict
        # if end == (18, 13, 0):
        #     print("in djikstra: cur ", cur, curCost)
        if cur[:compareEndUntil] == end[:compareEndUntil]:
            # store the final minimal cost if needed
            # trace back the path here
            temp = cur
            path = [(cur, "")]
            # print("In djikstra: on end: prev", prev)
            while prev.get(temp) != None:
                p = prev[temp]
                path.insert(0, p)
                temp = p[0]
            ins = ""
            for item in path:
                ins += item[1]
            return (ins, cur)
        for neighbor in neighbors(mymap, cur):
            neighborPos, moveCost, move = neighbor
            if not detectCollision(mymap, neighborPos[:-1]):
                if costs.get(neighborPos) != None: # has not been popped out (cost fixed)
                    if costs[neighborPos] > curCost + moveCost:
                        costs[neighborPos] = curCost + moveCost
                        prev[neighborPos] = (cur, move)

def getInstructions(map, waypoint, robotsize=(3,3), direction='north'):
    map.print()
    dir = 0
    if direction[0] == "n":
        dir = 0
    if direction[0] == "e":
        dir = 1
    if direction[0] == "s":
        dir = 2
    if direction[0] == "w":
        dir = 3
    instruction = ""
    mymap = map.get_2d_arr()
    waypoint = (waypoint[0], waypoint[1], 0) # padding 0 at the 3rd position to make it work with djikstra
    (instruction1, endpoint1) = dijkstra(mymap, (1, 1, dir), waypoint, endOrientationImportant = False)
    print("In getInstruction: reached waypoint", endpoint1)
    (instruction2, endpoint2) = dijkstra(mymap, endpoint1, (18,13, 0), endOrientationImportant = False)
    print("nothing in your eyes", instruction2, endpoint2)
    print("In getInstruction: reached goal")
    print(instruction1+instruction2)
    return instruction1+instruction2

if __name__ == "__main__":
    #map = readInput()
    map = utils.createMapTest() # map is a Map object
    instruction = getInstructions(map, (5,6))
    print(instruction)