# test_groups.py
from pysage.messaging import *
from pysage import MessageReceiver, ObjectManager
import time
import nose

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
        self.num_handled = 0
    def update(self, msg):
        if self.switch:
            self.dirty += 1
        return True
    def handle_TestMessage(self, msg):
        self.handled_message = True
        return True
    
class SlowLoader(Loader):
    def update(self, msg):
        for i in range(10):
            omanager.queue_message(TestMessage())
        return True
    def handle_TestMessage(self, msg):
        time.sleep(.2)
        self.handled_message = True
        self.num_handled += 1
        return True

class TestGroups(object):
    def setUp(self):
        omanager.reset()
    def tearDown(self):
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
        nose.tools.assert_raises(GroupAlreadyExists, lambda: omanager.set_groups(['dup','dup']))
    def test_groups_validationexistence(self):
        omanager.set_groups(['group1'])
        nose.tools.assert_raises(GroupDoesNotExist, lambda: omanager.register_object(Loader(), 'loader', 'group2'))
    def test_groups_validationexistence(self):
        nose.tools.assert_raises(InvalidGroupName, lambda: omanager.set_groups(['group1', '']))
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
    def test_message_add_group(self):
        omanager.add_group('workers')
        loader = Loader()
        omanager.register_object(loader, 'loader', 'workers')
        
        assert not loader.handled_message
        omanager.queue_message(TestMessage())
        
        time.sleep(1)
        assert loader.handled_message == True
    def test_message_add_group_maxtime(self):
        # the message takes .2 sec to process, we are giving it .1 sec to process
        # so the handle can process at most 1 per tick, and we tick every 1 sec
        # so as soon as we have something handled, there should only be one handled
        omanager.add_group('workers', max_tick_time = 0.1, interval=1)
        loader = SlowLoader()
        omanager.register_object(loader, 'loader', 'workers')
        
        # wait until the loader processed at least 1 message
        while not loader.handled_message:
            time.sleep(0.01)
            
        time.sleep(.5)
        
        assert loader.num_handled == 1
        
        time.sleep(1)
        
        assert loader.num_handled == 2
        
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
        
        
        
        
                       
