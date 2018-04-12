# -*- coding: utf-8 -*-
"""
Created on Fri Apr  6 11:00:17 2018

@author: daq11
"""

from arena import Arena,CellType
from Robot import Robot
from random import randint
import datetime
import time, socket, logging, sys
import race
from race import dijkstra
from tcp_client import TcpClient
import json
from operator import itemgetter
import re

class Explorer():
    def __init__(self, tcp_conn, robot_pos, buffer_size=1024, tBack=20, tThresh=330, pArea=1, needReExplore=True, alignStairs = True, logging_enabled=True):
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
        self.tcp_conn = tcp_conn
        self.auto_update = False
        self.status = ""
        self.logging_enabled = logging_enabled
        self.log_filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ".log"
        self.arena = Arena()
        self.needReExplore = needReExplore
        ##### exploration logics related variables ####
        self.exploredArea = 0
        self.cnt = 0 # no. of instruction executed
        self.goBackTime = tBack # seconds for it to go back Start from any position
        self.timeThreshold = tThresh # user-input time to terminate exploration
        self.timeLimit = 360
        self.areaPercentage = pArea # percentage we want the robot to explore up to
        self.reachGoal = False
        self.startTime = time.time()
        self.alignNow = False
        self.reReadSensor = False
        self.readingConflict = False
        self.innerMap = []
        self.turnList = []
        self.isPrevTurn = False
        self.isPrevRight = False
        self.alignStairs = alignStairs
        self.climbCnt = 0
        self.delayRight = 0
        self.alignCntH = 0 # horizontal displacement counter
        self.alignCntV = 0 # vertical displacement counter
        self.alignDict = {'R':1,
                          'L':1,
                          'F':0.5}
        self.alignCntHLimit = 2
        self.alignCntVLimit = 2
        self.breakPoints = []
        self.robotPosList = []
        self.alignSensor = "" # CF(front), CS(right)
        self.robot = Robot(
            'exploring', robot_pos[2]/90, robot_pos[0], robot_pos[1])

        self.frontCells = {0:[[[2,-1],[3,-1],[4,-1]],[[2,0],[3,0],[4,0]],[[2,1],[3,1],[4,1]]],
                    1:[[[1,2],[1,3],[1,4]],[[0,2],[0,3],[0,4]],[[-1,2],[-1,3],[-1,4]]],
                    2:[[[-2,1],[-3,1],[-4,1]],[[-2,0],[-3,0],[-4,0]],[[-2,-1],[-3,-1],[-4,-1]]],
                    3:[[[-1,-2],[-1,-3],[-1,-4]],[[0,-2],[0,-3],[0,-4]],[[1,-2],[1,-3],[1,-4]]]
            }
        # only keep top right and bottom right lines
        self.rightCells = {0:[[[1,2],[1,3],[1,4]],[[-1,2],[-1,3],[-1,4]],[[0,2],[0,3],[0,4]]],
                    1:[[[-2,1],[-3,1],[-4,1]],[[-2,-1],[-3,-1],[-4,-1]],[[-2,0],[-3,0],[-4,0]]],
                    2:[[[-1,-2],[-1,-3],[-1,-4]],[[1,-2],[1,-3],[1,-4]],[[0,-2],[0,-3],[0,-4]]],
                    3:[[[2,-1],[3,-1],[4,-1]],[[2,1],[3,1],[4,1]],[[2,0],[3,0],[4,0]]]
            }
        # only keep top left lines, detect up to the 6 cells in front
        self.leftCells = {0:[[1,-2],[1,-3],[1,-4],[1,-5],[1,-6],[1,-7]],
                    1:[[2,1],[3,1],[4,1],[5,1],[6,1],[7,1]],
                    2:[[-1,2],[-1,3],[-1,4],[-1,5],[-1,6],[-1,7]],
                    3:[[-2,-1],[-3,-1],[-4,-1],[-5,-1],[-6,-1],[-7,-1]]
                }
        self.leftAllCells = {0:[[1,-2],[1,-3],[1,-4],[0,-2],[0,-3],[0,-4],[-1,-2],[-1,-3],[-1,-4]],
                             1:[[2,1],[3,1],[4,1],[2,0],[3,0],[4,0],[2,-1],[3,-1],[4,-1]],
                             2:[[-1,2],[-1,3],[-1,4],[0,2],[0,3],[0,4],[1,2],[1,3],[1,4]],
                             3:[[-2,-1],[-3,-1],[-4,-1],[-2,0],[-3,0],[-4,0],[-2,1],[-3,1],[-4,1]]
                }
        self.frontLeftCells = {0:[[2,-2],[2,-3],[2,-4]],
                               1:[[2,2],[3,2],[4,2]],
                               2:[[-2,2],[-2,3],[-2,4]],
                               3:[[-2,-2],[-3,-2],[-4,-2]]
                }
        # positions in wallCells are for calibration
        self.wallCells = {0:[[],[],[]],
                    1:[[],[],[]],
                    2:[[],[],[]],
                    3:[[],[],[]]
                }
        for i in range(1,19):
            self.wallCells[0][0].append([i,13])
            self.wallCells[2][0].append([i,1])
            if 2 <= i <= 17:
                self.wallCells[0][1].append([i,12])
                self.wallCells[2][1].append([i,2])
                if 3 <= i <= 16:
                    self.wallCells[0][2].append([i, 11])
                    self.wallCells[2][2].append([i, 3])
                if 2 <= i <= 12:
                    self.wallCells[1][1].append([2,i])
                    self.wallCells[3][1].append([17,i])
                    if 3 <= i <= 11:
                        self.wallCells[1][2].append([3, i])
                        self.wallCells[3][2].append([16, i])
            if 1 <= i <= 13:
                self.wallCells[1][0].append([1,i])
                self.wallCells[3][0].append([18,i])
        

    def run(self):
        cnt = 0
        self.innerMap =  [[0 for y in range(15)]
                          for x in range(20)]
        self.update_all("ES", "Start exploration")
        # set start and goal zone as definitely empty, cannot overwrite
        for i in range(3):
            for j in range(3):
                self.innerMap[i][j] += 99
        for i in range(17,20):
            for j in range(12,15):
                self.innerMap[i][j] += 99
        while self.robot.robotMode != "done": 
            if [self.robot.robotCenterH, self.robot.robotCenterW] == [1,1] and self.reachGoal:
                self.robot.robotMode = 'done'
                continue  # next loop should break because enter start zone
            cnt += 1 
            sensors = self.tcp_conn.get_string()
            if self.logging_enabled:
                log_file = open(self.log_filename, "a+")
                log_file.write("Received: " + sensors + "\n")
                log_file.close()
            # sensor check
            if len(sensors) != 6 or sensors.isdigit()==False:
                self.update_all("N", "Rechecking sensor reading from Arduino")
                continue                
            self.updateMap(sensors)
                            
            explorationTime = time.time() - self.startTime
            #check reachgoal
            if self.robot.robotCenterH == 18 and self.robot.robotCenterW == 13:
                self.reachGoal = True
            # if reach time limit
            if self.timeThreshold < explorationTime:
            #or self.exploredArea >= 300*self.areaPercentage:
                if self.robot.isInStartZone():
                    self.robot.robotMode = "done"
                    break
                else:
                    print("time",explorationTime)
                    print("areaExplore",self.exploredArea)
                    # find the way back to start zone using djikstra
                    startnode = (self.robot.robotCenterH, self.robot.robotCenterW, int(self.robot.robotHead))
                    endnode = (1,1,2) # face backwards, can calibrate CF and CS
                    (instructions, endOrientation,cost) = dijkstra(self.arena.get_2d_arr(), startnode, endnode, endOrientationImportant=False)
                    # give instruction
                    self.cnt += len(instructions)
                    self.update_all(instructions, "Going back to start zone")
                    # update robot states (position and orientation)
                    self.robot.jump(endnode)
                    continue
            else:
                if self.reachGoal and self.robot.isAlmostBack(8) and self.shouldGo():
                    self.robot.robotMode = 'reExplore'
                if self.robot.robotMode == 'reExplore':
                    (instructions, endnode, instruction_noCalibration) = self.reExplore()
                    if len(instruction_noCalibration) == 0:
                        instructions = "N"                   
                    # give instruction
                    self.cnt += len(instructions)
                    self.update_all(instructions, "Navigating to nearest unexplored cell")
                    # update robot states
                    self.robot.jump(endnode) # already update sensors inside
                    print("comeplete a re-exploration")
                    continue
                # else, doing wall hugging
                instruction = self.wallHugging()
                self.update_all(instruction, "Performing right wall hugging exploration")
        
        # berak out of while loop means finish exploring, now check ending direction            
        if self.robot.robotHead != 2 :
                startnode = (self.robot.robotCenterH, self.robot.robotCenterW, int(self.robot.robotHead))
                endnode = (1,1,2) # face backwards, can calibrate CF and CS
                (instructions, endOrientation,cost) = dijkstra(self.arena.get_2d_arr(), startnode, endnode, endOrientationImportant=False)
                self.update_all(instructions, "Changing head direction to South")
                self.robot.jump(endnode)

        if self.logging_enabled:
            log_file = open(self.log_filename, "a+")
            log_file.write("Prob map before any processing: \n" + self.innerMapToStr())
            log_file.close()

        #before exploration end, check innerMap
        self.wellGuess()
        self.robot.jump((1,1,0))
        print("Exploration time:",explorationTime)
        print("Instruction count:", self.cnt)
        
        self.tcp_conn.send_command("CF000CS000RCF000R")
        self.robot.jump((1,1,0))
        
        self.tcp_conn.send_event("endExplore")
        self.update_all("EE", "End exploration")
        

    def wellGuess(self):
        for h in range(20):
            for w in range(15):
                if self.arena.get(h,w) == CellType.CONFLICT:
                    score = self.innerMap[h][w]
                    if score < 0:
                        self.arena.set(h,w,CellType.OBSTACLE)
                    elif score > 0:
                        self.arena.set(h,w,CellType.EMPTY)
                    else:
                        continue
                    
    def wallHugging(self):
        bodyCells = self.robot.returnBodyCells()
        for cell in bodyCells:
            # if robot was on this cell, it confirms to be empty
            self.innerMap[cell[0]][cell[1]] += 5
        self.isPrevTurn = False
        print("robot center:",self.robot.robotCenterH,self.robot.robotCenterW)
        print("robot head:",self.robot.robotHead)        
        print("staricase climb counter",self.climbCnt)
        print("prevRight:",self.isPrevRight)
        robotCurrentPos = self.getRobotCurrentPos()
        print("currentPos:", robotCurrentPos)
        (instruction,states) = self.stateSimulation()        
        endnode = states[-1]
        self.robot.jump(endnode)
        
        if len(states) < 3:
            return instruction
        
        # since goal zone must pass through, whenever the simulation path include goal zone, must do a "waypoint" there
        if (18,13,0) in states or (18,13,1) in states or (18,13,2) in states or (18,13,3) in states:
            print("enter")
            (instruction1, endPoint1, cost, instr1_noCali) = dijkstra(self.arena.get_2d_arr(), robotCurrentPos, (18,13,0), endOrientationImportant=False, isExploring = True, Hcounter=self.alignCntH, Vcounter=self.alignCntV)
            (instruction2, endPoint2, cost, instr2_noCali) = dijkstra(self.arena.get_2d_arr(), endPoint1, endnode, endOrientationImportant=True, isExploring = True)
            self.reachGoal = True
            print("set reachGoal True")
            if len(instr1_noCali+instr2_noCali) == 0:
                return "N"
            else:
                return instruction1+instruction2
            
        elif ((1,1,0) in states or (1,1,1) in states or (1,1,2) in states or (1,1,3) in states) and self.reachGoal:  # should complete
            (instructions, endPoint,cost, instr_noCali) = dijkstra(self.arena.get_2d_arr(), robotCurrentPos, (1,1,0), endOrientationImportant=False, isExploring = True, Hcounter=self.alignCntH, Vcounter=self.alignCntV)
            self.robot.robotMode = 'done'
            if len(instr_noCali) == 0:
                return "N"
            else:
                return instructions
        
        else:
            print("use fastest path")
            (instructions, endPoint,cost, instr_noCali) = dijkstra(self.arena.get_2d_arr(), robotCurrentPos, endnode, endOrientationImportant=True, isExploring = True, Hcounter=self.alignCntH, Vcounter=self.alignCntV)
            print("dijkstra instructions:", instructions)
            if len(instr_noCali) == 0:
                return "N"
            else:
                return instructions    
            
        
    def stateSimulation(self):
        instructions = ''
        states= []
        startPosition = self.getRobotCurrentPos()
        states.append(startPosition)
        (next_instruction, robotNextPos) = self.nextStep()
        states.append(robotNextPos)
        instructions = ''.join([instructions, next_instruction])
        print("before canSkip")
        canSkip = self.canSkip(robotNextPos)
        while True:
            if canSkip == False:
                print("states:",states)
                return (instructions, states)
            else:
                (next_instruction, robotNextPos) = self.nextStep()
                states.append(robotNextPos)
                instructions = ''.join([instructions, next_instruction])
                canSkip = self.canSkip(robotNextPos)
                if ((1,1,0) in states or (1,1,1) in states or (1,1,2) in states or (1,1,3) in states) and self.reachGoal:   # if the path include start zone and self.reachGoal, should stop there
                    return (instructions, states) 
                if self.reachGoal and self.robot.isAlmostBack(8) and self.shouldGo():
                    self.robot.robotMode = 'reExplore'
                    return (instructions, states)
            
    def canSkip(self, robotNextPos):
        print("hello")
        h = robotNextPos[0]
        w = robotNextPos[1]
        head = robotNextPos[2]
        print("evaluating point:",h,w,head)
        if not self.isFrontAllKnown(h,w,head,0):  # previously is 2, but maybe can change to 0 becaseu if both left and right are explored, the robot can burst
            print("front false")
            return False
        if not self.isLeftAllKnown(h,w,head,4):
            print("left false")
            return False
        # decide the right allKnown range
        if head == 1 or head == 3:
            right_range = 0
        else:
            right_range = 2
        if not self.isRightAllKnown(h,w,head,right_range): 
            print("right false")
            return False
        return True
        
    def isFrontAllKnown(self,h,w,head,trust_range):  # trust_Range is sensor trust range
        block_pos = [trust_range+1,trust_range+1,trust_range+1] # block_pos is a list because need to record all block pos at front cells (3)
        # check where is the nearest block
        for j in range(3):
            for i in range(trust_range+1):
                offset = self.frontCells[head][j][i]
                cell = [h+offset[0],w+offset[1]]
                if cell[0] == 20 or cell[0] == -1 or cell[1] == -1 or cell[1] == 15: # wall
                    block_pos[j] = i
                    break
                elif not self.is_valid_point(cell):
                    return False
                elif self.arena.get(cell[0],cell[1]) == CellType.OBSTACLE:
                    block_pos[j] = i
                    break
        # check if: inside the nearest block, all cells are known to be empty
        for j in range(3):
            for i in range(block_pos[j]):
                offset = self.frontCells[head][j][i]
                cell = [h+offset[0],w+offset[1]]
                if block_pos[j] == 0:
                    break
                elif not self.is_valid_point(cell):
                    return False
                elif self.arena.get(cell[0],cell[1]) != CellType.EMPTY:
                    return False
        return True
    
    def isRightAllKnown(self,h,w,head,trust_range):
        block_pos = [trust_range+1,trust_range+1] # block_pos is a list because need to record all block pos at front cells (3)
        # check where is the nearest block
        for j in range(2):
            for i in range(trust_range+1):
                offset = self.rightCells[head][j][i]
                cell = [h+offset[0],w+offset[1]]
                if cell[0] == 20 or cell[0] == -1 or cell[1] == -1 or cell[1] == 15: # wall
                    block_pos[j] = i
                    break
                elif not self.is_valid_point(cell):
                    return False
                elif self.arena.get(cell[0],cell[1]) == CellType.OBSTACLE:
                    block_pos[j] = i
                    break
        # check if: inside the nearest block, all cells are known to be empty
        for j in range(2):
            for i in range(block_pos[j]):
                offset = self.rightCells[head][j][i]
                cell = [h+offset[0],w+offset[1]]
                if block_pos[j] == 0:
                    break
                elif not self.is_valid_point(cell):
                    return False
                elif self.arena.get(cell[0],cell[1]) != CellType.EMPTY:
                    return False
        return True
    
    def isLeftAllKnown(self,h,w,head,trust_range):
        block_pos = trust_range+1 # block_pos is a list because need to record all block pos at front cells (3)
        # check where is the nearest block
        for i in range(trust_range+1):
            offset = self.leftCells[head][i]
            cell = [h+offset[0],w+offset[1]]
            if cell[0] == 20 or cell[0] == -1 or cell[1] == -1 or cell[1] == 15: # wall
                block_pos = i
                break
            elif not self.is_valid_point(cell):
                return False
            elif self.arena.get(cell[0],cell[1]) == CellType.OBSTACLE:
                block_pos = i
                break
        # check if: inside the nearest block, all cells are known to be empty
        for i in range(block_pos):
            offset = self.leftCells[head][i]
            cell = [h+offset[0],w+offset[1]]
            if block_pos == 0:
                break
            elif not self.is_valid_point(cell):
                return False
            elif self.arena.get(cell[0],cell[1]) != CellType.EMPTY:
                return False
        return True            
    
    def getRobotCurrentPos(self):
        return (self.robot.robotCenterH, self.robot.robotCenterW, int(self.robot.robotHead))
            
            
    def nextStep(self):
        robotCurrentPos = self.getRobotCurrentPos()
        self.checkAlign(1)
        print("alignsensor:",self.alignSensor)
        print("cntH:",self.alignCntH)
        print("cntV:",self.alignCntV)
        self.clearAlignCnt()
        print("cntH:",self.alignCntH)
        print("cntV:",self.alignCntV)
        # previously is == 0, off staircase is < 2
        if (self.isPrevRight == False and (self.climbCnt == 0 or (self.climbCnt == 2 and self.delayRight == 0))): #if climbCnt == 1, shouldn't check right condition first, should check front first
            # decide turn-right condition
            if (self.checkRight(1) == "true"):  # previously only checkright == TRUe; if off stairs, add or self.checkRight(1) == "stairs"
                print("check right true here")                  
                self.robot.rotateRight(needUpdateSensor = True)
                robotCurrentPos = self.getRobotCurrentPos()
                if robotCurrentPos[2] == 1 or robotCurrentPos[2] == 3:
                    self.alignCntV += self.alignDict['R']
                else:
                    self.alignCntH += self.alignDict['R']
                #self.robot.forward()
                self.isPrevTurn = True
                self.isPrevRight = True
                return (''.join([self.alignSensor, 'R']), robotCurrentPos)
            elif (self.checkRight(1) == "unknown"):
                print("right unknown")
                self.robot.rotateRight(needUpdateSensor = True)
                robotCurrentPos = self.getRobotCurrentPos()
                if robotCurrentPos[2] == 1 or robotCurrentPos[2] == 3:
                    self.alignCntV += self.alignDict['R']
                else:
                    self.alignCntH += self.alignDict['R']
                self.isPrevTurn = True
                self.isPrevRight = True
                return (''.join([self.alignSensor, 'R']), robotCurrentPos)            
            elif (self.checkRight(1) == "stairs"):
                self.climbCnt = 2
                self.delayRight = 1
        
        self.isPrevRight = False # same, reset
        # decide front condition
        if (self.checkFront() == "true"):
            #forwardSteps = self.canBurst()   # no bursting now
            forwardSteps = 1
            self.robot.forward(needUpdateSensor = True)
            #self.robot.forward(), comment out because canBurst() already update robot position
            if self.delayRight == 1:
                self.delayRight = 0
            elif self.climbCnt > 0: # if delayRight == 0 and climbCnt > 0
                self.climbCnt -= 1
            f_str = ""
            robotCurrentPos = self.getRobotCurrentPos()
            self.alignCntH += self.alignDict['F']
            self.alignCntV += self.alignDict['F']
            if self.climbCnt == 0:
                for i in range(forwardSteps):
                    f_str = ''.join([f_str, "F"])
            else:
                return (''.join([self.alignSensor, 'F']), robotCurrentPos)
            return (''.join([self.alignSensor, f_str]), robotCurrentPos)
        elif (self.checkFront() == "unknown"):
            return (''.join([self.alignSensor, 'N']), robotCurrentPos) # need to stop and check
        
        if self.climbCnt == 2: # and checkFront() == False implicitly
            self.robot.rotateRight(needUpdateSensor = True)
            robotCurrentPos = self.getRobotCurrentPos()
            if robotCurrentPos[2] == 1 or robotCurrentPos[2] == 3:
                self.alignCntV += self.alignDict['R']
            else:
                self.alignCntH += self.alignDict['R']            
            #self.robot.forward()
            self.climbCnt = 0
            self.isPrevRight = True
            self.isPrevTurn = True
            return (''.join([self.alignSensor,"R"]), robotCurrentPos) # if checkRight return "stairs", means at least at immediate right side of the robot is empty; otherwise it won't go into check stairs case; so can safely turn right here
            # previously RF here
            
        #turn left
        self.robot.rotateLeft(needUpdateSensor = True)
        robotCurrentPos = self.getRobotCurrentPos()
        if robotCurrentPos[2] == 1 or robotCurrentPos[2] == 3:
            self.alignCntV += self.alignDict['L']
        else:
            self.alignCntH += self.alignDict['L'] 
        self.climbCnt = 0
        self.isPrevTurn = True
        return (''.join([self.alignSensor,'L']), robotCurrentPos)

        
    def allEmpty(self,h,w):
        for i in range(h-1,h+2):
            for j in range(w-1,w+2):
                if self.is_valid_point((i,j))==False or self.arena.get(i,j) != CellType.EMPTY:
                    return False
        return True
                   

    def is_valid_point(self, point):
        x = point[0]
        y = point[1]
        return (x >= 0 and x <20 and y >= 0 and y < 15)

    def get_arena(self):
        return self.arena

    def get_inner_map(self):
        return self.innerMap

    def get_robot(self):
        if self.robot.robotMode == "done":
            return None
        return self.robot.getPosition()       

    def update_all(self, command, status):
        if self.logging_enabled:
            log_file = open(self.log_filename, "a+")
            log_file.write("Robot: " + str(self.robot.getPosition()) + "\n")
            log_file.write("Map: \n" + self.arena.display_str(self.robot.getPosition()))
            log_file.write("Sent: " + command + "\n")
            log_file.close()
        self.tcp_conn.send_command(command)
        self.update_status(status)

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

    def shouldGo(self):
        for i in range(self.robot.robotCenterH+2,20):
            for j in range(15):
                if self.arena.get(i,j) == CellType.UNKNOWN:
                    return True
        return False
        
    
    
    def updateExploredArea(self):   
        count = 0
        for row in self.arena.get_2d_arr():
            for cell in row:
                if (cell == CellType.EMPTY or cell == CellType.OBSTACLE ):
                    count += 1
        self.exploredArea = count
        
    def countObstacles(self):   
        count = 0
        for row in self.arena.get_2d_arr():
            for cell in row:
                if (cell == CellType.OBSTACLE ):
                    count += 1
        return count

    def innerMapToStr(self):
        map_str = ''
        for h in range(20):
            row_str = ''
            for w in range(15):
                value = round(self.innerMap[h][w],1)
                row_str = ''.join([row_str,str(value),'  '])
            row_str = ''.join([row_str,'\n'])
            map_str = ''.join([map_str,row_str])
        return map_str
    
    # given inputs, find corresponding cell coordinates needed to be marked as enum EMPTY or OBSTACLE
    def markCells(self, sensorIndex, value):
        w = self.robot.robotCenterW
        h = self.robot.robotCenterH
        # if withint the map range, then mark. Otherwise discard the reading
        if (0 <= w <= 13 and 0 <= h <= 18):
            # sensorIndex = 0..5 corresponding to F1,F2,F3,R1,R2,L1
            # only the 5th sensor (top left) is long range sensor
            sensor = self.robot.sensors[sensorIndex]
            offsets = self.robot.visible_offsets(sensor)
            if value > sensor.visible_range:
                value = sensor.visible_range
            if value <= sensor.visible_range:
                for i in range(value):
                    x = h + offsets[i][0]
                    y = w + offsets[i][1]
                    if self.is_valid_point((x,y)):
                        # front-two-side weightage
                        if sensorIndex == 0 or sensorIndex == 2:
                            if i < 2:
                                self.innerMap[x][y] += 1
                            elif i == 2:
                                self.innerMap[x][y] += 0.7
                            elif i == 3:
                                self.innerMap[x][y] += 0.5
                            else:
                                self.innerMap[x][y] += 0.2
                        # front-middle weightage
                        elif sensorIndex == 1:
                            if i < 2:
                                self.innerMap[x][y] += 1
                            elif i == 2:
                                self.innerMap[x][y] += 0.5
                            else:
                                self.innerMap[x][y] += 0.2
                        # side sensor weightage
                        elif sensorIndex > 3:
                            if i < 2:
                                self.innerMap[x][y] += 1
                            elif i == 2:
                                self.innerMap[x][y] += 0.5
                            else:
                                self.innerMap[x][y] += 0.2
                        # long range weightage
                        else:
                            if i < 2:
                                self.innerMap[x][y] += 1
                            elif i == 2:
                                self.innerMap[x][y] += 0.7
                            elif i == 3:
                                self.innerMap[x][y] += 0.5
                            else:
                                self.innerMap[x][y] += 0.3
