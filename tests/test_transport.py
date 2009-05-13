# test_transport.py
from pysage.transport import SelectUDPTransport
import unittest
import time

class handler(object):
    def __init__(self):
        self.received = ''
    def handle(self, packet, address):
        self.received += packet
        return True

class TestTransportModule(unittest.TestCase):
    def test_server_listen_single_client(self):
        h = handler()
        server = SelectUDPTransport()
        client = SelectUDPTransport()
        server.listen('localhost', 0)
        host, port = server.address
        client.connect(host, port)
        client.send('1234')
        time.sleep(.5)
        server.poll(h.handle)
        
        assert h.received == '1234'
        assert server.peers.has_key(client.address)
        
        server.disconnect()
        client.disconnect()
    def test_server_listen_multiple_client(self):
        h = handler()
        server = SelectUDPTransport()
        
        c1 = SelectUDPTransport()
        c2 = SelectUDPTransport()
        
        server.listen('localhost', 0)
        host, port = server.address
        
        c1.connect(host, port)
        c2.connect(host, port)
        
        c1.send('1234')
        c2.send('5678')
        time.sleep(.5)
        has_more = server.poll(h.handle)
        while has_more:
            has_more = server.poll(h.handle)
        
        assert h.received == '12345678'
        
        assert len(server.peers.keys()) == 2
        assert c1.address in server.peers.keys()
        assert c2.address in server.peers.keys()
        
        server.disconnect()
        c1.disconnect()
        c2.disconnect()
    def test_server_broadcast(self):
        h = handler()
        server = SelectUDPTransport()
        
        c1 = SelectUDPTransport()
        c2 = SelectUDPTransport()
        
        server.listen('localhost', 0)
        host, port = server.address
        
        c1.connect(host, port)
        c2.connect(host, port)
        
        c1.send('1234')
        c2.send('5678')
        time.sleep(.5)
        has_more = server.poll(h.handle)
        while has_more:
            has_more = server.poll(h.handle)
            
        server.send('abcd', broadcast=True)    
        
        time.sleep(.5)
        
        h1 = handler()
        h2 = handler()
        c1.poll(h1.handle)
        c2.poll(h2.handle)
        
        
        assert h1.received == 'abcd'
        assert h2.received == 'abcd'
        
        server.disconnect()
        c1.disconnect()
        c2.disconnect()
        
            
        