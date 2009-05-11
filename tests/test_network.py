# test_network.py
from pysage.system import Message, ActorManager, Actor, WrongMessageTypeSpecified
import time
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

class LongMessage(Message):
    properties = ['data']
    types = ['ai']
    packet_type = 107

class PascalMessage(Message):
    properties = ['data']
    types = ['p']
    packet_type = 108

class LongStringMessage(Message):
    properties = ['data']
    types = ['S']
    packet_type = 111

class BadMessage(Message):
    properties = ['data']
    packet_type = 110
    
class TestReceiver(Actor):
    pass

class PingMessage(Message):
    properties = ['secret']
    types = ['i']
    packet_type = 112

class TestMeMessage(Message):
    properties = ['port']
    types = ['i']
    packet_type = 114
    
class SYNMessage(Message):
    properties = ['port']
    types = ['i']
    packet_type= 115
    
class ACKMessage(Message):
    packet_type= 116

class PongMessage(Message):
    properties = ['secret']
    types = ['i']
    packet_type = 113

class PingReceiver(Actor):
    '''this is the actor that will be spawned in the new process'''
    subscriptions = ['PingMessage', 'TestMeMessage']
    def __init__(self):
        Actor.__init__(self)
        self.success = False
    def handle_PingMessage(self, msg):
        nmanager = ActorManager.get_singleton()
        nmanager.queue_message_to_group(nmanager.PYSAGE_MAIN_GROUP, PongMessage(secret=1234))
        return True
    def handle_TestMeMessage(self, msg):
        nmanager = ActorManager.get_singleton()
        nmanager.connect('localhost', msg.get_property('port'))
        nmanager.send_message(SYNMessage(port=nmanager.transport.address[1]), address=('localhost', msg.get_property('port')))
        return True
    def handle_ACKMessage(self, msg):
        self.success = True

class PongReceiver(Actor):
    subscriptions = ['PongMessage', 'SYNMessage']
    def __init__(self):
        Actor.__init__(self)
        self.received_secret = None
        self.success = False
    def handle_PongMessage(self, msg):
        self.received_secret = msg.get_property('secret')
        return True
    def handle_SYNMessage(self, msg):
        '''this method tests that server is able to receive messages from clients'''
        self.success = True
        return True

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
    def test_long_list(self):
        m = LongMessage(data=[1] * 10000)
        assert len(m.to_string()) == 1 + 4 + 10000 * 4
        assert len('k' + "\x00\x00'\x10" + '\x00\x00\x00\x01' * 10000) == 1 + 4 + 10000 * 4
        assert m.to_string() == 'k' + "\x00\x00'\x10" + '\x00\x00\x00\x01' * 10000
        assert LongMessage().from_string('k' + "\x00\x00'\x10" + '\x00\x00\x00\x01' * 10000).get_property('data') == [1] * 10000
    def test_long_pascal_string(self):
        m = PascalMessage(data='a' * 255)
        assert len(m.to_string()) == 257
        assert m.to_string() == 'l' + '\xff' + '\x61' * 255
        assert m.to_string() == 'l' + '\xff' + 'a' * 255
        m = PascalMessage(data='a' * 256)
        self.assertRaises(ValueError, m.to_string)
    def test_bad_message(self):
        m = BadMessage(data=1)
        self.assertRaises(WrongMessageTypeSpecified, m.to_string)
    def test_long_string_message(self):
        m = LongStringMessage(data='1' * 10000)
        assert len(m.to_string()) == 1 + 4 + 10000
        LongStringMessage().from_string(m.to_string()).get_property('data') == '1' * 10000
    def test_send_network_message(self):
        nmanager.register_actor(PongReceiver(), 'pong_receiver')
        assert not nmanager.find('pong_receiver').received_secret
        nmanager.add_process_group('a', PingReceiver)
        nmanager.queue_message_to_group('a', PingMessage(secret=1234))
        time.sleep(1)
        nmanager.tick()
        assert nmanager.find('pong_receiver').received_secret == 1234

        # the server listens on an auto-gened port on localhost
        nmanager.listen('localhost', 0)

        host, port = nmanager.transport.address

        # the server tells the slave via IPC to test send a message
        nmanager.queue_message_to_group('a', TestMeMessage(port=port))
        
        time.sleep(1)
        nmanager.tick()
        
        assert nmanager.find('pong_receiver').success == True


