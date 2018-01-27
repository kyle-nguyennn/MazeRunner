from Commander import CommanderInterface
class Simulator(CommanderInterface):
    def forward(self, unit=1):
        print("Simulator goes forward {} units".format(unit))

    def backward(self, unit=1):
        pass

    def rotateLeft(self, angle=90):
        pass

    def rotateRight(self, angle=90):
        pass

class PCSimulator(Simulator):
    def forward(self, unit=1):
        print("PCSimulator goes forward {} units".format(unit))

    def backward(self, unit=1):
        pass

    def rotateLeft(self, angle=90):
        pass

    def rotateRight(self, angle=90):
        pass

class AndroidSimulator(Simulator):
    def forward(self, unit=1):
        print("AndroidSimulator goes forward {} units".format(unit))

    def backward(self, unit=1):
        pass

    def rotateLeft(self, angle=90):
        pass

    def rotateRight(self, angle=90):
        pass