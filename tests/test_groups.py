# test_groups.py
from pysage.messaging import *
from pysage import MessageReceiver, ObjectManager
import py
import time

omanager = ObjectManager.get_singleton()

class Loader(MessageReceiver):
    def __init__(self):
        MessageReceiver.__init__(self)
        self.dirty = 0
    def update(self, msg):
        self.dirty += 1
        return True

class TestGroups(object):
    def setup_method(self, method):
        pass
    def teardown_method(self, method):
        omanager.reset()
    def test_setgroups(self):
        omanager.set_groups(['resource_loading'])
        omanager.reset()
    def test_isolation_maingroup(self):
        omanager.set_groups(['resource_loading'])
        # put loader in default group
        loader = omanager.register_object(Loader(), 'loader')
        
        assert not loader.dirty
        
        omanager.tick()
        
        assert loader.dirty
    def test_isolation_subgroup(self):
        omanager.set_groups(['resource_loading'])
        # put loader in default group
        loader = omanager.register_object(Loader(), 'loader', 'resource_loading')
        
        time.sleep(1)
        assert loader.dirty
        omanager.tick()
        assert loader.dirty
    def test_groups_validationdup(self):
        py.test.raises(GroupAlreadyExists, lambda: omanager.set_groups(['dup','dup']))
    def test_groups_validationexistence(self):
        omanager.set_groups(['group1'])
        py.test.raises(GroupDoesNotExist, lambda: omanager.register_object(Loader(), 'loader', 'group2'))
    def test_groups_validationexistence(self):
        py.test.raises(InvalidGroupName, lambda: omanager.set_groups(['group1', '']))
                       
