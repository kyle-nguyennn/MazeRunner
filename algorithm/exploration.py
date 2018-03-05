from arena import Arena,CellType
from Robot import Robot
from random import randint
import time, socket
import race
from race import dijkstra
from tcp_client import TcpClient

class Explorer():
    def __init__(self, tcp_conn, robot_pos, buffer_size=1024,tBack=20,tThresh=260,pArea=0.9):
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
        cnt = 0
        self.tcp_conn.send_command("ES")
        self.update_status("Start exploration")
        while self.robot.robotMode != "done": 
            cnt += 1 
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
                    (instructions, endOrientation) = dijkstra(self.arena.get_2d_arr(), startnode, endnode, endOrientationImportant=False)
                    # give instruction
                    self.tcp_conn.send_command(instructions)
                    # update robot states (position and orientation)
                    (self.robot.robotCenterH, self.robot.robotCenterW,self.robot.robotHead) = endnode
                    continue
            else:
                if self.reachGoal:
                    if explorationTime > self.timeThreshold and \
                        not self.robot.isAlmostBack() and \
                        self.robot.robotMode != 'reExplore':
                        # find way back to start zone using fastest path algo (djikstra)
                        startnode = (self.robot.robotCenterH, self.robot.robotCenterW, int(self.robot.robotHead))
                        endnode = (1,1,0)
                        (instructions, endOrientation) = dijkstra(self.arena.get_2d_arr(), startnode, endnode, endOrientationImportant=False)
                        # give instruction
                        self.tcp_conn.send_command(instructions)
                        # update robot states (position and orientation)
                        (self.robot.robotCenterH, self.robot.robotCenterW,self.robot.robotHead) = endnode
                        self.robot.robotHead = endOrientation
                        continue
                    if self.robot.isAlmostBack() and self.exploredArea < 300:
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
                    if (realTimeMap.get(h+offsets[i][0], w+offsets[i][1]) != CellType.OBSTACLE):
                        realTimeMap.set(h+offsets[i][0], w+offsets[i][1], CellType.EMPTY)
                if value < self.MAX_SHORT_SENSOR:
                    if (19 >= h+offsets[value][0] >= 0 and 14 >= w+offsets[value][1] >= 0):
                        realTimeMap.set(h+offsets[value][0], w+offsets[value][1], CellType.OBSTACLE)
            elif sensorIndex == 5:
                offsets = self.leftCells[head]
                for i in range(value):
                    if (realTimeMap.get(h+offsets[i][0], w+offsets[i][1]) != CellType.OBSTACLE):
                        realTimeMap.set(h+offsets[i][0], w+offsets[i][1], CellType.EMPTY)
                if value < self.MAX_LONG_SENSOR:
                    if (19 >= h+offsets[value][0] >= 0 and 14 >= w+offsets[value][1] >= 0):
                        realTimeMap.set(h+offsets[value][0], w+offsets[value][1], CellType.OBSTACLE)
            else:
                print("sensor index out of bound")
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
        print("inside checkRight")
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
        print("Inside wall hugging")
        bodyCells = self.robot.returnBodyCells()
        print("robot center:",self.robot.robotCenterH,self.robot.robotCenterW)
        print("robot head:",self.robot.robotHead)
        for cell in bodyCells:
            self.arena.set(cell[0],cell[1],CellType.EMPTY)
        print("hello")
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