# =============================================================================
#                         logging.debug("Empty coordinate " + str(x) +" " + str(y))
# =============================================================================
            if value < sensor.visible_range:
                x = h + offsets[value][0]
                y = w + offsets[value][1]
                if self.is_valid_point((x,y)) and not (12 <= y <= 14 and 17 <= x <= 19): # goal zone cannot deduct
                    # front-two-side weightage
                        if sensorIndex == 0 or sensorIndex == 2:
                            if value < 2:
                                self.innerMap[x][y] -= 1
                            elif value == 2:
                                self.innerMap[x][y] -= 0.7
                            elif value == 3:
                                self.innerMap[x][y] -= 0.5
                            else:
                                self.innerMap[x][y] -= 0.2
                        # front-middle weightage
                        elif sensorIndex == 1:
                            if value < 2:
                                self.innerMap[x][y] -= 1
                            elif value == 2:
                                self.innerMap[x][y] -= 0.5
                            else:
                                self.innerMap[x][y] -= 0.2
                        # side sensor weightage
                        elif sensorIndex > 3:
                            if value < 2:
                                self.innerMap[x][y] -= 1
                            elif value == 2:
                                self.innerMap[x][y] -= 0.5
                            else:
                                self.innerMap[x][y] -= 0.2
                        # long range weightage
                        else:
                            if value < 2:
                                self.innerMap[x][y] -= 1
                            elif value == 2:
                                self.innerMap[x][y] -= 0.7
                            elif value == 3:
                                self.innerMap[x][y] -= 0.5
                            else:
                                self.innerMap[x][y] -= 0.3
                                
        
    def updateMap(self, sensorValues):
        for i in range(len(sensorValues)):
            self.markCells(i, int(sensorValues[i]))
        h = 0
        for row in self.innerMap:
            w = 0
            for cell in row:
