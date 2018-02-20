class Robot():
    
    # attributes
    #robotMode = "idle"  # modes: idle, exploring, rushing, reExplore, break
    #robotHead = 1       # indicate robot head direction; "N","W","S","E" represented by 0,1,2,3 respectively
    #robotCenterH = 1
    #robotCenterW = 1
    #frontCells = {}     # set front cells dictionary to find robot's front 3 cells
    #rightCells = {}     # set right cells dictionary to find robot's right 3 cells
    
    def __init__ (self, mode="idle", head=0, h=1, w=1): # h is long dimension
        # mode is idle initially
        self.robotMode = mode
        # 0,1,2,3 represent N,E,S,W respectively
        self.robotHead = head
        # initialize starting point
        self.robotCenterH = h
        self.robotCenterW = w
		# TODO: what are these cells for ???
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
    def forward(self):
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
              
    
    def rotateRight(self):
        self.robotHead = (self.robotHead + 1) %4
    
    def rotateLeft(self):
        self.robotHead = (self.robotHead - 1) %4