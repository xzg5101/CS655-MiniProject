
class Shard():
    jid = None
    start = None
    end = None
    md5 = None
    answer = None
    stop = None
    

    def __init__(self, jid:int,  start:int, end:int, md5:str) -> None:
        self.jid, self.start, self.end, self.md5 = jid, start, end, md5
        self.stop = False