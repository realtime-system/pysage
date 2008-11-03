# test_network.py
from pysage.system import Message, ActorManager, Actor
import unittest

nmanager = ActorManager.get_singleton()

class TestMessage1(Message):
    properties = ['amount']
    types = ['i']
    packet_type = 103
    
class TestMessage2(Message):
    properties = ['size']
    types = [('i', 'i')]
    packet_type = 106
    
class TestReceiver(Actor):
    pass

class TestNetwork(unittest.TestCase):
    def test_packet_creation(self):
        p = TestMessage1(amount=1)
    def test_packing(self):
        p = TestMessage1(amount=1)
        assert p.to_string() == 'g\x00\x00\x00\x01'
    def test_manager_gid(self):
        assert nmanager.gid == 0
    def test_receiver_gid(self):
        r = TestReceiver()
        assert r.gid == (nmanager.gid, id(r))
    def test_packing_tuple(self):
        m = TestMessage2(size=(1,1))
        assert len(m.to_string()) == 9
        assert m.to_string() == 'j\x00\x00\x00\x01\x00\x00\x00\x01'
        
        print TestMessage2().from_string('j\x00\x00\x00\x01\x00\x00\x00\x01').get_property('size')
        assert TestMessage2().from_string('j\x00\x00\x00\x01\x00\x00\x00\x01').get_property('size') == [1,1]

