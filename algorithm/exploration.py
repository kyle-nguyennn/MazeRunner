from arena import Arena,CellType
from Robot import Robot
from random import randint
import time, socket
import race
from race import dijkstra
from tcp_client import TcpClient

class Explorer():
    def __init__(self, tcp_conn, robot_pos, buffer_size=1024,tBack=20,pArea=0.9,alignLimit = 3):
        self.tcp_conn = tcp_conn
        self.auto_update = False
        self.arena = Arena()
        #self.robot = [1, 1, 0] # 2d position plus orientation
        ### CONSTANT ####
        self.MAX_SHORT_SENSOR = 3
        self.MAX_LONG_SENSOR = 6
        ##### exploration logics related variables ####
        self.exploredArea = 0
        self.cnt = 0 # no. of instruction executed
        self.goBackTime = tBack # seconds for it to go back Start from any position
        self.timeLimit = 360
        self.areaPercentage = pArea # percentage we want the robot to explore up to
        self.reachGoal = False
        self.startTime = time.time()
        self.alignCnt = 0 # counter for robot alignment
        self.alignLimit = alignLimit
        self.alignNow = False
        self.readingConflict = False
        self.conflictCells = []
        self.alignSensor = "" # C1(front), C2(right)
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
        # positions in wallCells are for calibration
        self.wallCells = {0:[[],[]],
                    1:[[],[]],
                    2:[[],[]],
                    3:[[],[]]
                }
        for i in range(1,19):
            self.wallCells[0][0].append([i,13])
            self.wallCells[2][0].append([i,1])
            if 2 <= i <= 17:
                self.wallCells[0][1].append([i,12])
                self.wallCells[2][1].append([i,2]) 
                if 2 <= i <= 12:
                    self.wallCells[1][1].append([2,i])
                    self.wallCells[3][1].append([17,i])
            if 1 <= i <= 13:
                self.wallCells[1][0].append([1,i])
                self.wallCells[3][0].append([18,i])
        

    def run(self):
        cnt = 0
        self.tcp_conn.send_command("ES")
        self.update_status("Start exploration")
        while self.robot.robotMode != "done": 
            confirmReading = False # means sensor readings in this loop is for confirmation not detection
            cnt += 1 
            sensors = self.tcp_conn.get_string()
            if self.readingConflict == True:
                
            else:    
                #update map with sensor values
                self.updateMap(sensors)
                # sensor conflict solving if conflictCells contains cells
                if len(conflictCells) != 0:
                    self.readingConflict = True
                    self.tcp_conn.send_command("N")
                else:
                    self.readingConflict = False
                
            explorationTime = time.time() - self.startTime
            #check reachgoal
            if self.robot.robotCenterH == 18 and self.robot.robotCenterW == 13:
                self.reachGoal = True
            # if reach time limit
            if self.timeLimit < explorationTime or self.exploredArea >= 300*self.areaPercentage:
                if self.robot.isInStartZone():
                    self.robot.robotMode = "done"
                    break
                else:
                    self.update_status("Robot rushing back")
                    # find the way back to start zone using djikstra
                    startnode = (self.robot.robotCenterH, self.robot.robotCenterW, int(self.robot.robotHead))
                    endnode = (1,1,0)
                    (instructions, endOrientation) = dijkstra(self.arena.get_2d_arr(), startnode, endnode, endOrientationImportant=False)
                    # give instruction
                    self.tcp_conn.send_command(instructions)
                    # update robot states (position and orientation)
                    (self.robot.robotCenterH, self.robot.robotCenterW,self.robot.robotHead) = endnode
                    self.robot.robotHead = endOrientation
                    continue
            else:
                if self.reachGoal:
# =============================================================================
#                     if not self.robot.isAlmostBack() and \
#                         self.robot.robotMode != 'reExplore':
#                         # find way back to start zone using fastest path algo (djikstra)
#                         startnode = (self.robot.robotCenterH, self.robot.robotCenterW, int(self.robot.robotHead))
#                         endnode = (1,1,0)
#                         (instructions, endOrientation) = dijkstra(self.arena.get_2d_arr(), startnode, endnode, endOrientationImportant=False)
#                         # give instruction
#                         self.tcp_conn.send_command(instructions)
#                         # update robot states (position and orientation)
#                         (self.robot.robotCenterH, self.robot.robotCenterW,self.robot.robotHead) = endnode
#                         self.robot.robotHead = endOrientation
#                         continue
# =============================================================================
                    if self.robot.isAlmostBack() and self.exploredArea < 300*self.areaPercentage:
                        self.robot.robotMode = 'reExplore'
                    if self.robot.robotMode == 'reExplore':
                        # reexplore, find the fastest path to the nearest unexplored cell
                        (instruction, endnode) = self.reExplore()
                        # give instruction
                        self.tcp_conn.send_command(instruction)
                        # update robot states
                        (self.robot.robotCenterH, self.robot.robotCenterW,self.robot.robotHead) = endnode
                        print("comeplete a re-reploration")
                        continue

                #if havent reach any of above continue statements, just wall hugging
                instruction = self.wallHugging()
                # there's no need to update robot state because it is already done in wallHugging()
                # give instruction 
                self.tcp_conn.send_command(instruction)

                if self.reachGoal == False:
                    self.reachGoal = self.robot.isInGoal()           
        print("Exploration time:",explorationTime)
        self.update_status("End exploration")
        self.tcp_conn.send_command("EE")

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
            if 0 <= sensorIndex <= 4:
                #front sensors
                if sensorIndex < 3:
                    offsets = self.frontCells[head][sensorIndex]
                else:
                    # minus 3 as 3,4 correspond to 0 and 1 in rightCells arrays
                    offsets = self.rightCells[head][sensorIndex-3]
                for i in range(value):
                    # if got obstacle, dun update ???
                    if realTimeMap.get(h+offsets[i][0], w+offsets[i][1]) == CellType.OBSTACLE \
                        and [h+offsets[i][0], w+offsets[i][1]] not in self.conflictCells:
                        self.conflictCells.append([h+offsets[i][0], w+offsets[i][1]])
                    else:
                        realTimeMap.set(h+offsets[i][0], w+offsets[i][1], CellType.EMPTY)
                        if [h+offsets[i][0], w+offsets[i][1]] in self.conflictCells:
                            self.conflictCells.remove([h+offsets[i][0], w+offsets[i][1]])
                if value < self.MAX_SHORT_SENSOR:
                    if (19 >= h+offsets[value][0] >= 0 and 14 >= w+offsets[value][1] >= 0):
                        if realTimeMap.get(h+offsets[value][0], w+offsets[value][1]) == CellType.EMPTY\
                        and [h+offsets[value][0], w+offsets[value][1]] not in self.conflictCells:
                            self.conflictCells.append([h+offsets[value][0], w+offsets[value][1]])
                        else:
                            realTimeMap.set(h+offsets[value][0], w+offsets[value][1], CellType.OBSTACLE)
                            if [h+offsets[value][0], w+offsets[value][1]] in self.conflictCells:
                                self.conflictCells.remove([h+offsets[value][0], w+offsets[value][1]])

            elif sensorIndex == 5:
                offsets = self.leftCells[head]
                for i in range(value):
                    if (realTimeMap.get(h+offsets[i][0], w+offsets[i][1]) == CellType.OBSTACLE \
                        and [h+offsets[i][0], w+offsets[i][1]] not in self.conflictCells):
                        self.conflictCells.append([h+offsets[i][0], w+offsets[i][1]])
                    else:
                        realTimeMap.set(h+offsets[i][0], w+offsets[i][1], CellType.EMPTY)
                        if [h+offsets[i][0], w+offsets[i][1]] in self.conflictCells:
                            self.conflictCells.remove([h+offsets[i][0], w+offsets[i][1]])
                if value < self.MAX_LONG_SENSOR:
                    if (19 >= h+offsets[value][0] >= 0 and 14 >= w+offsets[value][1] >= 0):
                        if realTimeMap.get(h+offsets[value][0], w+offsets[value][1]) == CellType.EMPTY\
                        and [h+offsets[value][0], w+offsets[value][1]] not in self.conflictCells:
                            self.conflictCells.append([h+offsets[value][0], w+offsets[value][1]])
                        else:
                            realTimeMap.set(h+offsets[value][0], w+offsets[value][1], CellType.OBSTACLE)
                            if [h+offsets[value][0], w+offsets[value][1]] in self.conflictCells:
                                self.conflictCells.remove([h+offsets[value][0], w+offsets[value][1]])
            else:
                print("sensor index out of bound")
        self.updateExploredArea()
        return wrongCells
    def updateMap(self, sensorValues):
        for i in range(len(sensorValues)):
            self.markCells(i, int(sensorValues[i]))
    # check whether the 3 consecutive cells in front are empty
    def checkAlign(self,r):
        head = int(self.robot.robotHead)
        if head > 0:
            head1 = head - 1
        else:
            head1 = 3
        for i in range(r):
            if [self.robot.robotCenterH,self.robot.robotCenterW] in self.wallCells[head][i]:
                self.alignSensor = ''.join(["CS",str(i)])
                self.alignNow = True
            elif [self.robot.robotCenterH,self.robot.robotCenterW] in self.wallCells[head1][i]:
                self.alignSensor = ''.join(["CF",str(i)])
                self.alignNow = True
            else:
                frontCells = self.frontCells[self.robot.robotHead]
                rightCells = self.rightCells[self.robot.robotHead]
                h = self.robot.robotCenterH
                w = self.robot.robotCenterW
                if self.arena.get(h+frontCells[0][i][0],w+frontCells[0][i][1]) == self.arena.get(h+frontCells[2][i][0],w+frontCells[2][i][1]) == CellType.OBSTACLE :
                    self.alignSensor = ''.join(["CF",str(i)])
                    self.alignNow = True
                elif self.arena.get(h+rightCells[0][i][0],w+rightCells[0][i][1]) == self.arena.get(h+rightCells[1][i][0],w+rightCells[1][i][1]) == CellType.OBSTACLE :
                    self.alignSensor = ''.join(["CS",str(i)])
                    self.alignNow = True
                elif self.arena.get(h+frontCells[0][i][0],w+frontCells[0][i][1]) == self.arena.get(h+frontCells[1][i][0],w+frontCells[1][i][0]) == CellType.OBSTACLE\
                    or self.arena.get(h+frontCells[1][i][0],w+frontCells[1][i][1]) == self.arena.get(h+frontCells[2][i][0],w+frontCells[2][i][1]) == CellType.OBSTACLE:                
                    self.alignSensor = ''.join(["CF",str(i)])
                    self.alignNow = True  
        
    def align(self):
        self.alignCnt = 0 # after each align, reset
        self.alignNow = False
        self.alignSensor = ""
            
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
        return "true"
    def wallHugging(self): # return instruction
        # mark current body cells as empty
        # actually might not need, just put here first
        print("Inside wall hugging")
        sensor = "" 
        bodyCells = self.robot.returnBodyCells()
