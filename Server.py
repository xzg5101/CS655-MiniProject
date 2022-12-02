from Node import Node 
import math
class Server(Node):
    numOfWorker = None  # number of workers
    workerIdList = []   # list of worker id
    workerIpList = []   # list of worker ip
    jobList = []        # list of list

    def __init__(self):
        self.setNumCap()
        self.id = self.genId()
        self.numOfWorker = 0

    def divdeJob(self):
        # no workers
        if self.numOfWorker == 0:
            return
        
        # compute job ranges
        jobWidth = math.ceil(self.numCap/self.numOfWorker)
        base = 0
        for i in range(self.numOfWorker):
            self.jobList.append([base, min(base+jobWidth, self.numCap)])
            base += jobWidth
        