# =============================================================================
#                 if h > 16 and w > 11 and cell <= -1: #detect goal zone wrongly to obstacle, need to fix all previous
#                     self.robot.robotMode = "inspect"
# =============================================================================
                
                if h > 16 and w > 11 and self.reachGoal: #at goal zone
                    self.arena.set(h,w,CellType.EMPTY)
                if h < 3 and w < 3:
                    self.arena.set(h,w,CellType.EMPTY)
                elif cell >= 1:
                    self.arena.set(h,w,CellType.EMPTY)
                elif cell == 0:
                    self.arena.set(h,w,CellType.UNKNOWN)
                elif -1 < cell < 1 :
                    self.arena.set(h,w,CellType.CONFLICT)
                else:
                    self.arena.set(h,w,CellType.OBSTACLE)
                w += 1
            h += 1
        self.updateExploredArea()

    def are_valid_points(self,cells):
        for cell in cells:
            if not self.is_valid_point(cell):
                return False
        return True
    
    def needFrontCalibration(self):
        if self.robot.robotHead == 1 or self.robot.robotHead == 3:
            if self.alignCntH > self.alignCntHLimit:
                return True
        else:
            if self.alignCntV > self.alignCntVLimit:
                return True
        return False
            
    def needSideCalibration(self):
        if self.robot.robotHead == 0 or self.robot.robotHead == 2:
            if self.alignCntH > self.alignCntHLimit:
                return True
        else:
            if self.alignCntV > self.alignCntVLimit:
                return True
        return False
        
    
    def checkAlign(self,r):
        self.alignNow = False
        self.alignSensor = ''
        head = int(self.robot.robotHead)
        if head > 0:
            head1 = head- 1
        else:
            head1 = 3
    
        frontCells = self.frontCells[self.robot.robotHead]
        rightCells = self.rightCells[self.robot.robotHead]
        h = self.robot.robotCenterH
        w = self.robot.robotCenterW

        # check curner cell conditoin, if corner cell, just do two
        if [h,w] in self.wallCells[head1][0] \
        and [h,w] in self.wallCells[head][0]:
            self.alignSensor = ''.join(["CF000","CS000"])
            self.alignNow = True
            return
        
        if [h, w] in self.wallCells[head1][0]:  # if face wall, do calibration
            self.alignNow = True
            self.alignSensor += "CF000"            
        
        if self.needFrontCalibration():
            # check front condition
            if (self.is_valid_point((h + frontCells[0][0][0],w + frontCells[0][0][1])) and \
                    self.arena.get(h + frontCells[0][0][0],w + frontCells[0][0][1]) == self.arena.get(h + frontCells[2][0][0],w + frontCells[2][0][1])  == self.arena.get(h + frontCells[1][0][0],w + frontCells[1][0][1]) == CellType.OBSTACLE):
                self.alignNow = True
                self.alignSensor += "CF000"
    
            elif self.is_valid_point((h + frontCells[0][0][0],w + frontCells[0][0][1])) and \
                  self.arena.get(h + frontCells[0][0][0],w + frontCells[0][0][1]) == self.arena.get(h + frontCells[2][0][0],w + frontCells[2][0][1]) == CellType.OBSTACLE:
                self.alignNow = True
                self.alignSensor += "CF090"
    
            elif self.is_valid_point((h + frontCells[0][0][0],w + frontCells[0][0][1])) and \
                  self.arena.get(h + frontCells[0][0][0],w + frontCells[0][0][1]) == self.arena.get(h + frontCells[1][0][0],w + frontCells[1][0][1]) == CellType.OBSTACLE:
                self.alignNow = True
                self.alignSensor += "CF009"
    
            elif self.is_valid_point((h + frontCells[0][0][0],w + frontCells[0][0][1])) and \
                  self.arena.get(h + frontCells[2][0][0],w + frontCells[2][0][1]) == self.arena.get(h + frontCells[1][0][0],w + frontCells[1][0][1]) == CellType.OBSTACLE:
                self.alignNow = True
                self.alignSensor += "CF900"
            
            # calibrate stairs
            elif self.alignStairs == True:
                f10 = frontCells[0][0]
                f11 = frontCells[0][1]
                f20 = frontCells[1][0]
                f21 = frontCells[1][1]
                f30 = frontCells[2][0]
                f31 = frontCells[2][1]
                if (self.is_valid_point((h + f10[0],w + f10[1])) and self.is_valid_point((h + f11[0],w + f11[1]))):
                    if self.arena.get(h+f10[0],w+f10[1]) == CellType.OBSTACLE:
                        if self.arena.get(h+f31[0],w+f31[1]) == CellType.OBSTACLE:
                            self.alignNow = True
                            self.alignSensor += "CF091"
                        elif self.arena.get(h+f21[0],w+f21[1]) == CellType.OBSTACLE:
                            self.alignNow = True
                            self.alignSensor += "CF019"
                    elif self.arena.get(h+f20[0],w+f20[1]) == CellType.OBSTACLE:       
                        if self.arena.get(h+f11[0],w+f11[1]) == CellType.OBSTACLE:
                            self.alignNow = True
                            self.alignSensor += "CF109"
                        elif self.arena.get(h+f31[0],w+f31[1]) == CellType.OBSTACLE:
                            self.alignNow = True
                            self.alignSensor += "CF901"     
                    elif self.arena.get(h+f30[0],w+f30[1]) == CellType.OBSTACLE:       
                        if self.arena.get(h+f11[0],w+f11[1]) == CellType.OBSTACLE:
                            self.alignNow = True
                            self.alignSensor += "CF190"
                        elif self.arena.get(h+f21[0],w+f21[1]) == CellType.OBSTACLE:
                            self.alignNow = True
                            self.alignSensor += "CF910"  

        # check right condition
        if self.needSideCalibration():
            if ([h, w] in self.wallCells[head][0] \
                 or (self.is_valid_point((h + rightCells[0][0][0],w + rightCells[0][0][1])) and \
                    self.arena.get(h + rightCells[0][0][0],w + rightCells[0][0][1]) == self.arena.get(h + rightCells[1][0][0],w + rightCells[1][0][1]) == CellType.OBSTACLE)):
                if [h, w] in self.wallCells[head][0] or self.arena.get(h + rightCells[2][0][0],w + rightCells[2][0][1]) == CellType.OBSTACLE:
                    self.alignSensor += "CS000"
                else:
                    self.alignSensor += "CS090"
                self.alignNow = True
                return
            # elif self.is_valid_point((h + rightCells[0][i][0],w + rightCells[0][i][1])) and \
            #         self.arena.get(h + rightCells[0][i][0],w + rightCells[0][i][1]) == self.arena.get(h + rightCells[2][i][0],w + rightCells[2][i][1]) == CellType.OBSTACLE:
            #     self.alignNow = True
            #     self.alignSensor = "RCF110L"
            #     break
            
            elif self.is_valid_point((h + rightCells[0][0][0],w + rightCells[0][0][1])) and \
                    self.arena.get(h + rightCells[2][0][0],w + rightCells[2][0][1]) == self.arena.get(h + rightCells[1][0][0],w + rightCells[1][0][1]) == CellType.OBSTACLE and self.arena.get(h + rightCells[0][0][0],w + rightCells[0][0][1]) != CellType.OBSTACLE:
                self.alignNow = True
                self.alignSensor += "RCF900L"
                return
    
                    
            if len(self.alignSensor) == 0:
                    index = 0
                    count = 0
                    for leftCell in self.leftAllCells[head]:
                        if index == 0 or index == 3 or index ==6:
                            if self.is_valid_point([leftCell[0]+h,leftCell[1]+w]) and self.arena.get(leftCell[0]+h,leftCell[1]+w) == CellType.OBSTACLE:
                                count += 1
                        index += 1
                    if count >= 3: # 3 block on left for calibration
                        self.alignSensor += 'LCF000R'
                        self.alignNow = True 

    def clearAlignCnt(self):
        converted_sensor = re.sub("RCF[0-9]{3}L","CS000",self.alignSensor) # convert both to calibration side
        converted_sensor = re.sub("LCF[0-9]{3}R","CS000",converted_sensor)
        print("finish converting")
        # converted, now can process
        if "CF" in converted_sensor: # clear front calibration
            print("CF solved")
            if self.robot.robotHead == 1 or self.robot.robotHead == 3:
                self.alignCntH = 0
            else:
                self.alignCntV = 0
        if "CS" in converted_sensor: # check side calibration
            print("CS solved")
            if self.robot.robotHead == 0 or self.robot.robotHead == 2:
                self.alignCntH = 0
            else:
                self.alignCntV = 0

    def canBurst(self):
        burstSteps = 1  # if already entered checkFront == True condition in wall hugging, means can at least go forward by one step; i.e. burstSteps == 1
        while True:
            self.robot.forward()
            h = self.robot.robotCenterH
            w = self.robot.robotCenterW
            head = int(self.robot.robotHead)
            if [h,w] == [15,13] and head == 0 and self.checkFront(): # if front is goal zone, can burst in
                burstSteps += 3
                for j in range(3):
                    self.robot.forward()
                break
            
            if not [h,w] in self.wallCells[head][0]:
                if not self.is_valid_point((h+self.rightCells[head][0][0][0], w+self.rightCells[head][0][0][1])) or \
                self.arena.get(h+self.rightCells[head][0][0][0], w+self.rightCells[head][0][0][1]) != CellType.OBSTACLE:                    
                    break
            if not self.isLeftAllKnown(h,w,head,4):
                break
            if not self.checkFront():
                break
            # else, burst plus 1
            burstSteps += 1
        return burstSteps


    def checkFront(self):
        robot = self.robot
        frontCells = robot.frontCells
        for cell in frontCells[robot.robotHead]:
            if not self.is_valid_point((robot.robotCenterH+cell[0],robot.robotCenterW+cell[1])):
                return "false"
            if self.arena.get(robot.robotCenterH+cell[0],robot.robotCenterW+cell[1]) == CellType.OBSTACLE: 
                return "false"
            if self.arena.get(robot.robotCenterH+cell[0],robot.robotCenterW+cell[1]) == CellType.UNKNOWN:
                return "unknown"
        print("check front true")
        return "true"                   
    # check whether the 3 consecutive cells on robot right are empty
    def checkRight(self,layer):
                
        robot = self.robot
        rightCells = self.rightCells[robot.robotHead]
        
        h = robot.robotCenterH
        w = robot.robotCenterW
        
        for cell in rightCells:
            for r in range(layer):
                if (robot.robotCenterW+cell[0][1] > 14 or robot.robotCenterH+cell[0][0] > 19 \
                    or robot.robotCenterW+cell[0][1] < 0 or robot.robotCenterH+cell[0][0] < 0 \
                    or self.arena.get(robot.robotCenterH+cell[0][0],robot.robotCenterW+cell[0][1]) == CellType.OBSTACLE):
                    return "false"
                elif (self.arena.get(robot.robotCenterH+cell[0][0],robot.robotCenterW+cell[0][1]) == CellType.UNKNOWN \
                      or self.arena.get(robot.robotCenterH+cell[0][0],robot.robotCenterW+cell[0][1]) == CellType.CONFLICT):
                    return "unknown"

        # this part is to determine staircase condition
        stairs = True
        # if all level 1 right cells are empty, check level 2
        for cell in rightCells:
            # staircase only happen if bottom right is block and middle and front right is empty
            if cell == rightCells[1]:
                if not self.is_valid_point([robot.robotCenterH+cell[1][0],robot.robotCenterW+cell[1][1]]) \
                or self.arena.get(robot.robotCenterH+cell[1][0],robot.robotCenterW+cell[1][1]) != CellType.OBSTACLE:
                    stairs = False
                    break
            else:
                if not self.is_valid_point([robot.robotCenterH+cell[1][0],robot.robotCenterW+cell[1][1]]) \
                or self.arena.get(robot.robotCenterH+cell[1][0],robot.robotCenterW+cell[1][1]) != CellType.EMPTY:
                    stairs = False
                    break
                
        if stairs == True:
            return "stairs"
        
        # before return true, check infinite loop
        # the loop breaking algo here is bug-free,but can be improved. not finalized
        if (len(self.turnList)>= 4 and [h,w] == self.turnList[-4])\
        or self.turnList.count([h,w]) > 3:
            print("loop false")
            return "false"
        return "true"
    

    
    def searchObservableCells(self,cells,sensorRange):
        # search cell which: line withint sensor range all clear, and front row of robot at observing point have 3 empty cells
        observableCells = []
        for cell in cells:
            appended = False
            h = cell[0]
            w = cell[1]
            for side in range(4):
                #print("direction:",side)
                if appended == True:
                    break
                if side == 0 or side == 2:
                    #check intermediate cells
                    allClear = True                    
                    for i in range(1,sensorRange+1):
                        j = i
                        if side == 0:
                            j = j*(-1)
                        if self.is_valid_point((h+j,w)) == False or self.arena.get(h+j,w) != CellType.EMPTY:  # should UNKNWON be included
                            #print("h,w:",str(h+j),w)
                            allClear = False
                            break
                    if allClear == False: # if allClear at this direction is False, continue loop with a new direction
                        continue
                    else: # test for body of observing point
                        j = sensorRange+2
                        if side == 0:
                            j = j*(-1)
                        if not self.allEmpty(h+j,w) and not self.allEmpty(h+j,w+1) and not self.allEmpty(h+j,w-1):
                            #print("center of Ob:",str(h+j),w)
                            #print("not allEmpty")
                            continue #continue another direction
                        else:
                            #print("append observable cell:",cell)
                            observableCells.append(cell)
                            appended = True
                            break

                else: # side == 1 or 3
                    #check intermediate cells
                    for i in range(1,sensorRange+1):
                        allClear = True
                        j = i
                        if side == 1:
                            j = j*(-1)
                        if self.is_valid_point((h,w+j)) == False or self.arena.get(h,w+j) != CellType.EMPTY:  # should UNKNWON be included
                            #print("h,w:",str(h+j),w)                            
                            allClear = False
                            break
                    if allClear == False: # if allClear at this direction is False, continue loop with a new direction
                        continue
                    else: # test for body of observing point
                        j = sensorRange+2
                        if side == 1:
                            j = j*(-1)
                        if not self.allEmpty(h,w+j) and not self.allEmpty(h-1,w+j) and not self.allEmpty(h+1,w+j):
                            #print("center of Ob:",str(h+j),w)
                            #print("not allEmpty")
                            continue #continue another direction
                        else:
                            #print("append observable cell:",cell)
                            observableCells.append(cell)
                            appended = True
                            break
            #logging.debug("observable cells inside:" + str(observableCells))                                
        return observableCells
            
            
        
    def reExplore(self):
            
        # detect all unexplored cells
        reExploreCells = []
        observableCellsDist = []
        cellEuclidean = []
        targetCells = []
        robot = self.robot
        noOfPicks = 3
        
        startnode = (robot.robotCenterH, robot.robotCenterW, int(robot.robotHead)) #change to int(robothead) because somehow the robotHead is a float
     
        for x in range(len(self.arena.arena_map)-1,-1,-1):
            for y in range(len(self.arena.arena_map[x])-1,-1,-1):
                if (self.arena.get(x,y) == CellType.UNKNOWN or self.arena.get(x,y) == CellType.CONFLICT):
                    reExploreCells.append([x,y])
        
        layer = 0
        maxSensor = 2
        while (layer < maxSensor):         
            # only move to explore one of the boundary cells - cell that has at least one side has 3 consecutive empty blocks            
            observableCells = self.searchObservableCells(reExploreCells,layer) # can see up to 3 cells
            if len(observableCells) != 0: 
                break
            else:
                layer += 1

        if len(observableCells) == 0 and layer >= maxSensor: # no possible observation, go back
            (instr, endNode,cost, instr_noCali) = dijkstra(self.arena.get_2d_arr(), startnode, (1,1,2), endOrientationImportant=True,isExploring = True) 
            self.robot.robotMode = "done"
            return (instr, endNode, instr_noCali)
        # calculate Euclidean distance for each
        for cell in observableCells:
            euclideanDist =euclidean([robot.robotCenterH,robot.robotCenterW],cell)
            cellEuclidean.append(euclideanDist)
            observableCellsDist.append((cell,euclideanDist))
        logging.debug("observableCells2:" + str(observableCellsDist))
        
        # sort cellEuclidean distance and remove all duplicates
        cellEuclidean = list(set(cellEuclidean))
        cellEuclidean.sort()
        
        potentialPos = []
       # while len(potentialPos) == 0:  
            # pick k number of eucliean nearest cell candidates
        itemNo = 0
        noMore = False
        targetCells = []
        cellList = []
        for dist in cellEuclidean:
            print("dist:",dist)
            for cellTup in observableCellsDist:
                if cellTup[1] == dist:
                    if itemNo < noOfPicks:
                        targetCells.append(cellTup[0])
                        itemNo += 1
                        cellList.append(cellTup)
                if itemNo > noOfPicks:
                    noMore = True
                    break
            if noMore == True:
                break