# =============================================================================
#         print("robot center:",self.robot.robotCenterH,self.robot.robotCenterW)
#         print("robot head:",self.robot.robotHead)
# =============================================================================
        for cell in bodyCells:
            self.arena.set(cell[0],cell[1],CellType.EMPTY)
        self.alignCnt += 1 # increment alignment counter
        if self.alignCnt == self.alignLimit:
            # if just reach alignLimit, then use block0 to calibrate on only (more accurate)
            self.checkAlign(1)  
        elif self.alignCnt > self.alignLimit:
            # if alr exceed alignLimit and haven't found blocks to calibrate, use block1 to calibrate
            self.checkAlign(2)
        else:
            self.alignNow = False
            
        if (self.checkingRight == False):
            # decide turn-right condition
            if (self.checkRight() == "true"):                    
                self.robot.rotateRight()
                self.robot.forward()
                self.update_status("Turning right")
                if self.alignNow == True:
                    sensor = self.alignSensor
                    self.align()
                return (''.join([sensor,"RF"]))
            
            elif (self.checkRight() == "unknown"):
                self.robot.rotateRight()
                self.update_status("Checking right")  
                self.checkingRight = True
                if self.alignNow == True:
                    sensor = self.alignSensor
                    self.align()
                return (''.join([sensor,"R"]))

