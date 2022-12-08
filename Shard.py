
class Shard():
    jid = None
    shardNo = None
    start = None
    end = None
    md5 = None
    answer = None
    stop = None
    checked = None
    

    def __init__(self, jid:int,  shardNo:int, start:int, end:int, md5:str) -> None:
        self.jid, self.start, self.end, self.md5 = jid, start, end, md5
        self.shardNo = shardNo
        self.stop = False
        self.checked = False