# =============================================================================
#             for cell in cellList:
#                 observableCellsDist.remove(cell)
# =============================================================================
                        
        logging.debug("targetCells" + str(targetCells))
        for cell in targetCells:
            prevPosLength = len(potentialPos)
            layer = 0
            while (prevPosLength == len(potentialPos)):
                # find its nearest observing point
                offsets = [[-2,1],[-2,0],[-2,-1],[-1,-2],[0,-2],[1,-2],[2,-1],[2,0],[2,1],[1,2],[0,2],[-1,2], #layer 0
                           [-3,1],[-3,0],[-3,-1],[-1,-3],[0,-3],[1,-3],[3,-1],[3,0],[3,1],[1,3],[0,3],[-1,3], #layer 1
                           [-4,1],[-4,0],[-4,-1],[-1,-4],[0,-4],[1,-4],[4,-1],[4,0],[4,1],[1,4],[0,4],[-1,4], #layer 2
                           [-5,1],[-5,0],[-5,-1],[-1,-5],[0,-5],[1,-5],[5,-1],[5,0],[5,1],[1,5],[0,5],[-1,5]] #layer 3
                for offset in offsets[:(layer+1)*12]:
                    #print("layer:",layer)
                    allClear = True
                    if self.allEmpty(cell[0]+offset[0],cell[1]+offset[1]):
                        # check for intermediate cells condition
                        if offset[0] in [-1,0,1]: #check horizontal
                            if offset[1] < 0: # left
                                for i in range(offset[1]+2,0):
                                    if self.is_valid_point((cell[0],cell[1]+i)) == False or self.arena.get(cell[0],cell[1]+i) != CellType.EMPTY:
                                        allClear = False
                                        break
                            else: #right
                                for i in range(1,offset[1]-1):
                                    if self.is_valid_point((cell[0],cell[1]+i)) == False or self.arena.get(cell[0],cell[1]+i) != CellType.EMPTY:
                                        allClear = False
                                        break                                                                 
                        elif offset[1] in [-1,0,1]: #check vertical
                            if offset[0] < 0: # down
                                for i in range(offset[0]+2,0):
                                    if self.is_valid_point((cell[0]+i,cell[1])) == False or self.arena.get(cell[0]+i,cell[1]) != CellType.EMPTY:
                                        allClear = False
                                        break
                            else: #up
                                for i in range(1,offset[0]-1):
                                    if self.is_valid_point((cell[0]+i,cell[1])) == False or self.arena.get(cell[0]+i,cell[1]) != CellType.EMPTY:
                                        allClear = False
                                        break                    
                    else:
                        allClear = False
                    if allClear == True:
                        # potentialPos: [observingCoords,cellToObserveCoords]
                        #print("cell:",cell)
                        #print("obPoint:",[[cell[0]+offset[0],cell[1]+offset[1]]])
                        potentialPos.append([[cell[0]+offset[0],cell[1]+offset[1]],cell,0,0]) #default head is 0, cost = 0            
                if layer < 1:
                    layer += 1
                else:
                    break
        # sensor range here for reference
