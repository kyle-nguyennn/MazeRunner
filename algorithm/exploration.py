from arena import Arena,CellType
from Robot import Robot
from random import randint
import time, socket, logging, sys
import race
from race import dijkstra
from tcp_client import TcpClient
import json

class Explorer():
    def __init__(self, tcp_conn, robot_pos, buffer_size=1024,tBack=20,tThresh=260,pArea=0.9):
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
        self.tcp_conn = tcp_conn
        self.auto_update = False
        self.status = ""
        self.arena = Arena()
        #self.robot = [1, 1, 0] # 2d position plus orientation
        ### CONSTANT ####
        self.MAX_SHORT_SENSOR = 3
        self.MAX_LONG_SENSOR = 6
        ##### exploration logics related variables ####
        self.exploredArea = 0
        self.cnt = 0 # no. of instruction executed
        self.goBackTime = tBack # seconds for it to go back Start from any position
        self.timeThreshold = tThresh # user-input time to terminate exploration
        self.timeLimit = 360
        self.areaPercentage = pArea # percentage we want the robot to explore up to
        self.reachGoal = False
        self.startTime = time.time()
        self.robot = Robot(
            'exploring', robot_pos[2]/90, robot_pos[0], robot_pos[1])
        self.checkingRight = False

        self.frontCells = {0:[[[2,-1],[3,-1],[4,-1]],[[2,0],[3,0],[4,0]],[[2,1],[3,1],[4,1]]],
                    1:[[[1,2],[1,3],[1,4]],[[0,2],[0,3],[0,4]],[[-1,2],[-1,3],[-1,4]]],
                    2:[[[-2,1],[-3,1],[-4,1]],[[-2,0],[-3,0],[-4,0]],[[-2,-1],[-3,-1],[-4,-1]]],
                    3:[[[-1,-2],[-1,-3],[-1,-4]],[[0,-2],[0,-3],[0,-4]],[[1,-2],[1,-3],[1,-4]]]
            }
        # only keep top right and bottom right lines
        self.rightCells = {0:[[[1,2],[1,3],[1,4]],[[-1,2],[-1,3],[-1,4]]],
                    1:[[[-2,1],[-3,1],[-4,1]],[[-2,-1],[-3,-1],[-4,-1]]],
                    2:[[[-1,-2],[-1,-3],[-1,-4]],[[1,-2],[1,-3],[1,-4]]],
                    3:[[[2,-1],[3,-1],[4,-1]],[[2,1],[3,1],[4,1]]]
            }
        # only keep top left lines, detect up to the 6 cells in front
        self.leftCells = {0:[[1,-2],[1,-3],[1,-4],[1,-5],[1,-6],[1,-7]],
                    1:[[2,1],[3,1],[4,1],[5,1],[6,1],[7,1]],
                    2:[[-1,2],[-1,3],[-1,4],[-1,5],[-1,6],[-1,7]],
                    3:[[-2,-1],[-3,-1],[-4,-1],[-5,-1],[-6,-1],[-7,-1]]
                }
        

    def run(self):
        self.tcp_conn.send_command("ES")
        self.update_status("Start exploration")
        while self.robot.robotMode != "done": 
            sensors = self.tcp_conn.get_string()
            #update map with sensor values
            self.updateMap(sensors)
            explorationTime = time.time() - self.startTime
            # if hard deadline reached: just break
            if explorationTime > self.timeLimit:
                self.robot.robotMode = "break"
                break
            #check reachgoal
            if self.robot.robotCenterH == 18 and self.robot.robotCenterW == 13:
                self.reachGoal = True
            # if reach time limit
            if self.timeThreshold < explorationTime or self.exploredArea >= 300*self.areaPercentage:
                if self.robot.isInStartZone():
                    self.robot.robotMode = "done"
                    break
                else:
                    # find the way back to start zone using djikstra
                    startnode = (self.robot.robotCenterH, self.robot.robotCenterW, int(self.robot.robotHead))
                    endnode = (1,1,0)
                    (instructions, endOrientation,cost) = dijkstra(self.arena.get_2d_arr(), startnode, endnode, endOrientationImportant=False)
                    # give instruction
                    self.cnt += len(instructions)
                    self.tcp_conn.send_command(instructions)
                    # update robot states (position and orientation)
                    self.robot.jump(endnode)
                    continue
            else:
                if self.reachGoal:
                    if explorationTime > self.timeThreshold and \
                        not self.robot.isAlmostBack() and \
                        self.robot.robotMode != 'reExplore':
                        # find way back to start zone using fastest path algo (djikstra)
                        startnode = (self.robot.robotCenterH, self.robot.robotCenterW, int(self.robot.robotHead))
                        endnode = (1,1,0)
                        (instructions, endOrientation,cost) = dijkstra(self.arena.get_2d_arr(), startnode, endnode, endOrientationImportant=False)
                        # give instruction
                        self.cnt += len(instructions)
                        self.tcp_conn.send_command(instructions)
                        # update robot states (position and orientation)
                        self.robot.jump(endnode) # already update sensors inside
                        continue
                    if self.robot.isAlmostBack() and self.exploredArea < 300:
                        self.robot.robotMode = 'reExplore'
                    if self.robot.robotMode == 'reExplore':
                        # reexplore, find the fastest path to the nearest unexplored cell
                        (instruction, endnode) = self.reExplore()
                        # give instruction
                        self.cnt += len(instruction)
                        self.tcp_conn.send_command(instruction)
                        # update robot states
                        self.robot.jump(endnode) # already update sensors inside

                        print("comeplete a re-reploration")
                        continue

                #if havent reach any of above continue statements, just wall hugging
                instruction = self.wallHugging()
                # there's no need to update robot state because it is already done in wallHugging()
                # give instruction 
                self.cnt += len(instruction)
                self.tcp_conn.send_command(instruction)
                print("robot center:",self.robot.robotCenterH,self.robot.robotCenterW)
                print("robot head:",self.robot.robotHead)
                if self.reachGoal == False:
                    self.reachGoal = self.robot.isInGoal()           
        print("Exploration time:",explorationTime)
        print("Instruction count:", self.cnt)
        self.update_status("End exploration")
        self.tcp_conn.send_command(json.dumps({"event": "endExplore"}))
        self.tcp_conn.send_command("EE")

    def is_valid_point(self, point):
        x = point[0]
        y = point[1]
        return (x >= 0 and x <20 and y >= 0 and y < 15)

    def get_arena(self):
        return self.arena

    def get_robot(self):
        if self.robot.robotMode == "done":
            return None
        return self.robot.getPosition()            

    def update_status(self, status):
        self.status = status
        self.tcp_conn.send_status(status)
        if self.auto_update:
            self.tcp_conn.send_robot_pos(self.robot.getPosition())
            self.tcp_conn.send_arena(self.arena)

    def current_status(self):
        return self.status

    def set_update(self, auto):
        self.auto_update = auto

    ##### exploration logics #####

    def updateExploredArea(self):   
        count = 0
        for row in self.arena.get_2d_arr():
            for cell in row:
                if (cell != CellType.UNKNOWN):
                    count += 1
        self.exploredArea = count
    # given inputs, find corresponding cell coordinates needed to be marked as enum EMPTY or OBSTACLE
    def markCells(self, sensorIndex, value):
        w = self.robot.robotCenterW
        h = self.robot.robotCenterH
        head = self.robot.robotHead
        realTimeMap = self.arena
        # if withint the map range, then mark. Otherwise discard the reading
        if (0 <= w <= 13 and 0 <= h <= 18):
            # sensorIndex = 0..5 corresponding to F1,F2,F3,R1,R2,L1
            # only the 5th sensor (top left) is long range sensor
            sensor = self.robot.sensors[sensorIndex]
            offsets = self.robot.visible_offsets(sensor)
            if value > sensor.visible_range:
                value = sensor.visible_range
            if value <= sensor.visible_range:
                for i in range(value):
                    x = h + offsets[i][0]
                    y = w + offsets[i][1]
                    if self.is_valid_point((x,y)):
