from Map import Map
from Robot import Robot

exploredArea = 0    	# 0 out of 300 initially
timeLimit = 360    		# total time allowed for explration is 360 seconds
timeThreshold = 300 	# if 300 seconds past, robot need to break and rush back
explorationTime = 0 	# track robot exploration time
cnt = 0	    		  	# cnt increment for while loop, testing purpose.

        
# UpdateMap gets sensor inputs and use then to update map
def UpdateMap():
    pass
#IMPLEMENTATION NEEDED
        
# in rushing mode, run A* search to get back to Start
def rushing():
    pass
# IMPLEMENTATION NEEDED

def exploreUnvisited():
    pass
# IMPLEMENTATION NEEDED

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
    robot = Robot(1,1,1) #head,w,h all set to 1 (i.e. Starting position facing East)
    # to ask, assuming already have an internal map
    realTimeMap = Map()
    # check exploration time first
    
    # start counting explorationTime
    # IMPLEMENTATION NEEDED LATER
    
    robot.Mode = "exploring"
    
    while (explorationTime < timeThreshold):
        
        # robot coming back 
        # Haven't checked no. of cells explored for now, can add later
        if (robot.robotCenterW == 1 and robot.robotCenterH == 1 and cnt > 10): # set as 10 first, can adjust later 
            if (exploredArea >= 250):
			      # reach back to Start; exploration done
                robot.robotMode == "done"
                break
            else:
                # do not go back, switch to reEnter mode for unvisited cells
                robot.Mode = "reEnter"
                # IMPLEMENTATION NEEDED
                
        else: 
            # mark current body cells as empty
            bodyCells = robot.returnBodyCells()
            for cell in bodyCells:
                realTimeMap.unset(cell[0],cell[1])
				
            #sense surrounding and get sensor values
            # IMPLEMENTATION NEEDED
				
            # decide turn-right condition
            if (checkRight(robot,realTimeMap)):
                robot.turnRight()
                robot.moveFront()
                continue
				
            # decide front condition
            if (checkFront(robot,realTimeMap)):
                robot.moveFront()
                continue
            else:
                robot.turnLeft()
                continue
        cnt += 1
				
				
				
    # when time > threshold, switch to rushing mode
    # implement A* call here
		
		
		
		
		
		
		
		