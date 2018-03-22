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

class Explorer():
    def __init__(self, tcp_conn, robot_pos, buffer_size=1024, tBack=20, tThresh=330, pArea=1, alignLimit=2, needReExplore=False, logging_enabled=True):
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
        self.tcp_conn = tcp_conn
        self.auto_update = False
        self.status = ""
        self.logging_enabled = logging_enabled
        self.log_filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ".log"
        self.arena = Arena()
        self.needReExplore = needReExplore
        #self.robot = [1, 1, 0] # 2d position plus orientation
        ### CONSTANT ####
        self.MAX_SHORT_SENSOR = 3
        self.MAX_LONG_SENSOR = 6
        ##### exploration logics related variables ####
        self.exploredArea = 0
        self.cnt = 0 # no. of instruction executed
        self.goBackTime = tBack # seconds for it to go back Start from any position
        self.timeThreshold = tThresh # user-input time to terminate exploration
        self.timeLimit = 360
        self.areaPercentage = pArea # percentage we want the robot to explore up to
        self.reachGoal = False
        self.startTime = time.time()
        self.alignCntR = 0 # counter for robot alignment
        self.alignCntL = 0
        self.alignCnt = 0
        self.alignLimit = alignLimit
        self.alignNow = False
        self.reReadSensor = False
        self.readingConflict = False
        self.innerMap = []
        self.turnList = []
        self.isPrevTurn = False
        self.isPrevRight = False
        self.climbCnt = 0
        self.delayRight = 0
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
        while self.robot.robotMode != "done": 
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
                if self.reachGoal:
                    if self.needReExplore == False:
                        # use wall hugging to return back to start zone
                        if self.robot.robotCenterH == self.robot.robotCenterW == 1:
                            #check direction
                            if self.robot.robotHead != 2:
                                startnode = (self.robot.robotCenterH, self.robot.robotCenterW, int(self.robot.robotHead))
                                (instructions, endOrientation,cost) = dijkstra(self.arena.get_2d_arr(), startnode, (1,1,2), endOrientationImportant=True)
                                self.update_all(instructions, "Going back to start zone")
                                self.robot.robotMode = "done"
                                continue
                            else:
                                self.robot.robotMode = "done"
                                break
                            
                    else:   #need reExplore
                        if explorationTime > self.timeThreshold:
                            print("time2",explorationTime)
                            # and not self.robot.isAlmostBack():
                            # and self.robot.robotMode != 'reExplore':
                            
                            # find way back to start zone using fastest path algo (djikstra)
                            startnode = (self.robot.robotCenterH, self.robot.robotCenterW, int(self.robot.robotHead))
                            endnode = (1,1,2)
                            (instructions, endOrientation,cost) = dijkstra(self.arena.get_2d_arr(), startnode, endnode, endOrientationImportant=False)
                            # give instruction
                            self.cnt += len(instructions)
                            self.update_all(instructions, "Going back to start zone")
                            # update robot states (position and orientation)
                            self.robot.jump(endnode) # already update sensors inside
                            continue
                        # if less than 5 mins now, can go for exploration
                        if self.robot.isAlmostBack() and self.exploredArea < 300*self.areaPercentage and explorationTime < 300:
                            self.robot.robotMode = 'reExplore'
                        if self.robot.robotMode == 'reExplore':
                            # reexplore, find the fastest path to the nearest unexplored cell
                            (instructions, endnode) = self.reExplore()
                            # give instruction
                            self.cnt += len(instructions)
                            self.update_all(instructions, "Navigating to nearest unexplored cell")
                            # update robot states
                            self.robot.jump(endnode) # already update sensors inside
    
                            print("comeplete a re-exploration")
                            continue

                #if havent reach any of above continue statements, just wall hugging
                instruction = self.wallHugging()
                # there's no need to update robot state because it is already done in wallHugging()
                # give instruction 
                self.update_all(instruction, "Performing right wall hugging exploration")
                if self.reachGoal == False:
                    self.reachGoal = self.robot.isInGoal()
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
        count = self.countObstacles()
        self.wellGuess(count)
        print("Exploration time:",explorationTime)
        print("Instruction count:", self.cnt)
        
        self.tcp_conn.send_command("CF0CS0RCF0R")
        self.robot.jump((1,1,0))
        
        self.tcp_conn.send_command(json.dumps({"event": "endExplore"}))
        self.update_all("EE", "End exploration")

    def wellGuess(self,count):
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

        # if count == 30:
        #     for row in self.arena.get_2d_arr():
        #         for cell in row:
        #             if cell != CellType.OBSTACLE:
        #                 cell = CellType.EMPTY
        #
        # elif count > 30: # more obstacles than expected
        #     obstacles = []
        #     for h in range(20):
        #         for w in range(15):
        #             if self.arena.get(h,w) == CellType.OBSTACLE:
        #                 score = self.innerMap[h][w]
        #                 obstacles.append([h,w,score])
        #     sortedObstacles = sorted(obstacles,key=itemgetter(2))
        #     throwNumber = 30-count
        #     throwCells = sortedObstacles[throwNumber:]
        #     for cell in throwCells:
        #         self.arena.set(cell[0],cell[1],CellType.EMPTY)
        #     # put all other as empty
        #     for row in self.arena.get_2d_arr():
        #         for cell in row:
        #             if cell != CellType.OBSTACLE:
        #                 cell = CellType.EMPTY
        #
        # else: # less than expected
        #     candidateCells = []
        #     unexploredCells = []
        #     for h in range(20):
        #         for w in range(15):
        #             if self.arena.get(h,w) != CellType.OBSTACLE:
        #                 score = self.innerMap[h][w]
        #                 if score < 0:
        #                     candidateCells.append([h,w,score])
        #                 elif score == 0:
        #                     unexploredCells.append([h,w,score])
        #     sortedCandidates = sorted(candidateCells,key=itemgetter(2))
        #     addNumber = 30 - count
        #     addCells = sortedCandidates[:addNumber]
