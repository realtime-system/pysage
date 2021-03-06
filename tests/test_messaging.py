# test_messaging.py
# unit test that excercises the messaging system
from pysage.messaging import *
from pysage.messaging import MessageReceiver, Message, MessageManager
import time
import unittest

messageManager = MessageManager()

class Test(Message):
    properties = ['name']
    pass

class Receiver(MessageReceiver):
    subscriptions = ['Test']
    def handle_Test(self, msg):
        # don't consume this message
        return False
        
class SlowReceiver(MessageReceiver):
    subscriptions = ['Test']
    def handle_Test(self, msg):
       time.sleep(.1)
       # don't consume message
       return False
   
class MsgProducer(MessageReceiver):
    subscriptions = ['Test']
    def handle_Test(self, msg):
        for i in range(2):
            messageManager.queue_message(Test(name='unknown'))
        return False
    
class MessageToPack(Message):
    properties = ['secret']
    def pack_secret(self, value):
        return value[0]
    def unpack_secret(self, value):
        return value + 'ecret'
   
class ManyMsgReceiver(MessageReceiver):
    subscriptions = ['Test']
    def __init__(self):
        self.counter = 0
    def handle_Test(self, msg):
        self.counter += 1
        return False

class TestMessage(unittest.TestCase):
    def test_messageRepr(self):
        msg = Test()
        msg.gid = 1
        assert str(msg) == 'Message Test 1'
        
    def test_createMessage(self):
        msg = Test(name='Test')
        assert msg.message_type == 'Test'
        
    def test_createReceiver(self):
        receiver = Receiver()
        messageManager.register_receiver(receiver)
        assert 'Test' in messageManager.message_types
        print messageManager.message_receiver_map['Test']
        assert messageManager.message_receiver_map['Test'] == set([receiver])
        
    def test_triggerMessage(self):
        receiver = Receiver()
        messageManager.register_receiver(receiver)
        msg = Test(name='Test')
        # make sure that the receiver isn't consuming the msg, therefore the trigger will return
        # saying that the message wasn't consumed
        assert not messageManager.trigger(msg)
        
    def test_queue_message(self):
        receiver = Receiver()
        messageManager.register_receiver(receiver)
        msg = Test(name='Test')
        messageManager.queue_message(msg)
        assert messageManager.get_message_count() == 1
        assert messageManager.tick()
        assert messageManager.get_message_count() == 0
        
    def test_abort_message(self):
        receiver = Receiver()
        messageManager.register_receiver(receiver)
        msg = Test(name='Test')
        messageManager.queue_message(msg)
        assert messageManager.get_message_count() == 1
        assert messageManager.abort_message('Test')
        assert messageManager.get_message_count() == 0
        
    def test_twoMessages(self):
        receiver = Receiver()
        messageManager.register_receiver(receiver)
        msg = Test(name='Test')
        messageManager.queue_message(msg)
        msg2 = Message()
        messageManager.queue_message(msg2)
        assert not 'Message' in messageManager.message_types and 'Test' in messageManager.message_types
        assert messageManager.get_message_count() == 2
        # unhandled messages will be dropped
        assert messageManager.tick()
        assert messageManager.get_message_count() == 0
        
    def test_slowReceiver(self):
        receiver1 = Receiver()
        receiver2 = SlowReceiver()
        messageManager.register_receiver(receiver1)
        messageManager.register_receiver(receiver2)
        msg1 = Test(name='Good')
        msg2 = Test(name='Day')
        messageManager.queue_message(msg1)
        messageManager.queue_message(msg2)
        
        assert messageManager.get_message_count() == 2
        messageManager.tick(.001)
        assert messageManager.get_message_count() == 1
        messageManager.tick(.001)
        assert messageManager.get_message_count() == 0
        
    def test_manyMessages(self):
        receiver = ManyMsgReceiver()
        messageManager.register_receiver(receiver)
        for i in range(5000):
            msg = Test(name='Bla')
            messageManager.queue_message(msg)
        assert messageManager.get_message_count() == 5000
        messageManager.tick()
        assert messageManager.get_message_count() == 0
        assert receiver.counter == 5000
        
    def test_receiverProducesMsg(self):
        receiver = MsgProducer()
        messageManager.register_receiver(receiver)
        messageManager.queue_message(Test(name='bla'))
        assert messageManager.get_message_count() == 1
        messageManager.tick()
        assert messageManager.get_message_count() == 2
        messageManager.tick()
        assert messageManager.get_message_count() == 4
        
    def test_unregisteredReceiver(self):
        receiver = ManyMsgReceiver()
        messageManager.register_receiver(receiver)
        for i in range(5000):
            msg = Test(name='bla')
            messageManager.queue_message(msg)
        messageManager.unregister_receiver(receiver)
        messageManager.tick()
        assert receiver.counter == 0
        
    def test_propertyRetrieveEarly(self):
        msg = Test()
        assert msg.get_property('name') == None
        
    def test_propertyDefault(self):
        msg = Test()
        assert msg.get_property('name', 'bob') == 'bob'
        
    def test_lateErrorChecking(self):
        msg = Test(bad='bad', verybad='bad')
        assert msg
        
    def test_unknownProperty(self):
        msg = Test(bad='bad')
        self.assertRaises(InvalidMessageProperty, lambda: messageManager.queue_message(msg))
        
    def test_propertyGetSet(self):
        msg = Test()
        msg.set_property('name', 'robin')
        assert msg.get_property('name') == 'robin'
        
    # def test_packing(self):
    #     msg = MessageToPack(secret='secret')
    #     assert msg._properties['secret'] == 's'
    # 
    # def test_unpacking(self):
    #     msg = MessageToPack(secret='secret')
    #     assert msg._properties['secret'] == 's'
    #     assert msg.get_property('secret') == 'secret'
        
    def test_zeroMessageProperty(self):
        msg = Test(name=0)
        assert msg.get_property('name') == 0
    
    def test_setNonePropertyDefault(self):
        msg = Test(name=None)
        assert msg.get_property('name', 2) == 2
        
    def tearDown(self):
        messageManager.reset()
        
        
