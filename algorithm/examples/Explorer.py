import threading, queue, exploration
from queue import Queue

class ExplorerThread(threading.Thread):
    def __init__(self, sensorsQueue, instructionQueue):
        super(ExplorerThread, self).__init__()
        self.insQ = instructionQueue
        self.senQ = sensorsQueue
        self.stoprequest = threading.Event()
        self.cur = (1,1)
        #AQ add, to track robot direction for algo processing
        self.head = 1

    def run(self):
        while not self.stoprequest.isSet():
            try:
                sensors = self.senQ.get(True, 0.05) # set blocking to true, meaning the thread will wait until there is some instruction
                                                        # set timeout=0.05, meaning it only waits for 0.05s before throwing error
                (instruction, self.cur, self.head, map) = self.compute(sensors,cur,head,realTimeMap) # AQ modify function arguments
                self.insQ.put((instruction, self.cur))
                if self.cur == (18, 13):
                    self.insQ.put(("END", (18,13)))
                    break
            # catching error but ignore it and wait again
            except queue.Empty:
                continue
    
    def join(self, timeout=None):
        self.stoprequest.set()
        super(ExplorerThread, self).join(timeout)

#    def compute(self, sensors):
#        print("Explorer: received sensors data: " + str(sensors))
#        print("Explorer: computing the moves based on sensors data ... ")
#        newX = min(self.cur[0]+5, 18)
#        newY = min(self.cur[1]+4, 13)
#        return ("Some dummy instruction", (newX, newY))
        
   # AQ add. Main exploration logic
    def compute(self,sensors,cur,head):
        exploration.explore(sensors,cur,head)