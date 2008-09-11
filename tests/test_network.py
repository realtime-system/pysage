# test_network.py
from pysage.network import Packet, NetworkManager, PacketReceiver
import unittest

nmanager = NetworkManager.get_singleton()

class TestMessage(Packet):
    properties = ['amount']
    types = ['i']
    packet_type = 101
    
class TestReceiver(PacketReceiver):
    pass

class TestNetwork(unittest.TestCase):
    def test_packet_creation(self):
        p = TestMessage(amount=1)
    def test_packing(self):
        p = TestMessage(amount=1)
        print p.to_string()
        assert p.to_string() == 'e\x00\x00\x00\x01'
    def test_manager_gid(self):
        assert nmanager.gid == 0
    def test_receiver_gid(self):
        r = TestReceiver()
        assert r.gid == (nmanager.gid, id(r))




