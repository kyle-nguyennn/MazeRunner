class Robot():
    
    # attributes
    #robotMode = "idle"  # modes: idle, exploring, rushing, reExplore, break
    #robotHead = 1       # indicate robot head direction; "N","W","S","E" represented by 0,1,2,3 respectively
    #robotCenterH = 1
    #robotCenterW = 1
    #frontCells = {}     # set front cells dictionary to find robot's front 3 cells
    #rightCells = {}     # set right cells dictionary to find robot's right 3 cells
    
    def __init__ (self): #default constructor
        
        
        # mode is idle initially
        self.robotMode = "idle"
		
        # set robotHead to "South" direction
        self.robotHead = 1
		
        # initialize starting point
        self.robotCenterH = 1
        self.robotCenterW = 1
		
        self.rightCells = {0:[[1,2],[0,2],[-1,2]],
					       1:[[-2,-1],[-2,0],[-2,1]],
					       2:[[1,-2],[0,-2],[-1,-2]],
					       3:[[2,-1],[2,0],[2,1]]
        }
        
        self.frontCells = {0:[[2,-1],[2,0],[2,1]],
					       1:[[-1,2],[0,2],[1,2]],
					       2:[[-2,-1],[-2,0],[-2,1]],
					       3:[[-1,-2],[0,-2],[1,-2]]
        }
        
        
    # constructor with direction and starting coordinates    
    def __init__ (self,head,h,w):
        
        # mode is idle initially
        self.robotMode = "idle"
		
        # set robotHead to "South" direction
        # 0,1,2,3 represent N,E,S,W respectively
        self.robotHead = head
		
        # initialize starting point
        self.robotCenterH = h
        self.robotCenterW = w
		
        self.rightCells = {0:[[1,2],[0,2],[-1,2]],
					       1:[[-2,-1],[-2,0],[-2,1]],
					       2:[[1,-2],[0,-2],[-1,-2]],
					       3:[[2,-1],[2,0],[2,1]]
        }
        
        self.frontCells = {0:[[2,-1],[2,0],[2,1]],
					       1:[[1,2],[0,2],[-1,2]],
					       2:[[-2,1],[-2,0],[-2,-1]],
					       3:[[-1,-2],[0,-2],[1,-2]]
        }
        
        
    # given robot center, mark all 9 cells as empty
    def returnBodyCells(self):
        bodyCells = []
        for i in range(self.robotCenterH-1,self.robotCenterH+2):
            for j in range(self.robotCenterW-1,self.robotCenterW+2):
                bodyCells.append([i,j])
        return bodyCells


    # move front, update center cell coordinates
    def moveFront(self):
        if (self.robotHead == 0):		
            self.robotCenterH += 1
        elif (self.robotHead == 1):
            self.robotCenterW += 1
        elif (self.robotHead == 2):
           self.robotCenterH -= 1
        elif (self.robotHead == 3):
            self.robotCenterW -= 1
        else:
            print("Error: head direction out of bound")
              
    
    def turnRight(self):
        if (self.robotHead == 4):
            self.robotHead = 0
        else:
            self.robotHead += 1
    
    def turnLeft(self):
        if (self.robotHead == 0):
            self.robotHead = 4
        else:
            self.robotHead -= 1