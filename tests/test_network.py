# test_network.py
from pysage.system import Message, ActorManager, Actor, WrongMessageTypeSpecified
from pysage import transport
import time
import unittest
from pysage import get_logger

nmanager = ActorManager.get_singleton()
nmanager.enable_groups()

logger = get_logger()

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
    
class SYNACKMessage(Message):
    properties = ['port']
    types = ['i']
    packet_type= 116
    
class ACKMessage(Message):
    packet_type = 117

class PongMessage(Message):
    properties = ['secret']
    types = ['i']
    packet_type = 113

class TestCoord(object):
    def __init__(self, x,y):
        self.x, self.y = x,y

class ComplexMessage(Message):
    properties = ['coordinate', 'speed']
    types = [('i','i'), 'd']
    packet_type = 120
    def pack_coordinate(self, value):
        print value
        return value.x, value.y
    def unpack_coordinate(self, values):
        return TestCoord(values[0], values[1])

class PingReceiver(Actor):
    '''this is the actor that will be spawned in the new process'''
    subscriptions = ['PingMessage', 'TestMeMessage', 'SYNACKMessage']
    def handle_PingMessage(self, msg):
        nmanager = ActorManager.get_singleton()
        nmanager.queue_message_to_group(nmanager.PYSAGE_MAIN_GROUP, PongMessage(secret=1234))
        return True
    def handle_TestMeMessage(self, msg):
        nmanager = ActorManager.get_singleton()
        nmanager.connect(host='127.0.0.1', port=msg.get_property('port'))
        nmanager.send_message(SYNMessage(port=nmanager.transport.address[1]), address=('127.0.0.1', msg.get_property('port')))
        return True
    def handle_SYNACKMessage(self, msg):
        nmanager.send_message(ACKMessage(), address=('127.0.0.1', msg.get_property('port')))
        
class PingReceiverTCP(Actor):
    '''this is the actor that will be spawned in the new process'''
    subscriptions = ['PingMessage', 'TestMeMessage', 'SYNACKMessage']
    def handle_PingMessage(self, msg):
        nmanager = ActorManager.get_singleton()
        nmanager.queue_message_to_group(nmanager.PYSAGE_MAIN_GROUP, PongMessage(secret=1234))
        return True
    def handle_TestMeMessage(self, msg):
        nmanager = ActorManager.get_singleton()
        nmanager.connect(host='127.0.0.1', port=msg.get_property('port'), transport_class=transport.SelectTCPTransport)
        nmanager.send_message(SYNMessage(port=nmanager.transport.address[1]))
        return True
    def handle_SYNACKMessage(self, msg):
        nmanager.send_message(ACKMessage(), address=('127.0.0.1', msg.get_property('port')))
        nmanager.disconnect()

