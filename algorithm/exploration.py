from arena import Arena,CellType
from Robot import Robot
from random import randint
import time, socket
import race


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
            updateMap(sensors)
            explorationTime = time.time() - self.startTime
            # if reach time limit
            if self.timeLimit - explorationTime <= 20:
                if self.robot.isInStartZone():
                    self.send_data("S")
                    self.robot.robotMode = "done"
                    break
                else:
                    #TODO: find the way back to start zone
            else:
                if self.reachGoal:
                    if explorationTime > self.timeThreshold and \
                        not self.robot.isAlmostBack() and \
                        self.robot.robotMode != 'reExplore':
                        # TODO: find way back to start zone using fastest path algo
                        # TODO: give instruction
                        # TODO: update robot states (position and orientation)
                        continue
                    if self.robot.isAlmostBack() and self.exploredArea < 280:
                        self.robot.robotMode = 'reExplore'
                    if self.robot.robotMode == 'reExplore':
                        # TODO: reexplore, find the fastest path to the nearest unexplored cell
                        # TODO: give instruction
                        # TODO: update robot states
                        continue
                #if havent reach any of above continue statements, just wall hugging

                    
                    
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
        return self.robot
    ##### exploration logics #####

    def updateExploredArea(self):   
        count = 0
        for row in self.arena.get_2d_arr():
            for cell in row:
                if (cell != CellType.UNKNOWN):
                    count += 1
        self.exploredArea = count
    # given inputs, find corresponding cell coordinates needed to be marked as enum EMPTY or OBSTACLE
    def markCells(self, sensorIndex, dist):
        w = self.robot.robotCenterW
        h = self.robot.robotCenterH
        head = self.robot.robotHead
        realTimeMap = self.arena
        # if withint the map range, then mark. Otherwise discard the reading
        if (0 <= w <= 14 and 0 <= h <= 19):
        
            if (0 <= sensorIndex <= 2):
                for i in range(0,dist):
                    # mark empty
                    realTimeMap.set(h+frontCells[head][sensorIndex][i][0],w+frontCells[head][sensorIndex][i][1],CellType.EMPTY)
                #mark obstacle
                if (dist <= 3):
                    realTimeMap.set(h+frontCells[head][sensorIndex][dist][0],w+frontCells[head][sensorIndex][dist][1],CellType.OBSTACLE)
        
            elif (3 <= sensorIndex <= 4):
                for i in range(0,dist):
                    #mark all cells empty before obstacle
                    realTimeMap.set(h+rightCells[head][sensorIndex-3][i][0],w+rightCells[head][sensorIndex-3][i][1],CellType.EMPTY)
                #mark obstacle
                if (dist <= 3):
                    realTimeMap.set(h+rightCells[head][sensorIndex-3][dist][0],w+rightCells[head][sensorIndex-3][dist][1],CellType.OBSTACLE)
                
            elif (sensorIndex == 5):
                for i in range(0,dist):
                    #mark all cells empty before obstacle
                    realTimeMap.set(h+leftCells[head][i][0],w+leftCells[head][i][1],CellType.EMPTY)
                #mark obstacle
                if (dist <= 7):
                    realTimeMap.set(h+leftCells[head][dist][0],w+leftCells[head][dist][1],CellType.OBSTACLE)
            
            else:
                print("sensor index out of bound")
    def updateMap(self, sensorValue):
        # sensorValue = "AAAAAA"
        # F1,F2,F3,R1,R2,L1
        index = 0 # track string character position
        for dist in sensorValue:
            if (dist == "A"):
                if (0 <= index <= 4): # front and right sensors
                    dist = 3
                elif (index == 5):# left sensors
                    dist = 6
                else:
                    print("wrong index count") # for error checking only
            else:
                markCells(index,int(dist))
            index += 1
        self.updateExploredArea()
    # check whether the 3 consecutive cells in front are empty
    def checkFront(self):
        for cell in self.robot.frontCells:
            if (robot.robotCenterW+cell[1] > 14 or robot.robotCenterH+cell[0] > 19 # boundary check
                or self.arena.get(robot.robotCenterH+cell[0],robot.robotCenterW+cell[1]) != CellType.EMPTY): 
                return False
            else:
                return True                   
    # check whether the 3 consecutive cells on robot right are empty
    def checkRight(self):
        for cell in self.robot.rightCells:
            if (robot.robotCenterW+cell[1] > 14 or robot.robotCenterH+cell[0] > 19 # boundary check
                or self.arena.get(robot.robotCenterH+cell[0],robot.robotCenterW+cell[1]) != CellType.EMPTY): 
                return False
            else:
                return True
                
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
############################## below this is aiqing code ################
    
        
def rush():
    instr = race.getInstructions(realTimeMap,(robot.robotCenterH,robot.robotCenterW),(1,1),(1,1),(3,3),convertDirection(robot.robotHead))
    return (instr,(1,1),robot.robotHead, realTimeMap)
    # need to change to final robot head direction
        
def reExplore():
    # detect all unexplored cells
    reExploreCells = []
    cellEuclidean = []
    for row in realTimeMap:
        for cell in row:
            if (cell == CellType.UNKNOWN):
                reExploreCells.append(cell)
    # calculate Euclidean distance for each
    for cell in reExploreCells:
        euclideanDist =euclidean([robot.robotCenterH,robot.robotCenterW],cell)
        cellEuclidean.append(euclideanDist)
        
    # find the nearest one
    targetCell = reExploreCells[findArrayMin(cellEuclidean)]
    
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
        dist =euclidean([robot.robotCenterH,robot.robotCenterW],cell)
        posDistance.append(dist)
    cellToMove = potentialPos[findArrayMin(posDistance)]
    # modification on getInstructions needed, to include start and goal coordinates
    # use race.djikstra instead
    instr = race.getInstructions(realTimeMap,(robot.robotCenterH,robot.robotCenterW),cellToMove,cellToMove,(3,3),convertDirection(robot.robotHead))
    return (instr,cellToMove,robot.robotHead,realTimeMap)
    # need to check robot final head direction


def convertDirection(head):
    if (head == 0):
        return "north"
    elif (head == 1):
        return "east"
    elif (head == 2):
        return "south"
    elif (head == 3):
        return "west"
    else:
        print("error in converting")
    
def findArrayIndexMin(arr):
    return arr.index(min(arr))
            
def euclidean(pos1,pos2):
    return abs(pos1[1]-pos2[1])+abs(pos1[0]-pos2[0])
  
def wallHugging():
    global robot,realTimeMap
    # mark current body cells as empty
    # actually might not need, just put here first
    bodyCells = robot.returnBodyCells()
    for cell in bodyCells:
        realTimeMap.set(cell[0],cell[1],CellType.EMPTY)
    		
    # decide turn-right condition
    if (checkRight()):
        robot.turnRight()
        robot.moveFront()        
        return ("RF",(robot.robotCenterH,robot.robotCenterW),robot.robotHead,realTimeMap)
    				
    # decide front condition
    elif (checkFront()):
        robot.moveFront()
        return ("F",(robot.robotCenterH,robot.robotCenterW),robot.robotHead,realTimeMap)
    else:
        robot.turnLeft()
        return ("L",(robot.robotCenterH,robot.robotCenterW),robot.robotHead,realTimeMap)
    			
	


		
		
		
		
		
		
		
		