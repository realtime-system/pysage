# client.py
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pysage.network import *

class TestMessage(Packet):
    properties = ['secret']
    types = ['p']
    packet_type = 101

nmanager = NetworkManager.get_singleton()

nmanager.connect('localhost', 8000)


while True:
    time.sleep(.33)
    nmanager.tick()
    nmanager.broadcast_message(TestMessage(secret='bla'))
