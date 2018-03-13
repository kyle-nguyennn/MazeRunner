import abc
class CommanderInterface(metaclass = abc.ABCMeta):
    @abc.abstractmethod
    def forward(self, unit=1):
        pass
    @abc.abstractmethod
    def backward(self, unit=1):
        pass
    @abc.abstractmethod
    def rotateLeft(self, angle=90):
        pass
    @abc.abstractmethod
    def rotateRight(self, angle=90):
        pass

class CommanderComposite(CommanderInterface):
    def __init__(self):
        self._children = set()

    def forward(self, unit=1):
        print("Every child goes forward {} units".format(unit))
        for child in self._children:
            child.forward(unit)

    def backward(self, unit=1):
        print("Every child goes backward {} units".format(unit))
        for child in self._children:
            child.backward(unit)

    def rotateLeft(self, angle=90):
        print("Every child rotates left {} units".format(unit))
        for child in self._children:
            child.rotateLeft(angle)

    def rotateRight(self, angle=90):
        print("Every child rotates right {} units".format(unit))
        for child in self._children:
            child.rotateRight(angle)

    def add(self, child):
        self._children.add(child)

    def remove(self, child):
        self._children.discard(child)
