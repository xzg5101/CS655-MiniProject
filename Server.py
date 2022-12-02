from Node import Node

class Server(Node):
    workerIpList = []

    def __init__(self):
        self.setNumCap()
        self.id = self.genId()