# test_network.py
from pysage.network import Packet, NetworkManager
import unittest

nmanager = NetworkManager.get_singleton()

class TestMessage(Packet):
    properties = ['amount']
    types = ['i']
    packet_type = 100

class TestNetwork(unittest.TestCase):
    def test_packet_creation(self):
        p = TestMessage(amount=1)
    def test_packing(self):
        p = TestMessage(amount=1)
        assert p.to_string() == 'd\x00\x00\x00\x01'
    def test_manager_gid(self):
        assert nmanager.gid == 0