# =============================================================================
#         rightRange = 2
#         frontRange = 3
#         leftRange = 3
# =============================================================================
        
        # update all potentialPos values with dijkstra cost
        updatedNodes = [] 

        for node in potentialPos:
#        for [cellToGo,cellToOb,head,cost] in potentialPos:
            indexOff = 0
            for offset in offsets:
                if [node[0][0]-node[1][0],node[0][1]-node[1][1]] == offset:
                    if 0 <= indexOff < 3 or 12 <= indexOff < 15 or 24 <= indexOff < 27 or 36 <= indexOff < 39:
                        if indexOff in [1,13,25,37]: # front only   # ,37
                            if indexOff != 37:
                                node[2] = [0]
                            break
                        elif indexOff in [2,14,26,38]: # front and left and right
                            if indexOff < 26:
                                node[2] = [0,1,3]
                            elif indexOff < 38:
                                node[2] = [0,1]
                            else:
                                node[2] = [1]
                            break
                        else:
                            if indexOff < 24:
                                node[2] = [0,3] # front and right
                            elif indexOff < 36:
                                node[2] = [0]
                            break
                    elif 3 <= indexOff < 6 or 15 <= indexOff < 18 or 27 <= indexOff < 30 or 39 <= indexOff < 42:
                        if indexOff in [4,16,28,40]:
                            if indexOff != 40:
                                node[2] = [1]
                            break
                        elif indexOff in [5,17,29,41]:
                            if indexOff < 29:
                                node[2] = [1,2,0]
                            elif indexOff < 41:
                                node[2] = [1,2]
                            else:
                                node[2] = [2]
                            break
                        else:
                            if indexOff < 27:
                                node[2] = [1,0]
                            elif indexOff < 39:
                                node[2] = [1]
                            break
                    elif 6 <= indexOff < 9 or 18 <= indexOff < 21 or 30 <= indexOff < 33 or 42 <= indexOff < 45:
                        if indexOff in [7,19,31,43]:
                            if indexOff != 43:
                                node[2] = [2]
                            break
                        elif indexOff in [8,20,32,44]:
                            if indexOff < 32:
                                node[2] = [2,3,1]
                            elif indexOff < 44:
                                node[2] = [2,3]
                            else:
                                node[2] = [3]
                            break
                        else:
                            if indexOff < 30:
                                node[2] = [2,1]
                            elif indexOff < 42:
                                node[2] = [2]
                            break
                    else:
                        if indexOff in [10,22,34,46]:
                            if indexOff < 46:
                                node[2] = [3]
                            break
                        elif indexOff in [11,23,35,47]:
                            if indexOff < 35:
                                node[2] = [3,0,2]
                            elif indexOff < 47:
                                node[2] = [3,0]
                            else:
                                node[2] = [0]
                            break
                        else:
                            if indexOff < 33:
                                node[2] = [3,2]
                            elif indexOff < 45:
                                node[2] = [3]
                            break
                else:
                    indexOff += 1
            cellsToMoves = []
            costs = []
            # find the path of less cost considring both front ahd right direction for same point
            for direction in node[2]:
                cellsToMoves.append((node[0][0],node[0][1],direction))
            for cellToMove in cellsToMoves:
                (instr, endNode,cost, instr_noCali) = dijkstra(self.arena.get_2d_arr(), startnode, cellToMove, endOrientationImportant=True, isExploring = True) 
