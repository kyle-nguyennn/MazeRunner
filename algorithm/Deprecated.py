@Deprecated
def explore(self,sensorValue,center,head):
    global robot,exploredArea,cnt,reachGoal,realTimeMap
    
    #update map with sensor values
    updateMap(sensorValue)

    # update robot status
    # BUT seems to be redudant because the robot will update itself when it moves
    robot.robotHead = head
    robot.robotCenterW = center[1]
    robot.robotCenterH = center[0]

    # if reach goal, mark
    if (robot.robotCenterH == 18 and robot.robotCenterW == 13):
        reachGoal = 1
        
    if (cnt == 0): # first instruction ,sense only, dun move
        return ("N",center,head,realTimeMap)   
    cnt += 1
    
    explorationTime = time.time() - startTime           
    
    if (explorationTime > timeLimit): # if reach time limit
        robot.robotMode = "break"
        return ("N",(robot.robotCenterH,robot.robotCenterW),robot.robotHead,realTimeMap)
    
    else: # continue exploration           
        if (explorationTime > timeThreshold and reachGoal == 1):
            robot.robotMode = "rush"
            return rush()
        else:  
            if (cnt > 30 and robot.robotCenterW == 1 and robot.robotCenterH == 1 and exploredArea > 280): # set as 30 first, any reasonable number just to make sure that the robot is not just started 
                # reach back to Start; exploration done
                robot.robotMode = "done"
                return ("N",(1,1),robot.robotHead,realTimeMap)
            
            elif (robot.robotMode == "reExplore"):
                return reExplore()
            
            elif (reachGoal == 1 and cnt > 30 and almostBack(robot.robotCenterH,robot.robotCenterW) and exploredArea < 280 ):
                # first time enter reExplore mode
                robot.robotMode = "reExplore"
                return reExplore()
                        
            else: # normal exploration procedure
                wallHugging()      


@Deprecated
def dijkstra(mymap, start, end, direction): # return tuple of instruction string with the final (x,y,d) of the robot after executing these instructions
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