# =============================================================================           
#             if the number is still less than 30, check unexplored cells
#                if count + len(addCells) < 30: 
#                 # if plus unexplored cells, still less: most likely unexplored cells are obstacles
#                 if count+len(addCells)+len(unexploredCells) <= 30:
#                     for cell in unexploredCells:
#                         addCells.append(cell)
# =============================================================================
            # it might be still less than 30, but it's fine.
        #     for cell in addCells:
        #         self.arena.set(cell[0],cell[1],CellType.OBSTACLE)
        #
        # # clean up all other non-obstacles to EMPTY
        # for h in range(20):
        #     for w in range(15):
        #         if self.arena.get(h,w) != CellType.OBSTACLE and self.arena.get(h,w) != CellType.UNKNOWN:
        #                self.arena.set(h,w,CellType.EMPTY)
            

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
            log_file.write("Map: \n" + self.arena.display_str())
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
    
    def checkAlign(self,r):
        self.alignNow = False
        self.alignSensor = ''
        head = int(self.robot.robotHead)
        if head > 0:
            head1 = head- 1
        else:
            head1 = 3
            
        for i in range(r):
            frontCells = self.frontCells[self.robot.robotHead]
            rightCells = self.rightCells[self.robot.robotHead]
            h = self.robot.robotCenterH
            w = self.robot.robotCenterW

            # check curner cell conditoin, if corner cell, just do two 
            if [h,w] in self.wallCells[head1][i] \
            and [h,w] in self.wallCells[head][i]:
                self.alignSensor = ''.join(["CF",str(i),"CS",str(i)])
                self.alignNow = True
                self.alignCnt = 0
                self.alignCntR = 0
                break
                
            # check front condition
            if [h,w] in self.wallCells[head1][i] \
            or self.arena.get(h+frontCells[0][i][0],w+frontCells[0][i][1]) == self.arena.get(h+frontCells[1][i][0],w+frontCells[1][i][1]) == self.arena.get(h+frontCells[2][i][0],w+frontCells[2][i][1]) == CellType.OBSTACLE :
               self.alignSensor = ''.join(["CF",str(i)])
               self.alignNow = True
               self.alignCnt = 0
            
            # check right condition
            if self.alignCntR > self.alignLimit:
                if [h,w] in self.wallCells[head][i] \
                or self.arena.get(h+rightCells[0][i][0],w+rightCells[0][i][1]) == self.arena.get(h+rightCells[1][i][0],w+rightCells[1][i][1]) == self.arena.get(h+rightCells[2][i][0],w+rightCells[2][i][1]) == CellType.OBSTACLE:
                    if [h,w] not in self.wallCells[head1][1] and [h,w] not in self.wallCells[head1][2]:
                        self.alignSensor = ''.join(["CS",str(i)])
                        self.alignNow = True
                        self.alignCntR = 0
                        self.alignCnt = 0
                    
            if len(self.alignSensor) == 0:
                if self.alignCntL > 2 and self.alignCnt > 2:
                    # check left wall, do possible calibration
                    index = 0
                    count = 0
                    for leftCell in self.leftAllCells[head]:
                        if index == 0 or index == 3 or index ==6:
                            if self.is_valid_point([leftCell[0]+h,leftCell[1]+w]) and self.arena.get(leftCell[0]+h,leftCell[1]+w) == CellType.OBSTACLE:
                                count += 1
                        index += 1
                    print("count",count)
                    if count >= 3: # 3 block on left for calibration
                        self.alignSensor = ''.join(["LCF",str(i),"R"])
                        self.alignNow = True 
                        self.alignCntL = 0
                        self.alignCnt = 0
                        
            # if all cannot fulfill, use two blocks to calibrate
