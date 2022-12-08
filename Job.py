

class Job():
    id = None       # int
    md5 = None      # str
    shards = None    # int
    shard_flags = None
    start = None
    end = None
    numOfShards = None
    answer = None
    solved = None
    solver = None
    wkr_cnt = None
    result_list = None
    done = None

    def __init__(self, id, md5, start, end) -> None:
        self.id = id
        self.md5 = md5
        self.shards = []
        self.shard_flags = []
        self.start = start
        self.end = end
        self.solved = False
        self.numOfShards = 1
        self.wkr_cnt = 0
        self.done = False
        self.result_list = []

    def scanned(self):
        for i in self.shard_flags:
            if i == False :
                return False
        return True