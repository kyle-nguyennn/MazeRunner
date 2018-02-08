from Map import Map,CellType
from Robot import Robot
        
# in rushing mode, run A* search to get back to Start
def rushing():
    pass
# IMPLEMENTATION NEEDED

def exploreUnvisited(robot,realMap):
    pass
# IMPLEMENTATION NEEDED
    
def almostBack(w,h):
    if (w <= 4 and h <= 4):
        return True
    else:
        return False
    
def commandCallBack(robot,realMap,instruction):
    
    # IMPLEMENTATION NEEDED
    # call some function for asynchronous call to Arduino
    # will get back and return sensor value
    
    # put dummy first, assuming no obstacles
    sensorValue = "AAAAAA"
    # F1,F2,F3,R1,R2,L1
    # process sensor value
    index = 0 # track character position
    for dist in sensorValue:
        if (dist == "A"):
            if (0 <= index <= 4): # front and right sensors
                dist = 4
            elif (index == 5):# left sensors
                dist = 8
            else:
                print("wrong index count") # for error checking only
        else:
            markCells(index,int(dist),robot.robotCenterW,robot.robotCenterH,robot.robotHead,realMap)
        index += 1

# given inputs, find corresponding cell coordinates needed to be marked as enum EMPTY or OBSTACLE
def markCells(sensorIndex,dist,w,h,head,realMap):
    frontCells = {0:[[[-1,2][-1,3][-1,4][-1,5]][[0,2][0,3][0,4][0,5]][[1,2][1,3][1,4][1,5]]],
                  1:[[[2,1][3,1][4,1][5,1]][[2,0][3,0][4,0][5,0]][[2,-1][3,-1][4,-1][5,-1]]],
                  2:[[[1,-2][1,-3][1,-4][1,-5]][[0,-2][0,-3][0,-4][0,-5]][[-1,-2][-1,-3][-1,-4][-1,-5]]],
                  3:[[[-2,-1][-3,-1][-4,-1][-5,-1]][[-2,0][-3,0][-4,0][-5,0]][[-2,1][-3,1][-4,1][-5,1]]]
        }
    
    # only keep top right and bottom right lines
    rightCells = {0:[[[2,1][3,1][4,1][5,1]][[2,-1][3,-1][4,-1][5,-1]]],
                  1:[[[1,-2][1,-3][1,-4][1,-5]][[-1,-2][-1,-3][-1,-4][-1,-5]]],
                  2:[[[-2,-1][-3,-1][-4,-1][-5,-1]][[-2,1][-3,1][-4,1][-5,1]]],
                  3:[[[-1,2][-1,3][-1,4][-1,5]][[1,2][1,3][1,4][1,5]]]
        }
    
    # only keep top left lines, detect up to the 7 cells in front
    leftCells = {0:[[-2,1][-3,1][-4,1][-5,1][-6,1][-7,1][-8,1]],
                 1:[[1,2][1,3][1,4][1,5][1,6][1,7][1,8]],
                 2:[[2,-1][3,-1][4,-1][5,-1][6,-1][7,-1][8,-1]],
                 3:[[-1,-2][-1,-3][-1,-4][-1,-5][-1,-6][-1,-7][-1,-8]]
            }
    
    if (0 <= sensorIndex <= 2):
        for i in range(0,dist):
            # mark empty
            realMap.unset(w+frontCells[head][sensorIndex][i][0],h+frontCells[head][sensorIndex][i][1])
        #mark obstacle
        if (dist <= 3):
            realMap.set(w+frontCells[head][sensorIndex][dist][0],h+frontCells[head][sensorIndex][dist][1])

    elif (3 <= sensorIndex <= 4):
        for i in range(0,dist):
            #mark all cells empty before obstacle
            realMap.unset(w+rightCells[head][sensorIndex-3][i][0],h+rightCells[head][sensorIndex-3][i][1])
        #mark obstacle
        if (dist <= 3):
            realMap.set(w+rightCells[head][sensorIndex-3][dist][0],h+rightCells[head][sensorIndex-3][dist][1])
        
    elif (sensorIndex == 5):
        for i in range(0,dist):
            #mark all cells empty before obstacle
            realMap.unset(w+leftCells[head][i][0],h+leftCells[head][i][1])
        #mark obstacle
        if (dist <= 7):
            realMap.set(w+leftCells[head][dist][0],h+leftCells[head][dist][1])
    
    else:
        print("sensor index out of bound")
    

# check whether the 3 consecutive cells in front are empty
def checkFront(robot,realMap):
    for cell in robot.frontCells[robot.robotHead]:
        if (realMap.get(robot.robotCenterW+cell[0],robot.robotCenterH+cell[1]) != 0):
            return False
        return True
					
# check whether the 3 consecutive cells on robot right are empty
def checkRight(robot,realMap):
    for cell in robot.rightCells[robot.robotHead]:
        if (realMap.get(robot.robotCenterW+cell[0],robot.robotCenterH+cell[1]) != 0):
            return False
        return True
			
	
def main(self,robotCenterW,robotCenterH,robotHead):
    robot = Robot(robotHead,robotCenterH,robotCenterW) #head,w,h all set to 1 (i.e. Starting position facing East)
    # to ask, assuming already have an internal map
    realTimeMap = Map()
    #realTimeMapArray = realTimeMap.get2dArr()
    cnt = 0
    # check exploration time first
    
    exploredArea = 0    	# 0 out of 300 initially
    timeLimit = 360    	# total time allowed for explration is 360 seconds
    timeThreshold = 300 	# if 300 seconds past, robot need to break and rush back
    explorationTime = 0 	# track robot exploration time
    
    # start counting explorationTime
    # IMPLEMENTATION NEEDED LATER
    
    robot.robotMode = "exploring"
    
    # get first map reading without moving the robot
    robot.commandCallBack(robot,realTimeMap,"N") # for the first instruction, don't move, just sense
    
    while (explorationTime < timeThreshold): # time can afford to do exploration       
        
        if (cnt > 30 and almostBack(robot.robotCenterW,robot.robotCenterH) and exploredArea < 250 ):
            robot.robotMode = "reExplore"
            # some action needed, implement later
            break
        
        elif (cnt > 30 and robot.robotCenterW == 1 and robot.robotCenterH == 1): # set as 30 first, any reasonable number just to make sure that the robot is not just started 
			      # reach back to Start; exploration done
            robot.robotMode = "done"
            break          
                
        else: 
            # mark current body cells as empty
            # actually might not need, just put here first
            bodyCells = robot.returnBodyCells()
            for cell in bodyCells:
                realTimeMap.unset(cell[0],cell[1])
				
            # decide turn-right condition
            if (checkRight(robot,realTimeMap)):
                robot.turnRight()
                robot.moveFront()
                cnt += 1
                robot.commandCallBack(robot,realTimeMap,"R")
                robot.commandCallBack(robot,realTimeMap,"F")
                # is it possible to make "R" command both turn right and move one cell forward? so one less command reading, might save time
                continue
				
            # decide front condition
            if (checkFront(robot,realTimeMap)):
                robot.moveFront()
                cnt += 1
                robot.commandCallBack(robot,realTimeMap,"F")
                continue
            else:
                robot.turnLeft()
                robot.commandCallBack(robot,realTimeMap,"L")
                continue
        
    if(robot.robotMode == "done"):
        pass
    elif(robot.robotMode == "reExplore"):
        # switch to reexploration mode
        pass
    else:
        robot.robotMode = "rushing"
        # rushing to be implemented here
        pass

        

		
		
		
		
		
		
		
		