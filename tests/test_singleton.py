# test_singleton.py
from pysage.util import *
import unittest
import time

processing = None

try:
    import multiprocessing as processing
except ImportError:
    pass

try:
    import processing as processing
except ImportError:
    pass

if not processing:
    raise Exception('pysage requires either python2.6 or the "processing" module')

class TestProcessSingleton(ProcessLocalSingleton):
    pass

def return_instance_id():
    return id(TestProcessSingleton.get_singleton())

def proc_change_id(q):
    q.put(id(TestProcessSingleton.get_singleton()))

class TestSingleton(unittest.TestCase):
    def tearDown(self):
        TestProcessSingleton._clear_singleton()
    def test_same_thread(self):
        return return_instance_id() == return_instance_id()
    def test_singleton_process(self):
        '''tests that all processes have their own manager, --> unnecessary'''
        queue = processing.Queue()
        assert queue.empty()
        
        p = processing.Process(target=proc_change_id, args=(queue,))
        p.start()
        p.join()
        
        assert not queue.empty()
        assert not queue.get() == id(TestProcessSingleton.get_singleton())
    def test_singleton_process_before_fork(self):
        '''tests that all processes have their own manager, --> unnecessary'''
        s = TestProcessSingleton.get_singleton()
        queue = processing.Queue()
        assert queue.empty()
        
        p = processing.Process(target=proc_change_id, args=(queue,))
        p.start()
        p.join()
        
        assert not queue.empty()
        assert not queue.get() == id(TestProcessSingleton.get_singleton())
        
        
        