# =============================================================================
#                 print("dijkstra startnode:",startnode)
#                 print("dijkstra cellToMove:",cellToMove)
#                 print("dijkstra instr:",instr)
# =============================================================================
                costs.append(cost)
                minCost = costs[0]
                index = 0
                for cost in costs:
                    if cost < minCost:
                        minCost = cost
                        index += 1
            node[1] = cellsToMoves[index] 
            node[2] = node[2][index]                  
            node[3] = minCost
            updatedNodes.append(node)
        #logging.debug("potentialPos: " + str(updatedNodes))
        
        # find the minimum cost in potentialPos 
        # this algo can be optimized later
        minCost = 1000
        index = 0
        for choice in updatedNodes:
            if choice[3] < minCost and choice[3] != 0:
                minCost = choice[3]       
        for choice in updatedNodes:
            if choice[3] != minCost:
                index += 1
            else:
                break
        if len(updatedNodes) == 0:
            print("no more")
            cellToMove = (1,1,2)
        cellToMove = (updatedNodes[index][0][0], updatedNodes[index][0][1], updatedNodes[index][2])
# =============================================================================
#         print("cell to move:",cellToMove)
#         print("start cell:",startnode)
# =============================================================================
        (instr, endNode,cost, instr_noCali) = dijkstra(self.arena.get_2d_arr(), startnode, cellToMove, endOrientationImportant=True, isExploring = True) 
        logging.debug("Observing point " + str(endNode)) 
       
        # check calibration condition in reExplore
        sensor = ""
        self.checkAlign(1)
        if self.alignNow == True:
            sensor = self.alignSensor
        instr = ''.join([sensor, instr])
        logging.debug("instruction:"+instr)
        return (instr, endNode, instr_noCali)

###### helper functions #####    
def findArrayIndexMin(arr):
    return arr.index(min(arr))
            
def euclidean(pos1,pos2):
    return abs(pos1[1]-pos2[1])+abs(pos1[0]-pos2[0])
