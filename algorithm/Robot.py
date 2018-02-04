class Robot():
    
    # attributes
    robotMode = "idle"  # modes: idle, exploring, rushing, reEnter
    sensorList = [] 
    robotHead = 1       # indicate robot head direction; "N","W","S","E" represented by 0,1,2,3 respectively
    robotCenterH = 1
    robotCenterW = 1
    frontCells = {}     # set front cells dictionary to find robot's front 3 cells
    rightCells = {}     # set right cells dictionary to find robot's right 3 cells
    
    def __init__ (self): #default constructor
        
        # initialize sensor value
        sensorList = [0,0,0,0,0,0]
        
        # mode is idle initially
        robotMode = "idle"
		
        # set robotHead to "South" direction
        robotHead = 1
		
        # initialize starting point
        robotCenterH = 1
        robotCenterW = 1
		
        rightCells = {0:[[2,1],[2,0],[2,-1]],
					       1:[[-1,-2],[0,-2],[1,-2]],
					       2:[[-2,1],[-2,0],[-2,-1]],
					       3:[[-1,2],[0,2],[1,2]]
        }
        
        frontCells = {0:[[-1,2],[0,2],[1,2]],
					       1:[[2,-1],[2,0],[2,1]],
					       2:[[-1.-2],[0,-2],[1,-2]],
					       3:[[-2,-1],[-2,0],[-2,1]]
        }
        
        
    # constructor with direction and starting coordinates    
    def __init__ (self,head,h,w):
        
        # initialize sensor value
        sensorList = [0,0,0,0,0,0]
        
        # mode is idle initially
        robotMode = "idle"
		
        # set robotHead to "South" direction
        # 0,1,2,3 represent N,E,S,W respectively
        robotHead = head
		
        # initialize starting point
        robotCenterH = h
        robotCenterW = w
		
        rightCells = {0:[[2,1],[2,0],[2,-1]],
					       1:[[-1,-2],[0,-2],[1,-2]],
					       2:[[-2,1],[-2,0],[-2,-1]],
					       3:[[-1,2],[0,2],[1,2]]
        }
        
        frontCells = {0:[[-1,2],[0,2],[1,2]],
					       1:[[2,-1],[2,0],[2,1]],
					       2:[[-1.-2],[0,-2],[1,-2]],
					       3:[[-2,-1],[-2,0],[-2,1]]
        }
        
        
    # given robot center, mark all 9 cells as empty
    def returnBodyCells(self):
        bodyCells = []
        for i in range(robotCenterW-1,robotCenterW+2):
            for j in range(robotCenterH-1,robotCenterH+2):
                c=bodyCells.append([i,j])
        return bodyCells


    # move front, update center cell coordinates
    def moveFront(self):
        if (robotHead == 0):		
            robotCenterH += 1
        elif (robotHead == 1):
            robotCenterW += 1
        elif (robotHead == 2):
            robotCenterH -= 1
        elif (robotHead == 3):
            robotCenterW -= 1
        else:
            print("Error: head direction out of bound")
              
    
    def turnRight(self):
        if (robotHead == 4):
            robotHead = 0
        else:
            robotHead += 1
    
    def turnLeft(self):
        if (robotHead == 0):
            robotHead = 4
        else:
            robotHead -= 1