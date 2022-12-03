class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

CODE_DICT = {
    'OK': '200',
    'BAD_REQUEST': '400',
    'NOT_ALLOWED': '405',
    'NOT_FOUND': '404',
    'IM_A_TEAPOT': '418',
    'DUPLICATED': '422',
    'NOT_UMPLEMENTED': '501'
}

STATUS = AttributeDict(CODE_DICT)