# =============================================================================
#             if len(self.alignSensor) == 0:
#                 if self.alignCnt > 2:
#                     if self.are_valid_points([[h+rightCells[0][i][0],w+rightCells[0][i][1]],[h+rightCells[1][i][0],w+rightCells[1][i][1]],[h+rightCells[2][i][0],w+rightCells[2][i][1]]])\
#                     and self.arena.get(h+rightCells[0][i][0],w+rightCells[0][i][1]) == self.arena.get(h+rightCells[1][i][0],w+rightCells[1][i][1]) == CellType.OBSTACLE :
#                         self.alignSensor = ''.join(["CS",str(i)])
#                         self.alignNow = True
#                         self.alignCnt = 0
#                         self.alignCntR = 0
#                     elif self.are_valid_points([[h+frontCells[0][i][0],w+frontCells[0][i][1]],[h+frontCells[1][i][0],w+frontCells[1][i][1]],[h+frontCells[2][i][0],w+frontCells[2][i][1]]])\
#                     and (self.arena.get(h+frontCells[0][i][0],w+frontCells[0][i][1]) == self.arena.get(h+frontCells[1][i][0],w+frontCells[1][i][1]) == CellType.OBSTACLE \
#                     or self.arena.get(h+frontCells[1][i][0],w+frontCells[1][i][1]) == self.arena.get(h+frontCells[2][i][0],w+frontCells[2][i][1]) == CellType.OBSTACLE):
#                         self.alignSensor = ''.join(["CF",str(i)])
#                         self.alignNow = True
#                         self.alignCnt = 0
#                     elif self.are_valid_points([[h+rightCells[0][i][0],w+rightCells[0][i][1]],[h+rightCells[1][i][0],w+rightCells[1][i][1]],[h+rightCells[2][i][0],w+rightCells[2][i][1]]])\
#                     and (self.arena.get(h+rightCells[0][i][0],w+frontCells[0][i][1]) == self.arena.get(h+rightCells[2][i][0],w+rightCells[2][i][1]) == CellType.OBSTACLE \
#                     or self.arena.get(h+rightCells[1][i][0],w+rightCells[1][i][1]) == self.arena.get(h+rightCells[2][i][0],w+rightCells[2][i][1]) == CellType.OBSTACLE) :
#                         self.alignSensor = ''.join(["RCF",str(i),"L"])
#                         self.alignNow = True
#                         self.alignCnt = 0
#                         self.alignCntR = 0
# =============================================================================
            
            # if still no wall to calibrate
            if len(self.alignSensor) == 0:
                continue
            else:
                break
            
            
    def checkFront(self):
        robot = self.robot
        frontCells = robot.frontCells
        for cell in frontCells[robot.robotHead]:
            if (robot.robotCenterW+cell[1] > 14 or robot.robotCenterH+cell[0] > 19 \
                or robot.robotCenterW+cell[1] < 0 or robot.robotCenterH+cell[0] < 0 \
                or self.arena.get(robot.robotCenterH+cell[0],robot.robotCenterW+cell[1]) != CellType.EMPTY): 
                return False
        print("check front true")
        return True                   
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
    
    def wallHugging(self): # return instruction
        # mark current body cells as empty
        # actually might not need, just put here first
        sensor = "" 
        bodyCells = self.robot.returnBodyCells()
        for cell in bodyCells:
            # if robot was on this cell, it confirms to be empty
            self.innerMap[cell[0]][cell[1]] += 2

        if self.isPrevTurn == True:
            self.alignCntR = 9 
        self.isPrevTurn = False
        self.checkAlign(1)
        self.alignCntR += 1
        self.alignCntL += 1
        self.alignCnt += 1
        print("robot center:",self.robot.robotCenterH,self.robot.robotCenterW)
        print("robot head:",self.robot.robotHead)        
        print("staricase climb counter",self.climbCnt)

        print("prevRight:",self.isPrevRight)

        if (self.isPrevRight == False and (self.climbCnt == 0 or (self.climbCnt == 2 and self.delayRight == 0))): #if climbCnt == 1, shouldn't check right condition first, should check front first
            # decide turn-right condition
            if (self.checkRight(1) == "true"):  
                print("check right true here")                  
                if self.alignNow == True:
                    sensor = self.alignSensor
                # for every turn, calibrate
                else:
                    self.alignCntR = 9
                    self.checkAlign(1)
                    sensor = self.alignSensor
                self.robot.rotateRight()
                self.turnList.append([self.robot.robotCenterH,self.robot.robotCenterW])
                #self.robot.forward()
                self.isPrevTurn = True
                self.isPrevRight = True
                return (''.join([sensor,"R"])) #previously RF here
            
            elif (self.checkRight(1) == "unknown"):
                print("right unknown")
                if self.alignNow == True:
                    sensor = self.alignSensor
                # for every turn, calibrate
                else:
                    self.alignCntR = 9
                    self.checkAlign(1)
                    sensor = self.alignSensor
                self.robot.rotateRight()
                self.turnList.append([self.robot.robotCenterH,self.robot.robotCenterW])
                self.isPrevTurn = True
                self.isPrevRight = True
                return (''.join([sensor,"R"]))
            
            elif (self.checkRight(1) == "stairs"):
                self.climbCnt = 2
                self.delayRight = 1

        self.isPrevRight = False # same, reset
        # decide front condition
        if (self.checkFront()):
            self.robot.forward()
            if self.alignNow == True:
                sensor = self.alignSensor
            if self.delayRight == 1:
                self.delayRight = 0
            elif self.climbCnt > 0: # if delayRight == 0 and climbCnt > 0
                self.climbCnt -= 1
            return (''.join([sensor,"F"]))

        if self.climbCnt == 2: # and checkFront() == False implicitly
            if self.alignNow == True:
                sensor = self.alignSensor
            # for every turn, calibrate
            else:
                self.alignCntR = 9
                self.checkAlign(1)
                sensor = self.alignSensor
            self.robot.rotateRight()
            self.turnList.append([self.robot.robotCenterH,self.robot.robotCenterW])
            #self.robot.forward()
            self.climbCnt = 0
            self.isPrevRight = True
            self.isPrevTurn = True
            return (''.join([sensor,"R"])) # if checkRight return "stairs", means at least at immediate right side of the robot is empty; otherwise it won't go into check stairs case; so can safely turn right here
            # previously RF here

        skipSteps = False
        
        # haven't debug yet, leave it first
