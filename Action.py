class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

ACT_DICT = {
    'REGISTER':'reg', 
    'WORK':'wrk', 
    'REMOVE':'rmv', 
    'ANSWER':'ans', 
    'ACK':'ack'
}

ACTION = AttributeDict(ACT_DICT)