#                        logging.debug("Empty coordinate " + str(x) +" " + str(y))
                        realTimeMap.set(x, y, CellType.EMPTY)
                if value < sensor.visible_range:
                    x = h + offsets[value][0]
                    y = w + offsets[value][1]
                    if self.is_valid_point((x,y)):
#                        logging.debug("Obstacle coordinate " + str(x) + " " + str(y))
                        realTimeMap.set(x, y, CellType.OBSTACLE)
        self.updateExploredArea()
    def updateMap(self, sensorValues):
        # sensorValue = "AAAAAA"
        # F1,F2,F3,R1,R2,L1
        for i in range(len(sensorValues)):
            self.markCells(i, int(sensorValues[i]))
        self.updateExploredArea()
    # check whether the 3 consecutive cells in front are empty
    def checkFront(self):
        robot = self.robot
        frontCells = robot.frontCells
        for cell in frontCells[robot.robotHead]:
            if (robot.robotCenterW+cell[1] > 14 or robot.robotCenterH+cell[0] > 19 \
                or robot.robotCenterW+cell[1] < 0 or robot.robotCenterH+cell[0] < 0 \
                or self.arena.get(robot.robotCenterH+cell[0],robot.robotCenterW+cell[1]) != CellType.EMPTY): 
                return False
        print("check front true")
        return True                   
    # check whether the 3 consecutive cells on robot right are empty
    def checkRight(self):
        robot = self.robot
        rightCells = robot.rightCells
        for cell in rightCells[robot.robotHead]:
            if (robot.robotCenterW+cell[1] > 14 or robot.robotCenterH+cell[0] > 19 \
                or robot.robotCenterW+cell[1] < 0 or robot.robotCenterH+cell[0] < 0 \
                or self.arena.get(robot.robotCenterH+cell[0],robot.robotCenterW+cell[1]) == CellType.OBSTACLE):
                return "false"
            elif (self.arena.get(robot.robotCenterH+cell[0],robot.robotCenterW+cell[1]) == CellType.UNKNOWN):
                return "unknown"
        print("check right true")
        return "true"
    def wallHugging(self): # return instruction
        # mark current body cells as empty
        # actually might not need, just put here first
        bodyCells = self.robot.returnBodyCells()
        for cell in bodyCells:
            self.arena.set(cell[0],cell[1],CellType.EMPTY)
        if (self.checkingRight == False):
            # decide turn-right condition
            if (self.checkRight() == "true"):
                self.robot.rotateRight()
                self.robot.forward()
                self.update_status("Turning right")
                return ("RF")
            
            elif (self.checkRight() == "unknown"):
                self.robot.rotateRight()
                self.update_status("Checking right")  
                self.checkingRight = True
                return ("R")
            else:
                print("right has obstacle")
                                  
        # alr enter checkingRight now, so update status as False again
        self.checkingRight = False
        # decide front condition
        if (self.checkFront()):
            self.robot.forward()
            self.update_status("Moving forward")  
            return ("F")
        else:
            self.robot.rotateLeft()
            self.update_status("Turning left")  
            return ("L")
        
    def allEmpty(self,h,w):
        for i in range(h-1,h+2):
            for j in range(w-1,w+2):
                if self.is_valid_point((i,j))==False or self.arena.get(i,j) != CellType.EMPTY:
                    return False
        return True
    
    def searchObservableCells(self,cells,sensorRange):
        # search cell which: line withint sensor range all clear, and front row of robot at observing point have 3 empty cells
        observableCells = []
        for cell in cells:
            print("exam cells:",cell)
            appended = False
            h = cell[0]
            w = cell[1]
            for side in range(4):
                print("direction:",side)
                if appended == True:
                    break
                if side == 0 or side == 2:
                    #check intermediate cells
                    allClear = True                    
                    for i in range(1,sensorRange+1):
                        j = i
                        if side == 0:
                            j = j*(-1)
                        if self.is_valid_point((h+j,w)) == False or self.arena.get(h+j,w) != CellType.EMPTY:  # should UNKNWON be included
                            print("h,w:",str(h+j),w)
                            allClear = False
                            break
                    if allClear == False: # if allClear at this direction is False, continue loop with a new direction
                        continue
                    else: # test for body of observing point
                        j = sensorRange+2
                        if side == 0:
                            j = j*(-1)
                        if not self.allEmpty(h+j,w) and not self.allEmpty(h+j,w+1) and not self.allEmpty(h+j,w-1):
                            print("center of Ob:",str(h+j),w)
                            print("not allEmpty")
                            continue #continue another direction
                        else:
                            print("append observable cell:",cell)
                            observableCells.append(cell)
                            appended = True
                            break

                else: # side == 1 or 3
                    #check intermediate cells
                    for i in range(1,sensorRange+1):
                        allClear = True
                        j = i
                        if side == 1:
                            j = j*(-1)
                        if self.is_valid_point((h,w+j)) == False or self.arena.get(h,w+j) != CellType.EMPTY:  # should UNKNWON be included
                            print("h,w:",str(h+j),w)                            
                            allClear = False
                            break
                    if allClear == False: # if allClear at this direction is False, continue loop with a new direction
                        continue
                    else: # test for body of observing point
                        j = sensorRange+2
                        if side == 1:
                            j = j*(-1)
                        if not self.allEmpty(h,w+j) and not self.allEmpty(h-1,w+j) and not self.allEmpty(h+1,w+j):
                            print("center of Ob:",str(h+j),w)
                            print("not allEmpty")
                            continue #continue another direction
                        else:
                            print("append observable cell:",cell)
                            observableCells.append(cell)
                            appended = True
                            break
            logging.debug("observable cells inside:" + str(observableCells))                                
        return observableCells
            
            
        
    def reExplore(self):
            
        # detect all unexplored cells
        reExploreCells = []
        observableCellsDist = []
        cellEuclidean = []
        targetCells = []
        robot = self.robot
        noOfPicks = 3
        startnode = (robot.robotCenterH, robot.robotCenterW, int(robot.robotHead)) #change to int(robothead) because somehow the robotHead is a float
     
        for x in range(len(self.arena.arena_map)):
            for y in range(len(self.arena.arena_map[x])):
                if (self.arena.get(x,y) == CellType.UNKNOWN):
                    reExploreCells.append([x,y])
        
        layer = 0
        maxSensor = 2
        while (layer < maxSensor):         
            # only move to explore one of the boundary cells - cell that has at least one side has 3 consecutive empty blocks            
            observableCells = self.searchObservableCells(reExploreCells,layer) # can see up to 3 cells
            if len(observableCells) != 0: 
                break
            else:
                layer += 1

        if len(observableCells) == 0 and layer >= maxSensor: # no possible observation, go back
            (instr, endNode,cost) = dijkstra(self.arena.get_2d_arr(), startnode, (1,1,0), endOrientationImportant=True) 
            self.robot.robotMode = "done"
            return (instr, endNode)

        # calculate Euclidean distance for each
        for cell in observableCells:
            euclideanDist =euclidean([robot.robotCenterH,robot.robotCenterW],cell)
            cellEuclidean.append(euclideanDist)
            observableCellsDist.append((cell,euclideanDist))
        
        # sort cellEuclidean distance and remove all duplicates
        cellEuclidean.sort()
        cellEuclidean = list(set(cellEuclidean))
        
        potentialPos = []
       # while len(potentialPos) == 0:  
            # pick k number of eucliean nearest cell candidates
        itemNo = 0
        noMore = False
        targetCells = []
        cellList = []
        for dist in cellEuclidean:
            for cellTup in observableCellsDist:
                if cellTup[1] == dist:
                    if itemNo < noOfPicks:
                        targetCells.append(cellTup[0])
                        itemNo += 1
                        cellList.append(cellTup)
                if itemNo > noOfPicks:
                    noMore = True
                    break
            if noMore == True:
                break
