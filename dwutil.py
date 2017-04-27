import math
def NS_TO_FT(x): return x*0.9836
def US_TO_FT(x): return x*983.6
def FT_TO_US(x): return x/983.6
def FT_TO_NS(x): return x/0.9836
def TIMEUNITS_TO_NS(x): return  (x *1000. / (128 * 499.2))
def TIMEUNITS_TO_US(x): return  (x / (128 * 499.2))
def TIMEUNITS_TO_FT(x): return x*0.01539337941
THRESH = 3000
ANTENNA_DELAY = 530

class Empty():
    pass


class Point:
    def __init__(self,x,y):
        self.x=x
        self.y=y


class factorydict(dict):
    def __init__(self, factory):
        super().__init__()
        self.factory = factory

    def __missing__(self, key):
        v = self.factory(key)
        self.__setitem__(key, v)
        return v

def distance(a, b):
    return math.sqrt(math.pow(a.x - b.x, 2) + math.pow(a.y - b.y, 2))

DWF_MARK_1=0x01
DWF_MARK_2 = 0x02
DWF_PING = 0x04
DWF_RESPONSE= 0x08
DWF_SLAVE= 0x10
def IS_MASTER(x):
    return (((x)&0xC000)==0xC000)
def IS_TAG(x):
    return (((x)&0xC000)==0x0000)


