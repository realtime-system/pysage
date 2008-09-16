# server.py
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pysage.network import *

nmanager = NetworkManager.get_singleton()

nmanager.start_server(8000)

class TestMessage(Packet):
    properties = ['secret']
    types = ['p']
    packet_type = 101
    
class TestMessageReceiver(PacketReceiver):
    subscriptions = ['TestMessage']
    def handle_TestMessage(self, msg):
        print 'Got "%s"' % msg.get_property('secret')
        return True
    
nmanager.register_object(TestMessageReceiver())

while True:
    time.sleep(.33)
    nmanager.tick()