# =============================================================================
#             for cell in cellList:
#                 observableCellsDist.remove(cell)
# =============================================================================
                        
        logging.debug("targetCells" + str(targetCells))
        for cell in targetCells:
            prevPosLength = len(potentialPos)
            layer = 0
            while (prevPosLength == len(potentialPos)):
                # find its nearest observing point
                offsets = [[-2,1],[-2,0],[-2,-1],[-1,-2],[0,-2],[1,-2],[2,-1],[2,0],[2,1],[1,2],[0,2],[-1,2], #layer 0
                           [-3,1],[-3,0],[-3,-1],[-1,-3],[0,-3],[1,-3],[3,-1],[3,0],[3,1],[1,3],[0,3],[-1,3], #layer 1
                           [-4,1],[-4,0],[-4,-1],[-1,-4],[0,-4],[1,-4],[4,-1],[4,0],[4,1],[1,4],[0,4],[-1,4], #layer 2
                           [-5,1],[-5,0],[-5,-1],[-1,-5],[0,-5],[1,-5],[5,-1],[5,0],[5,1],[1,5],[0,5],[-1,5]] #layer 3
                for offset in offsets[:(layer+1)*12]:
                    print("layer:",layer)
                    allClear = True
                    if self.allEmpty(cell[0]+offset[0],cell[1]+offset[1]):
                        # check for intermediate cells condition
                        if offset[0] in [-1,0,1]: #check horizontal
                            if offset[1] < 0: # left
                                for i in range(offset[1]+2,0):
                                    if self.is_valid_point((cell[0],cell[1]+i)) == False or self.arena.get(cell[0],cell[1]+i) != CellType.EMPTY:
                                        allClear = False
                                        break
                            else: #right
                                for i in range(1,offset[1]-1):
                                    if self.is_valid_point((cell[0],cell[1]+i)) == False or self.arena.get(cell[0],cell[1]+i) != CellType.EMPTY:
                                        allClear = False
                                        break                                                                 
                        elif offset[1] in [-1,0,1]: #check vertical
                            if offset[0] < 0: # down
                                for i in range(offset[0]+2,0):
                                    if self.is_valid_point((cell[0]+i,cell[1])) == False or self.arena.get(cell[0]+i,cell[1]) != CellType.EMPTY:
                                        allClear = False
                                        break
                            else: #up
                                for i in range(1,offset[0]-1):
                                    if self.is_valid_point((cell[0]+i,cell[1])) == False or self.arena.get(cell[0]+i,cell[1]) != CellType.EMPTY:
                                        allClear = False
                                        break                    
                    else:
                        allClear = False
                    if allClear == True:
                        # potentialPos: [observingCoords,cellToObserveCoords]
                        print("cell:",cell)
                        print("obPoint:",[[cell[0]+offset[0],cell[1]+offset[1]]])
                        potentialPos.append([[cell[0]+offset[0],cell[1]+offset[1]],cell,0,0]) #default head is 0, cost = 0            
                if layer < 2:
                    layer += 1
                else:
                    break
        # sensor range here for reference