# =============================================================================
#             else:
#                 print("right has obstacle")
# =============================================================================
                                  
        # alr enter checkingRight now, so update status as False again
        self.checkingRight = False
        # decide front condition
        if (self.checkFront()):
            self.robot.forward()
            self.update_status("Moving forward")
            if self.alignNow == True:
                sensor = self.alignSensor
                self.align()
            return (''.join([sensor,"F"]))
        else:
            self.robot.rotateLeft()
            self.update_status("Turning left") 
            if self.alignNow == True:
                sensor = self.alignSensor
                self.align()
            return (''.join([sensor,"L"]))
        
    def allEmpty(self,h,w):
        for i in range(h-1,h+2):
            for j in range(w-1,w+2):
                if self.arena.get(i,j) != CellType.EMPTY:
                    return False
        return True
    
    def searchBoundaryCells(self,cells):
        boundaryCells = []
        for cell in cells:
            h = cell[0]
            w = cell[1]
            if (self.arena.get(h+1,w-1) == CellType.EMPTY \
                and self.arena.get(h+1,w) == CellType.EMPTY \
                and self.arena.get(h+1,w+1) == CellType.EMPTY \
                or self.arena.get(h+1,w+1) == CellType.EMPTY \
                and self.arena.get(h,w+1) == CellType.EMPTY \
                and self.arena.get(h-1,w+1) == CellType.EMPTY \
                or self.arena.get(h-1,w-1) == CellType.EMPTY \
                and self.arena.get(h-1,w) == CellType.EMPTY \
                and self.arena.get(h-1,w+1) == CellType.EMPTY \
                or self.arena.get(h+1,w-1) == CellType.EMPTY \
                and self.arena.get(h,w-1) == CellType.EMPTY \
                and self.arena.get(h-1,w-1) == CellType.EMPTY ):
                boundaryCells.append(cell)
        return boundaryCells
            
            
        
    def reExplore(self):
            
        # detect all unexplored cells
        reExploreCells = []
        cellEuclidean = []
        robot = self.robot
        
        for x in range(len(self.arena.arena_map)):
            for y in range(len(self.arena.arena_map[x])):
                if (self.arena.get(x,y) == CellType.UNKNOWN):
                    reExploreCells.append([x,y])
        
        # only move to explore one of the boundary cells - cell that has at least one side has 3 consecutive empty blocks            
        boundaryCells = self.searchBoundaryCells(reExploreCells)
        print("boundary:",boundaryCells)
                    
        # calculate Euclidean distance for each
        for cell in boundaryCells:
            euclideanDist =euclidean([robot.robotCenterH,robot.robotCenterW],cell)
            cellEuclidean.append(euclideanDist)
            
        # find the nearest one
        targetCell = boundaryCells[findArrayIndexMin(cellEuclidean)]
        print("target cell:",targetCell)
        
        # find its nearest observing point
        offsets = [[-2,1],[-2,0],[-2,-1],[-1,-2],[0,-2],[1,-2],[2,-1],[2,0],[2,1],[1,2],[0,2],[-1,2]]
        potentialPos = []
        for offset in offsets:
            if self.allEmpty(targetCell[0]+offset[0],targetCell[1]+offset[1]):
                potentialPos.append([targetCell[0]+offset[0],targetCell[1]+offset[1]])
        # calculate Euclidean distance for each
        posDistance = []
        for cell in potentialPos:
            dist = euclidean([robot.robotCenterH,robot.robotCenterW],cell)
            posDistance.append(dist)
        xToMove, yToMove = potentialPos[findArrayIndexMin(posDistance)]
        endingCell = [xToMove,yToMove]

        indexOff = 0
        for offset in offsets:
            if [endingCell[0]-targetCell[0],endingCell[1]-targetCell[1]] == offset:
                if 0 <= indexOff < 3:
                    observeDirection = 0
                    break
                elif 3 <= indexOff < 6:
                    observeDirection = 1
                    break
                elif 6 <= indexOff < 9:
                    observeDirection = 2
                    break
                else:
                    observeDirection = 3
                    break
            else:
                indexOff += 1
                
        print("offset:",offset)
        print("observeDirection:",observeDirection)
            
        cellToMove = (xToMove, yToMove, observeDirection)
        # use djikstra
        startnode = (robot.robotCenterH, robot.robotCenterW, int(robot.robotHead)) #change to int(robothead) because somehow the robotHead is a float
        (instr, endNode) = dijkstra(self.arena.get_2d_arr(), startnode, cellToMove, endOrientationImportant=True) 
        return (instr, endNode)
        
        # need to check robot final head direction
###### helper functions #####    
def findArrayIndexMin(arr):
    return arr.index(min(arr))
            
def euclidean(pos1,pos2):
    return abs(pos1[1]-pos2[1])+abs(pos1[0]-pos2[0])

