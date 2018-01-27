from Commander import CommanderComposite
from RobotController import RobotController
from Simulator import Simulator, PCSimulator, AndroidSimulator
if __name__ == "__main__":
    commander = CommanderComposite()
    commander.add(RobotController())
    commander.add(AndroidSimulator())
    commander.forward()