class PongReceiver(Actor):
    subscriptions = ['PongMessage', 'SYNMessage', 'ACKMessage']
    def __init__(self):
        Actor.__init__(self)
        self.received_secret = None
        self.syn_success = False
        self.ack_success = False
        self.sender = None
    def handle_PongMessage(self, msg):
        self.received_secret = msg.get_property('secret')
        return True
    def handle_SYNMessage(self, msg):
        '''this method tests that server is able to receive messages from clients'''
        self.syn_success = True
        self.sender = msg.sender
        return True
    def handle_ACKMessage(self, msg):
        '''handles when client responds with an "ack" message'''
        self.ack_success = True
        self.sender = msg.sender

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
    def test_pack_complex_message(self):
        m = ComplexMessage(coordinate=TestCoord(1,2), speed=10.0)
        assert m._properties['coordinate'].x == 1, m._properties['coordinate'].y == 2
        s = m.to_string()
        nm = ComplexMessage()
        nm.from_string(s)
        coord = nm.get_property('coordinate')
        assert coord.x == 1 and coord.y ==2 and nm.get_property('speed') == 10.0
    def test_bad_message(self):
        m = BadMessage(data=1)
        self.assertRaises(WrongMessageTypeSpecified, m.to_string)
    def test_long_string_message(self):
        m = LongStringMessage(data='1' * 10000)
        assert len(m.to_string()) == 1 + 4 + 10000
        LongStringMessage().from_string(m.to_string()).get_property('data') == '1' * 10000
    def test_send_network_message(self):
        nmanager.register_actor(PongReceiver(), 'pong_receiver')
        
        assert nmanager.find('pong_receiver').syn_success == False
        assert nmanager.find('pong_receiver').ack_success == False
        
        assert not nmanager.find('pong_receiver').received_secret
        nmanager.add_process_group('a', PingReceiver)
        nmanager.queue_message_to_group('a', PingMessage(secret=1234))
        time.sleep(1)
        nmanager.tick()
        assert nmanager.find('pong_receiver').received_secret == 1234

        # the server listens on an auto-gened port on localhost
        nmanager.listen(host='localhost', port=0)

        host, port = nmanager.transport.address

        # the server tells the slave via IPC to test send a message
        nmanager.queue_message_to_group('a', TestMeMessage(port=port))
        
        time.sleep(1)
        nmanager.tick()
        
        # confirms that the server can receive messages via nettwork
        assert nmanager.find('pong_receiver').syn_success == True
        assert nmanager.find('pong_receiver').ack_success == False
        
        # server sends syn-ack
        print 'message sender: ', nmanager.find('pong_receiver').sender
        nmanager.send_message(SYNACKMessage(port=port), nmanager.find('pong_receiver').sender)
        
        time.sleep(1)
        nmanager.tick()
        
        # confirms that the client received the syn-ack message by verifying that the server received "ack"
        assert nmanager.find('pong_receiver').syn_success == True
        assert nmanager.find('pong_receiver').ack_success == True
    def test_send_network_message_tcp(self):
        nmanager.register_actor(PongReceiver(), 'pong_receiver')
        
        assert nmanager.find('pong_receiver').syn_success == False
        assert nmanager.find('pong_receiver').ack_success == False
        
        assert not nmanager.find('pong_receiver').received_secret
        nmanager.add_process_group('a', PingReceiverTCP)
        nmanager.queue_message_to_group('a', PingMessage(secret=1234))
        
        time.sleep(1)
        nmanager.tick()
            
        assert nmanager.find('pong_receiver').received_secret == 1234

        # the server listens on an auto-gened port on localhost
        nmanager.listen(host='127.0.0.1', port=0, transport_class=transport.SelectTCPTransport)

        host, port = nmanager.transport.address
        print 'server bound to %s:%s' % (host, port)

        # the server tells the slave via IPC to test send a message
        nmanager.queue_message_to_group('a', TestMeMessage(port=port))
        
        for i in range(2):
            nmanager.tick()
            time.sleep(.2)
        
        # confirms that the server can receive messages via nettwork
        assert nmanager.find('pong_receiver').syn_success == True
        assert nmanager.find('pong_receiver').ack_success == False
        
        # server sends syn-ack
        print 'message sender: ', nmanager.find('pong_receiver').sender
        nmanager.send_message(SYNACKMessage(port=port), nmanager.find('pong_receiver').sender)
        
        time.sleep(1)
        nmanager.tick()
        
        # confirms that the client received the syn-ack message by verifying that the server received "ack"
        assert nmanager.find('pong_receiver').syn_success == True
        assert nmanager.find('pong_receiver').ack_success == True
    def test_send_network_message_broadcast_tcp(self):
        nmanager.register_actor(PongReceiver(), 'pong_receiver')
        
        assert nmanager.find('pong_receiver').syn_success == False
        assert nmanager.find('pong_receiver').ack_success == False
        
        assert not nmanager.find('pong_receiver').received_secret
        nmanager.add_process_group('a', PingReceiverTCP)
        nmanager.queue_message_to_group('a', PingMessage(secret=1234))
        time.sleep(1)
        nmanager.tick()
        assert nmanager.find('pong_receiver').received_secret == 1234

        # the server listens on an auto-gened port on localhost
        nmanager.listen(host='127.0.0.1', port=0, transport_class=transport.SelectTCPTransport)

        host, port = nmanager.transport.address

        # the server tells the slave via IPC to test send a message
        nmanager.queue_message_to_group('a', TestMeMessage(port=port))
        
        time.sleep(1)
        nmanager.tick()
        
        # confirms that the server can receive messages via nettwork
        assert nmanager.find('pong_receiver').syn_success == True
        assert nmanager.find('pong_receiver').ack_success == False
        
        # server sends syn-ack
        nmanager.broadcast_message(SYNACKMessage(port=port))
        
        time.sleep(1)
        nmanager.tick()
        
        # confirms that the client received the syn-ack message by verifying that the server received "ack"
        assert nmanager.find('pong_receiver').syn_success == True
        assert nmanager.find('pong_receiver').ack_success == True
    def test_send_network_message_broadcast(self):
        nmanager.register_actor(PongReceiver(), 'pong_receiver')
        
        assert nmanager.find('pong_receiver').syn_success == False
        assert nmanager.find('pong_receiver').ack_success == False
        
        assert not nmanager.find('pong_receiver').received_secret
        nmanager.add_process_group('a', PingReceiver)
        nmanager.queue_message_to_group('a', PingMessage(secret=1234))
        time.sleep(1)
        nmanager.tick()
        assert nmanager.find('pong_receiver').received_secret == 1234

        # the server listens on an auto-gened port on localhost
        nmanager.listen(host='localhost', port=0)

        host, port = nmanager.transport.address

        # the server tells the slave via IPC to test send a message
        nmanager.queue_message_to_group('a', TestMeMessage(port=port))
        
        time.sleep(1)
        nmanager.tick()
        
        # confirms that the server can receive messages via nettwork
        assert nmanager.find('pong_receiver').syn_success == True
        assert nmanager.find('pong_receiver').ack_success == False
        
        # server sends syn-ack
        nmanager.broadcast_message(SYNACKMessage(port=port))
        
        time.sleep(1)
        nmanager.tick()
        
        # confirms that the client received the syn-ack message by verifying that the server received "ack"
        assert nmanager.find('pong_receiver').syn_success == True
        assert nmanager.find('pong_receiver').ack_success == True
    def tearDown(self):
        nmanager.clear_process_group()
        nmanager.reset()
        

