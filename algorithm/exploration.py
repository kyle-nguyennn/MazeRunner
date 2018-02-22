from arena import Arena,CellType
from Robot import Robot
from random import randint
import time, socket
import race
from race import dijkstra


######################## integrate with Calvin code #############################

class Explorer():
    def __init__(self, tcp_ip, tcp_port, buffer_size=1024):
        self.running = False
        self.arena = Arena()
        #self.robot = [1, 1, 0] # 2d position plus orientation
        self.tcp_ip = tcp_ip
        self.tcp_port = tcp_port
        self.buffer_size = buffer_size
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ### CONSTANT ####
        self.MAX_SHORT_SENSOR = 3
        self.MAX_LONG_SENSOR = 6
        ##### exploration logics related variables ####
        self.exploredArea = 0
        self.cnt = 0 # no. of instruction executed
        self.timeThreshold = 260
        self.timeLimit = 360
        self.reachGoal = False
        self.startTime = time.time()
        self.robot = Robot(mode='exploring')

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
        self.running = True
        self.client_socket.connect((self.tcp_ip, self.tcp_port))
        print(
            "ExplorationExample - Connected to {}:{}".format(self.tcp_ip, self.tcp_port))
        self.send_data("startExplore")
        while self.robot.robotMode != "done":
            sensors = self.recv_data()
            #update map with sensor values
            self.updateMap(sensors)
            explorationTime = time.time() - self.startTime
            # if reach time limit
            if self.timeLimit - explorationTime <= 20:
                if self.robot.isInStartZone():
                    self.send_data("S")
                    self.robot.robotMode = "done"
                    break
                else:
                    # find the way back to start zone using djikstra
                    startnode = (self.robot.robotCenterH, self.robot.robotCenterW)
                    endnode = (1,1)
                    (instructions, endOrientation) = dijkstra(self.arena.get_2d_arr(), startnode, endnode, self.robot.robotHead)
                    # give instruction
                    self.send_data(instructions)
                    # update robot states (position and orientation)
                    (self.robot.robotCenterH, self.robot.robotCenterW) = endnode
                    self.robot.robotHead = endOrientation
            else:
                if self.reachGoal:
                    if explorationTime > self.timeThreshold and \
                        not self.robot.isAlmostBack() and \
                        self.robot.robotMode != 'reExplore':
                        # find way back to start zone using fastest path algo (djikstra)
                        startnode = (self.robot.robotCenterH, self.robot.robotCenterW)
                        endnode = (1,1)
                        (instructions, endOrientation) = dijkstra(self.arena.get_2d_arr(), startnode, endnode, self.robot.robotHead)
                        # give instruction
                        self.send_data(instructions)
                        # update robot states (position and orientation)
                        (self.robot.robotCenterH, self.robot.robotCenterW) = endnode
                        self.robot.robotHead = endOrientation
                        continue
                    if self.robot.isAlmostBack() and self.exploredArea < 280:
                        self.robot.robotMode = 'reExplore'
                    if self.robot.robotMode == 'reExplore':
                        # reexplore, find the fastest path to the nearest unexplored cell
                        (instruction, endnode, endOrientation) = self.reExplore()
                        # give instruction
                        self.send_data(instruction)
                        # update robot states
                        (self.robot.robotCenterH, self.robot.robotCenterW) = endnode
                        self.robot.robotHead = endOrientation                        
                        continue
                #if havent reach any of above continue statements, just wall hugging
                instruction = self.wallHugging()
                # there's no need to update robot state because it is already done in wallHugging()
                # give instruction 
                self.send_data(instruction)

                if self.reachGoal == False:
                    self.reachGoal = self.robot.isInGoal()
                    
    def recv_data(self):
        data = self.client_socket.recv(self.buffer_size)
        data_s = data.decode('utf-8')
        print("ExplorationExample - Received data: {}".format(data_s))
        return data_s

    def send_data(self, data):
        self.client_socket.send(data.encode('utf-8'))

    def close_conn(self):
        self.client_socket.close()
        print("ExplorationExample - Connection cloased")

    def get_arena(self):
        if self.running:
            return self.arena
        else:
            return None

    def get_robot(self):
        return self.robot.getPosition()
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
        if (0 <= w <= 14 and 0 <= h <= 19):
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
                    realTimeMap.set(h+offsets[i][0], w+offsets[i][1], CellType.EMPTY)
                if value < self.MAX_SHORT_SENSOR:
                    realTimeMap.set(h+offsets[value][0], w+offsets[value][1], CellType.OBSTACLE)
            elif sensorIndex == 5:
                offsets = self.leftCells[head]
                for i in range(value):
                    realTimeMap.set(h+offsets[i][0], w+offsets[i][1], CellType.EMPTY)
                if value < self.MAX_LONG_SENSOR:
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
        for cell in robot.frontCells:
            if (robot.robotCenterW+cell[1] > 14 or robot.robotCenterH+cell[0] > 19 # boundary check
                or self.arena.get(robot.robotCenterH+cell[0],robot.robotCenterW+cell[1]) != CellType.EMPTY): 
                return False
            else:
                return True                   
    # check whether the 3 consecutive cells on robot right are empty
    def checkRight(self):
        robot = self.robot
        for cell in robot.rightCells:
            if (robot.robotCenterW+cell[1] > 14 or robot.robotCenterH+cell[0] > 19 # boundary check
                or self.arena.get(robot.robotCenterH+cell[0],robot.robotCenterW+cell[1]) != CellType.EMPTY): 
                return False
            else:
                return True
    def wallHugging(self): # return instruction
        # mark current body cells as empty
        # actually might not need, just put here first
        bodyCells = self.robot.returnBodyCells()
        for cell in bodyCells:
            self.arena.set(cell[0],cell[1],CellType.EMPTY)
                
        # decide turn-right condition
        if (self.checkRight()):
            # chage the internal state of the robot
            self.robot.rotateRight()
            self.robot.forward()        
            return ("RF")
                        
        # decide front condition
        elif (self.checkFront()):
            self.robot.forward()
            return ("F")
        else:
            self.robot.rotateLeft()
            return ("L")
    def reExplore(self):
        # detect all unexplored cells
        reExploreCells = []
        cellEuclidean = []
        robot = self.robot
        for row in self.arena.get_2d_arr():
            for cell in row:
                if (cell == CellType.UNKNOWN):
                    reExploreCells.append(cell)
        # calculate Euclidean distance for each
        for cell in reExploreCells:
            euclideanDist =euclidean([robot.robotCenterH,robot.robotCenterW],cell)
            cellEuclidean.append(euclideanDist)
            
        # find the nearest one
        targetCell = reExploreCells[findArrayIndexMin(cellEuclidean)]
        
        # find its nearest observing point
        offsets = [[-2,1],[-2,0],[-2,-1],[-1,-2],[0,-2],[1,-2],[2,-1],[2,0],[2,1],[1,2],[0,2],[-1,2]]
        potentialPos = []
        index2 = 0
        for offset in offsets:
            potentialPos.append([targetCell[0]+offset[index2][0],targetCell[1]+offset[index2][1]])
            index2 += 1
        # calculate Euclidean distance for each
        posDistance = []
        for cell in potentialPos:
            dist = euclidean([robot.robotCenterH,robot.robotCenterW],cell)
            posDistance.append(dist)
        cellToMove = potentialPos[findArrayIndexMin(posDistance)]
        # use djikstra
        startnode = (robot.robotCenterH, robot.robotCenterW)
        (instr, endOrientation) = dijkstra(self.arena.get_2d_arr(), startnode, cellToMove, robot.robotHead)
        return (instr, cellToMove, endOrientation)
        # need to check robot final head direction
###### helper functions #####    
def findArrayIndexMin(arr):
    return arr.index(min(arr))
            
def euclidean(pos1,pos2):
    return abs(pos1[1]-pos2[1])+abs(pos1[0]-pos2[0])