# =============================================================================
#         rightRange = 2
#         frontRange = 3
#         leftRange = 3
# =============================================================================
        
        # update all potentialPos values with dijkstra cost
        updatedNodes = [] 

        for node in potentialPos:
#        for [cellToGo,cellToOb,head,cost] in potentialPos:
            indexOff = 0
            for offset in offsets:
                if [node[0][0]-node[1][0],node[0][1]-node[1][1]] == offset:
                    if 0 <= indexOff < 3 or 12 <= indexOff < 15 or 24 <= indexOff < 27 or 36 <= indexOff < 39 :
                        if indexOff in [1,13,25,37]: # front only
                            node[2] = [0]
                            break
                        elif indexOff in [2,14,26,38]: # front and left and right
                            if indexOff != 38:
                                node[2] = [0,1,3]
                            else:
                                node[2] = [0,1]
                            break
                        else:
                            if indexOff != 36:
                                node[2] = [0,3] # front and right
                            else:
                                node[2] = [0]
                            break
                    elif 3 <= indexOff < 6 or 15 <= indexOff < 18 or 27 <= indexOff < 30 or 39 <= indexOff < 42:
                        if indexOff in [4,16,28,40]:
                            node[2] = [1]
                            break
                        elif indexOff in [5,17,29,41]:
                            if indexOff != 41:
                                node[2] = [1,2,0]
                            else:
                                node[2] = [1,2]
                            break
                        else:
                            if indexOff != 39:
                                node[2] = [1,0]
                            else:
                                node[2] = [1]
                            break
                    elif 6 <= indexOff < 9 or 18 <= indexOff < 21 or 30 <= indexOff < 33 or 42 <= indexOff < 45:
                        if indexOff in [7,19,31,43]:
                            node[2] = [2]
                            break
                        elif indexOff in [8,20,32,44]:
                            if indexOff != 44:
                                node[2] = [2,3,1]
                            else:
                                node[2] = [2,3]
                            break
                        else:
                            if indexOff != 42:
                                node[2] = [2,1]
                            else:
                                node[2] = [2]
                            break
                    else:
                        if indexOff in [10,22,34,46]:
                            node[2] = [3]
                            break
                        elif indexOff in [11,23,35,47]:
                            if indexOff != 46:
                                node[2] = [3,0,2]
                            else:
                                node[2] = [3,0]
                            break
                        else:
                            if indexOff != 45:
                                node[2] = [3,2]
                            else:
                                node[2] = [3]
                            break
                else:
                    indexOff += 1
            cellsToMove = []
            costs = []
            # find the path of less cost considring both front ahd right direction for same point
            for direction in node[2]:
                cellsToMove.append((node[0][0],node[0][1],direction))
            for cellToMove in cellsToMove:
                (instr, endNode,cost) = dijkstra(self.arena.get_2d_arr(), startnode, cellToMove, endOrientationImportant=True) 
                print("dijkstra startnode:",startnode)
                print("dijkstra cellToMove:",cellToMove)
                print("dijkstra instr:",instr)
                costs.append(cost)
                minCost = costs[0]
                index = 0
                for cost in costs:
                    if cost < minCost:
                        minCost = cost
                        index += 1
            node[1] = cellsToMove[index] 
            node[2] = node[2][index]                  
            node[3] = minCost
            updatedNodes.append(node)
        logging.debug("potentialPos: " + str(updatedNodes))
        
        # find the minimum cost in potentialPos 
        # this algo can be optimized later
        minCost = 1000
        index = 0
        for choice in updatedNodes:
            if choice[3] < minCost and choice[3] != 0:
                minCost = choice[3]       
        for choice in updatedNodes:
            if choice[3] != minCost:
                index += 1
            else:
                break
        cellToMove = (updatedNodes[index][0][0], updatedNodes[index][0][1], updatedNodes[index][2])
# =============================================================================
#         print("cell to move:",cellToMove)
#         print("start cell:",startnode)
# =============================================================================
        (instr, endNode,cost) = dijkstra(self.arena.get_2d_arr(), startnode, cellToMove, endOrientationImportant=True) 
        logging.debug("Instruction for going to observing cell" + instr)
        logging.debug("Observing point " + str(endNode))       
        return (instr, endNode)

###### helper functions #####    
def findArrayIndexMin(arr):
    return arr.index(min(arr))
            
def euclidean(pos1,pos2):
    return abs(pos1[1]-pos2[1])+abs(pos1[0]-pos2[0])

