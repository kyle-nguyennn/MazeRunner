from Map import Map
from Robot import Robot


        
# UpdateMap gets sensor inputs and use then to update map
def UpdateMap():
    pass
#IMPLEMENTATION NEEDED
        
# in rushing mode, run A* search to get back to Start
def rushing(tExe,tLimit):
    pass
# IMPLEMENTATION NEEDED

def exploreUnvisited(robot,mapArray):
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
            if (0 <= index <= 2): # front sensors
                pass
            elif (3 <= index <= 4):# right sensors
                pass
            else: # left sensor
                pass
    return realMap

# given inputs, find corresponding cell coordinates needed to be marked as 0 or 1
def findCells(sensorIndex,head,w,h):
    pass
    

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
    
    robot.Mode = "exploring"
    
    # get first map reading without moving the robot
    robot.commandCallBack(robot,realTimeMap,"none") # for the first instruction, don't move, just sense
    
    while (explorationTime < timeThreshold):
          
        # assume previous step gives sensor reading
        # now update map using sensor value
        
        
        if (robot.robotCenterW == 1 and robot.robotCenterH == 1 and cnt > 20): # set as 20 first, any reasonable number just to make sure that the robot is not just started 
            if (exploredArea >= 250):
			      # reach back to Start; exploration done
                robot.robotMode = "done"
                break
        elif (almostBack(robot.robotCenterW,robot.robotCenterH) and exploredArea < 250 ):
            robot.robotMode = "reExplore"
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
                robot.commandCallBack(robot,realTimeMap,"right")
                robot.commandCallBack(robot,realTimeMap,"front")
                continue
				
            # decide front condition
            if (checkFront(robot,realTimeMap)):
                robot.moveFront()
                cnt += 1
                robot.commandCallBack(robot,realTimeMap,"front")
                continue
            else:
                robot.turnLeft()
                robot.commandCallBack(robot,realTimeMap,"left")
                continue
        
    # change to rushing mode
    if (robot.robotMode != "done"):
        robot.rushing(explorationTime,timeLimit)
    # else, done.
        

		
		
		
		
		
		
		
		