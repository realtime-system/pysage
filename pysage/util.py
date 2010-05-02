# util.py
import sys
import time
import threading
import os

class Singleton(object):
    def __new__(cls, *args, **kwds):
        return cls.get_singleton(*args, **kwds)
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

class ProcessLocalSingleton(object):
    '''fork safe'''
    def __new__(cls, *args, **kwds):
        return cls.get_singleton(*args, **kwds)
    @classmethod
    def get_singleton(cls, *args, **kwds):
        it = cls.__dict__.get("__it__")
        if it is not None and it[0] == os.getpid():
            return it[1]
        cls.__it__ = it = (os.getpid(), object.__new__(cls))
        it[1].init(*args, **kwds)
        return it[1]
    def init(self, *args, **kwds):
        pass
    @classmethod
    def _clear_singleton(cls):
        cls.__it__ = None
    @classmethod
    def _switch_instance_after_fork(cls):
        '''after forking, parent's isntance still remains, need to adjust the pid so no extra instance is created'''
        it = cls.__dict__.get("__it__")
        if it is not None:
            cls.__it__ = (os.getpid(), it[1])
    
if sys.platform.startswith("win"):
    get_time = time.clock
else:
    get_time = time.time
    
