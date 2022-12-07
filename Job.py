

class Job():
    id = None       # int
    md5 = None      # str
    shards = None    # int
    start = None
    end = None
    numOfShards = None

    def __init__(self, id, md5, start, end) -> None:
        self.id = id
        self.md5 = md5
        self.shards = []
        self.start = start
        self.end = end
        self.numOfShards = 1