# test_groups_process.py
from pysage.system import *
import time

processing = None

try:
    import multiprocessing as processing
except ImportError:
    pass
else:
    active_children = processing.active_children

try:
    import processing as processing
except ImportError:
    pass
else:
    active_children = processing.activeChildren

if not processing:
    raise Exception('pysage requires either python2.6 or the "processing" module')

import unittest

nmanager = ActorManager.get_singleton()

class PingMessage(Message):
    properties = ['secret']
    types = ['i']
    packet_type = 101
    
class PongMessage(Message):
    properties = ['secret']
    types = ['i']
    packet_type = 102
    
class PingReceiver(Actor):
    subscriptions = ['PingMessage']
    def handle_PingMessage(self, msg):
        nmanager = ActorManager.get_singleton()
        nmanager.queue_message_to_group(nmanager.PYSAGE_MAIN_GROUP, PongMessage(secret=1234))
        return True
    
class PongReceiver(Actor):
    subscriptions = ['PongMessage']
    def __init__(self):
        Actor.__init__(self)
        self.received_secret = None
    def handle_PongMessage(self, msg):
        self.received_secret = msg.get_property('secret')
        return True

class TestGroupsProcess(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        nmanager.clear_process_group()
        nmanager.reset()
    def test_add_group_single(self):
        nmanager.add_process_group('resource_loading')
        assert len(nmanager.groups) == 1
        assert len(active_children()) == 1
    def test_add_group_multi(self):
        nmanager.add_process_group('a', )
        nmanager.add_process_group('b')
        assert len(nmanager.groups) == 2
        assert len(active_children()) == 2
        nmanager.clear_process_group()
        assert len(nmanager.groups) == 0
        assert len(active_children()) == 0
    def test_remove_group_individual(self):
        nmanager.add_process_group('a')
        nmanager.add_process_group('b')

        assert len(nmanager.groups) == 2
        assert len(active_children()) == 2

        nmanager.remove_process_group('a')

        self.assertRaises(GroupDoesNotExist, nmanager.queue_message_to_group, PingMessage(secret=1234), 'a')

        assert len(nmanager.groups) == 1
        assert len(active_children()) == 1
    def test_sending_message(self):
        nmanager.register_actor(PongReceiver(), 'pong_receiver')
        assert not nmanager.find('pong_receiver').received_secret
        nmanager.add_process_group('a', PingReceiver)
        nmanager.queue_message_to_group('a', PingMessage(secret=1234))
        time.sleep(1)
        nmanager.tick()
        assert nmanager.find('pong_receiver').received_secret == 1234
    def test_multi_group_message(self):
        nmanager.register_actor(PongReceiver(), 'pong_receiver')
        assert not nmanager.find('pong_receiver').received_secret

        self.assertRaises(GroupDoesNotExist, nmanager.queue_message_to_group, PingMessage(secret=1234), 'a')

        nmanager.add_process_group('a', PingReceiver)
        self.assertRaises(GroupAlreadyExists, nmanager.add_process_group, 'a', PingReceiver)
        nmanager.add_process_group('b', PingReceiver)
        
        nmanager.queue_message_to_group('a', PingMessage(secret=1234))
        time.sleep(1)
        nmanager.tick()

        assert nmanager.find('pong_receiver').received_secret == 1234
        nmanager.find('pong_receiver').received_secret = None

        nmanager.queue_message_to_group('b', PingMessage(secret=1234))
        time.sleep(1)
        nmanager.tick()
        assert nmanager.find('pong_receiver').received_secret == 1234







        

