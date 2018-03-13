from Commander import CommanderInterface
class RobotController(CommanderInterface):
    def forward(self, unit=1):
        print("Robot goes forward {} units".format(unit))

    def backward(self, unit=1):
        pass

    def rotateLeft(self, angle=90):
        pass

    def rotateRight(self, angle=90):
        pass
