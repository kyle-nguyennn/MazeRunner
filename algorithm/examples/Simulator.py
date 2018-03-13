from Explorer import ExplorerThread
from queue import Queue
import queue

# determine if the robot reach the goal
def reachGoal(cur):
    if cur == (18,13):
        return True
    return False

def executeAndSense(instruction):
    print("Simulator: received instruction: " + str(instruction))
    print("Simulator: Moving robot on the simulator ... ")
    print("Simulator: Sensing the environment from the new position ...")
    return ("Some dummy sensors data")

if __name__ == "__main__":
    # ....
    # when receive explore signal from UI
    insQ = Queue()
    senQ = Queue()
    explorer = ExplorerThread(senQ, insQ)
    explorer.start()
    senQ.put("123456")
    while True:
        try:
            (instruction, supposedPos) = insQ.get(True, 0.05)
            if instruction == "END":
                print("Simulator: Reach goal !!! Huray")
                explorer.join()
                break
            else:
                sensors = executeAndSense(instruction)
                print("Simulator: current position is supposed to be " + str(supposedPos))
                senQ.put(sensors)
        except queue.Empty:
            continue
        
        