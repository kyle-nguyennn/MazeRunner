from socket_server import TCPClient
from Map import Map, CellType
from random import randint
import time


class ExplorationExample():
    def __init__(self):
        self._map = Map()

    def run(self):
        self._client = TCPClient('127.0.0.1', 6666)
        self._client.send("startExplore".encode('utf-8'))
        while True:
            data = self._client.recv()
            print(data.decode('utf-8'))
            self._map.set(randint(0, 19), randint(
                0, 14), CellType(randint(0, 1)))
            self._client.send("F".encode('utf-8'))
            data = self._client.recv()
            print(data.decode('utf-8'))
            self._map.set(randint(0, 19), randint(
                0, 14), CellType(randint(0, 1)))
            self._client.send("R".encode('utf-8'))
            data = self._client.recv()
            print(data.decode('utf-8'))
            self._map.set(randint(0, 19), randint(
                0, 14), CellType(randint(0, 1)))
            self._client.send("F".encode('utf-8'))
            data = self._client.recv()
            print(data.decode('utf-8'))
            self._map.set(randint(0, 19), randint(
                0, 14), CellType(randint(0, 1)))
            self._client.send("L".encode('utf-8'))
            data = self._client.recv()
            print(data.decode('utf-8'))
            self._map.set(randint(0, 19), randint(
                0, 14), CellType(randint(0, 1)))
            self._client.send("B".encode('utf-8'))
            data = self._client.recv()
            print(data.decode('utf-8'))
            self._map.set(randint(0, 19), randint(
                0, 14), CellType(randint(0, 1)))
            self._client.send("L".encode('utf-8'))
            data = self._client.recv()
            print(data.decode('utf-8'))
            self._map.set(randint(0, 19), randint(
                0, 14), CellType(randint(0, 1)))
            self._client.send("F".encode('utf-8'))
            data = self._client.recv()
            print(data.decode('utf-8'))
            self._map.set(randint(0, 19), randint(
                0, 14), CellType(randint(0, 1)))
            self._client.send("R".encode('utf-8'))

    def getMap(self):
        return self._map
