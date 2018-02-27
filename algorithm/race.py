from arena import Arena, CellType
import utils
import heapq

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

def neighbors(mymap, cur, dir):
    # cur is the representative point of the robot
    offsets_n = [(1,0), (0,1), (-1,0), (0,-1)]
    offsets_e = [(0,1), (-1,0), (0,-1), (1,0)]
    offsets_s = [(-1,0), (0,-1), (1,0), (0,1)]
    offsets_w = [(0,-1), (1,0), (0,1), (-1,0)]
    offsets = []
    if dir == 0:
        offsets = offsets_n
    if dir == 1:
        offsets = offsets_e
    if dir == 2:
        offsets = offsets_s
    if dir == 3:
        offsets = offsets_w

    neighbors = []
    for i in range(len(offsets)):
        offset = offsets[i]
        neighbors.append((cur[0] + offset[0], cur[1] + offset[1], (dir+i)%4))
    return neighbors

def dijkstra(mymap, start, end, direction): # return tuple of instruction string with the final orientation of the robot after executing these instructions
    q = []
    cost = []
    prev = [[[((0,0), "", 0) for i in range(4)] for i in range(len(mymap[0]))] for i in range(len(mymap))]
    dir = direction
    cur = start
    
    for i in range(len(mymap)):
        r = mymap[i]
        z = []
        p = []
        for j in range(len(r)):
            #p.append(((i,j), "", 0))
            z.append(1000)
        cost.append(z)
        #prev.append(p)
    cost[start[0]][start[1]] = 0
    prev[start[0]][start[1]][0] = ((-1,-1), "", 0)
    heapq.heappush(q, (cost[start[0]][start[1]], start, dir, ""))
    print("break1")
    while len(q) > 0:
        (c, cur, dir, m) = heapq.heappop(q)
        if cur == end:
            break
        my_neighbors = neighbors(mymap, cur, dir)
        for i in range(len(my_neighbors)):
            neighbor = (my_neighbors[i][0], my_neighbors[i][1])
            neighbor_dir = my_neighbors[i][2]
            if not detectCollision(mymap, neighbor):
                dir_cost = 0
                move = ""
                if i == 0:
                    dir_cost = 1
                    move = "F"
                if i == 1:
                    dir_cost = 2
                    move = "RF"
                if i == 2:
                    dir_cost = 1
                    move = "B"
                if i == 3:
                    dir_cost = 2
                    move = "LF"
                if cost[neighbor[0]][neighbor[1]] > c+dir_cost:
                    # TODO: costs for same cell but different directions are different
                    cost[neighbor[0]][neighbor[1]] = c+dir_cost
                    prev[neighbor[0]][neighbor[1]][neighbor_dir] = (cur, move, dir)
                    # TODO: change to c+dir_cost after fixing cost for different directions bug
                    heapq.heappush(q, (c+1, (neighbor[0], neighbor[1]), neighbor_dir, move))
    print("break2")
    #(cur, m) = prev[end[0]][end[1]]
    final_dir = dir
    path = [(cur, "", final_dir)]
    instruction = ""
    while cur != (-1,-1):
        (p, move, prev_direction) = prev[cur[0]][cur[1]][dir]
        if p != (-1,-1): # check curent position
            path.insert(0, prev[cur[0]][cur[1]][dir])
        cur = p
        dir = prev_direction
    print("break3")
    for node in path:
        instruction += node[1]
        print(str(node) + " -> ")
    print('END')
    return (instruction, final_dir)


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
    (instruction1, dir1) = dijkstra(mymap, (1,1), waypoint, dir)
    (instruction2, dir2) = dijkstra(mymap, (waypoint), (18,13), dir1)
    return instruction1+instruction2

if __name__ == "__main__":
    #map = readInput()
    map = utils.createMapTest() # map is a Map object
    instruction = getInstructions(map, (5,6))
    print(instruction)