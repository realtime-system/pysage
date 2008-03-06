# util.py
import sys
import time

class Singleton(object):
    def __new__(cls, *args, **kwds):
        it = cls.__dict__.get("__it__")
        if it is not None:
            return it
        cls.__it__ = it = object.__new__(cls)
        it.init(*args, **kwds)
        return it
    @classmethod
    def get_singleton(cls, *args, **kwds):
        it = cls.__dict__.get("__it__")
        if it is not None:
            return it
        cls.__it__ = it = object.__new__(cls)
        it.init(*args, **kwds)
        return it      
    def init(self, *args, **kwds):
        pass
    
if sys.platform.startswith("win"):
    get_time = time.clock
else:
    get_time = time.time