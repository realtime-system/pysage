# test_groups.py
from pysage.messaging import *
from pysage import MessageReceiver, ObjectManager
import py
import time

omanager = ObjectManager.get_singleton()

class TestMessage(Message):
    pass

class Loader(MessageReceiver):
    subscriptions = ['TestMessage']
    def __init__(self):
        MessageReceiver.__init__(self)
        self.dirty = 0
        self.switch = True
        self.handled_message = False
    def update(self, msg):
        if self.switch:
            self.dirty += 1
        return True
    def handle_TestMessage(self, msg):
        self.handled_message = True
        return True

class TestGroups(object):
    def setup_method(self, method):
        omanager.reset()
    def teardown_method(self, method):
        pass
    def test_setgroups(self):
        omanager.set_groups(['resource_loading'])
        omanager.reset()
    def test_isolation_maingroup(self):
        omanager.set_groups(['resource_loading'])
        # put loader in default group
        loader = omanager.register_object(Loader(), 'loader')
        
        time.sleep(1)
        assert not loader.dirty
        
        omanager.tick()
        
        assert loader.dirty
    def test_isolation_subgroup(self):
        omanager.set_groups(['resource_loading'])
        # put loader in default group
        loader = Loader()
        loader.switch = False
        omanager.register_object(loader, 'loader', 'resource_loading')
        
        time.sleep(1)
        assert not loader.dirty
        omanager.tick()
        assert not loader.dirty
        loader.switch = True
        time.sleep(1)
        assert loader.dirty
    def test_groups_validationdup(self):
        py.test.raises(GroupAlreadyExists, lambda: omanager.set_groups(['dup','dup']))
    def test_groups_validationexistence(self):
        omanager.set_groups(['group1'])
        py.test.raises(GroupDoesNotExist, lambda: omanager.register_object(Loader(), 'loader', 'group2'))
    def test_groups_validationexistence(self):
        py.test.raises(InvalidGroupName, lambda: omanager.set_groups(['group1', '']))
    def test_unregister_frommain(self):
        omanager.set_groups(['resource_loading'])
        # put loader in default group
        loader = omanager.register_object(Loader(), 'loader')
        
        omanager.unregister_object(loader)
        
        time.sleep(1)
        assert not loader.dirty
        
        omanager.tick()
        
        assert not loader.dirty
    def test_unregister_fromgroup(self):
        omanager.set_groups(['resource_loading'])
        # put loader in default group
        loader = Loader()
        loader.switch = False
        omanager.register_object(loader, 'loader', 'resource_loading')
        
        omanager.unregister_object(loader)
        loader.switch = True
        
        time.sleep(1)
        assert not loader.dirty
        
        omanager.tick()
        
        assert not loader.dirty
    def test_message_queuing_main(self):
        omanager.set_groups(['workers'])
        loader = Loader()
        omanager.register_object(loader, 'loader')
        
        omanager.queue_message(TestMessage())
        assert not loader.handled_message
        omanager.tick()
        
        assert loader.handled_message
    def test_message_queuing_subgroup(self):
        omanager.set_groups(['workers'])
        loader = Loader()
        omanager.register_object(loader, 'loader', 'workers')
        
        assert not loader.handled_message
        omanager.queue_message(TestMessage())
        
        time.sleep(1)
        assert loader.handled_message == True
    def test_multigroup(self):
        omanager.set_groups(['workers_a', 'workers_b'])
        loader = Loader()
        omanager.register_object(loader, 'loader', 'workers_a')
        
        assert not loader.handled_message
        for i in range(100):
            omanager.queue_message(TestMessage())
        
        time.sleep(1)
        assert omanager.get_message_count('workers_a') == 0
        assert omanager.get_message_count() == 100
        assert loader.handled_message == True
        
        omanager.tick()
        assert omanager.get_message_count('workers_a') == 0
        assert omanager.get_message_count() == 0
        assert loader.handled_message == True
        
    def test_no_listeners(self):
        omanager.set_groups(['workers_a'])
        loader = Loader()
        omanager.register_object(loader, 'loader')
        
        omanager.queue_message(TestMessage())
        
        time.sleep(1)
        
        
        
        
                       
