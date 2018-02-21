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