# =============================================================================
#         skipSteps = True
#         h = self.robot.robotCenterH
#         w = self.robot.robotCenterW
#         for cell in self.frontCells[self.robot.robotHead]:
#             if not self.is_valid_point(cell[0]) or self.arena.get(cell[0][0]+h,cell[0][1]+w) != CellType.EMPTY:
#                 skipSteps = False
#                 break
#         if skipSteps == True:
#             for cell1 in self.leftAllCells[self.robot.robotHead]:
#                 if self.is_valid_point([cell1[0]+h,cell1[1]+w]) and self.arena.get(cell1[0]+h,cell1[1]+w) != CellType.EMPTY:
#                     skipSteps = False
#                     print("false empty")
#                     break
#         if skipSteps == True:
#             for cell2 in self.frontLeftCells[self.robot.robotHead]:
#                 if self.is_valid_point([cell2[0]+h,cell2[1]+w]) and self.arena.get(cell2[0]+h,cell2[1]+w) != CellType.OBSTACLE:
#                     skipSteps = False
#                     print("false obstacle")
#                     break
# =============================================================================
        
        # for every turn, calibrate
        self.alignCntR = 9
        self.checkAlign(1)
        sensor = self.alignSensor
        self.robot.rotateLeft()
        self.climbCnt = 0
        self.isPrevTurn = True
        if skipSteps == False:
            return (''.join([sensor,"L"]))
        else:
            self.alignCntR += 3
            return (''.join([sensor,"LCS0FFF"])) 
        
    def allEmpty(self,h,w):
        for i in range(h-1,h+2):
            for j in range(w-1,w+2):
                if self.is_valid_point((i,j))==False or self.arena.get(i,j) != CellType.EMPTY:
                    return False
        return True
    
    def searchObservableCells(self,cells,sensorRange):
        # search cell which: line withint sensor range all clear, and front row of robot at observing point have 3 empty cells
        observableCells = []
        for cell in cells:
            print("exam cells:",cell)
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
            logging.debug("observable cells inside:" + str(observableCells))                                
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
     
        for x in range(len(self.arena.arena_map)):
            for y in range(len(self.arena.arena_map[x])):
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
            (instr, endNode,cost) = dijkstra(self.arena.get_2d_arr(), startnode, (1,1,2), endOrientationImportant=True) 
            self.robot.robotMode = "done"
            return (instr, endNode)

        # calculate Euclidean distance for each
        for cell in observableCells:
            euclideanDist =euclidean([robot.robotCenterH,robot.robotCenterW],cell)
            cellEuclidean.append(euclideanDist)
            observableCellsDist.append((cell,euclideanDist))
        
        # sort cellEuclidean distance and remove all duplicates
        cellEuclidean.sort()
        cellEuclidean = list(set(cellEuclidean))
        
        potentialPos = []
       # while len(potentialPos) == 0:  
            # pick k number of eucliean nearest cell candidates
        itemNo = 0
        noMore = False
        targetCells = []
        cellList = []
        for dist in cellEuclidean:
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
                if layer < 2:
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
                    if 0 <= indexOff < 3 or 12 <= indexOff < 15 or 24 <= indexOff < 27 or 36 <= indexOff < 39 :
                        if indexOff in [1,13,25,37]: # front only
                            node[2] = [0]
                            break
                        elif indexOff in [2,14,26,38]: # front and left and right
                            if indexOff != 38:
                                node[2] = [0,1,3]
                            else:
                                node[2] = [0,1]
                            break
                        else:
                            if indexOff != 36:
                                node[2] = [0,3] # front and right
                            else:
                                node[2] = [0]
                            break
                    elif 3 <= indexOff < 6 or 15 <= indexOff < 18 or 27 <= indexOff < 30 or 39 <= indexOff < 42:
                        if indexOff in [4,16,28,40]:
                            node[2] = [1]
                            break
                        elif indexOff in [5,17,29,41]:
                            if indexOff != 41:
                                node[2] = [1,2,0]
                            else:
                                node[2] = [1,2]
                            break
                        else:
                            if indexOff != 39:
                                node[2] = [1,0]
                            else:
                                node[2] = [1]
                            break
                    elif 6 <= indexOff < 9 or 18 <= indexOff < 21 or 30 <= indexOff < 33 or 42 <= indexOff < 45:
                        if indexOff in [7,19,31,43]:
                            node[2] = [2]
                            break
                        elif indexOff in [8,20,32,44]:
                            if indexOff != 44:
                                node[2] = [2,3,1]
                            else:
                                node[2] = [2,3]
                            break
                        else:
                            if indexOff != 42:
                                node[2] = [2,1]
                            else:
                                node[2] = [2]
                            break
                    else:
                        if indexOff in [10,22,34,46]:
                            node[2] = [3]
                            break
                        elif indexOff in [11,23,35,47]:
                            if indexOff != 46:
                                node[2] = [3,0,2]
                            else:
                                node[2] = [3,0]
                            break
                        else:
                            if indexOff != 45:
                                node[2] = [3,2]
                            else:
                                node[2] = [3]
                            break
                else:
                    indexOff += 1
            cellsToMove = []
            costs = []
            # find the path of less cost considring both front ahd right direction for same point
            for direction in node[2]:
                cellsToMove.append((node[0][0],node[0][1],direction))
            for cellToMove in cellsToMove:
                (instr, endNode,cost) = dijkstra(self.arena.get_2d_arr(), startnode, cellToMove, endOrientationImportant=True) 
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
            node[1] = cellsToMove[index] 
            node[2] = node[2][index]                  
            node[3] = minCost
            updatedNodes.append(node)
        logging.debug("potentialPos: " + str(updatedNodes))
        
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
        cellToMove = (updatedNodes[index][0][0], updatedNodes[index][0][1], updatedNodes[index][2])
# =============================================================================
#         print("cell to move:",cellToMove)
#         print("start cell:",startnode)
# =============================================================================
        (instr, endNode,cost) = dijkstra(self.arena.get_2d_arr(), startnode, cellToMove, endOrientationImportant=True) 
        logging.debug("Observing point " + str(endNode)) 
       
        # check calibration condition in reExplore
        sensor = ""
        self.checkAlign(1)
        if self.alignNow == True:
            sensor = self.alignSensor
        instr = ''.join([sensor, instr])
        logging.debug("instruction:"+instr)
        return (instr, endNode)

###### helper functions #####    
def findArrayIndexMin(arr):
    return arr.index(min(arr))
            
def euclidean(pos1,pos2):
    return abs(pos1[1]-pos2[1])+abs(pos1[0]-pos2[0])
