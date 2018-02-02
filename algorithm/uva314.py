'''
sample input
9 10
0 0 0 0 0 0 1 0 0 0
0 0 0 0 0 0 0 0 1 0
0 0 0 1 0 0 0 0 0 0
0 0 1 0 0 0 0 0 0 0
0 0 0 0 0 0 1 0 0 0
0 0 0 0 0 1 0 0 0 0
0 0 0 1 1 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0
1 0 0 0 0 0 0 0 1 0
7 2 2 7 south
0 0
#sample output
12
'''

''' convention
North : 0
East: 1
South: 2
West: 3

'''

import heapq
def inp():
    mymap = []
    [n, m] = list(map(int, input().split()))
    for i in range (n):
        mymap.append(list(map(int, input().split())))
    points = input().split()
    start = (int(points[0])-1, int(points[1])-1)
    end = (int(points[2])-1, int(points[3])-1)
    direction = points[4]
    padded_map = []
    for i in range (n-1):
        padded_map.append(mymap[i][0:-1])
    return (padded_map, start, end, direction)

def detectCollision(mymap, pos): #take care of robot size in here, outside of this function the robot is treated as a 1x1 object
    # pos is the north-west corner cell that the robot takes
    # treat the system as the collecitons of all the point that the robot covers
    system = [pos, (pos[0], pos[1]+1), (pos[0]+1, pos[1]), (pos[0]+1, pos[1]+1)]
    for p in system:
        if p[0] < 0 or p[0] >= len(mymap) or p[1] < 0 or p[1] >= len(mymap[0]):
            return True
        if mymap[p[0]][p[1]] == 1: # there is obstacle at p
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
        off_sets = offsets_n
    if dir == 1:
        off_sets = offsets_e
    if dir == 2:
        off_sets = offsets_s
    if dir == 3:
        off_sets = offsets_w

    neighbors = []
    for offset in offsets:
        neighbors.append((cur[0] + offset[0], cur[1] + offset[1]))
    return neighbors

def dijkstra(mymap, start, end, direction):
    print(mymap)
    q = []
    cost = []
    prev = []
    dir = 0
    if direction[0] == "n":
        dir = 0
    if direction[0] == "e":
        dir = 1
    if direction[0] == "s":
        dir = 2
    if direction[0] == "w":
        dir = 3
    print(neighbors(mymap, start, dir))
    for i in len(mymap):
        r = mymap[i]
        z = []
        p = []
        for j in len(r):
            c = r[j]
            p.append(((i,j), ""))
            z.append(1000)
        cost.append(z)
        prev.append(p)
    cost[start[0]][start[1]] = 0
    prev[start[0]][start[1]] = ((-1,-1), "")
    heapq.heappush(q, (cost[start[0]][start[1]], start, dir, ""))
    while len(q) > 0:
        (c, cur, dir, m) = heapq.heappop(q)
        if cur == end:
            break
        my_neighbors = neighbors(mymap, cur, dir)
        for i in range(len(my_neighbors)):
            neighbor = my_neighbors[i]
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
            if not detectCollision(mymap, neighbor):
                if cost[neighbor[0]][neighbor[1]] > c+dir_cost:
                    cost[neighbor[0]][neighbor[1]] = c+dir_cost
                    prev[neighbor[0]][neighbor[1]] = (cur, move)
                    heapq.heappush(q, (c+1, (neighbor[0], neighbor[1]), dir, move))
    (cur, m) = prev[end[0]][end[1]]
    path = [(cur, m)]
    while cur != (-1,-1):
        if prev[cur[0]][cur[1]][0] != (-1,-1): # check curent position
            path.insert(0, prev[cur[0]][cur[1]])
        cur = prev[cur[0]][cur[1]][0]
    for node in path:
        print(str(node) + " -> ")
    print('END')


if __name__ == "__main__":
    (mymap, start, end, direction) = inp()
    dijkstra(mymap, start, end, direction)

    