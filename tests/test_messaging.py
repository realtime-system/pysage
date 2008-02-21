# test_messaging.py
# unit test that excercises the messaging system
from pysage.messaging import *
import py
import time

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
            messageManager.queueMessage(Test(name='unknown'))
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

class TestMessage(object):
    def setup_method(self, method):
        pass
    
    def test_messageRepr(self):
        msg = Test()
        msg.gid = 1
        assert str(msg) == 'Message Test 1'
        
    def test_createMessage(self):
        msg = Test(name='Test')
        assert msg.messageType == 'Test'
        
    def test_createReceiver(self):
        receiver = Receiver()
        messageManager.registerReceiver(receiver)
        assert 'Test' in messageManager.messageTypes
        assert messageManager.messageReceiverMap['Test'] == [receiver]
        
    def test_triggerMessage(self):
        receiver = Receiver()
        messageManager.registerReceiver(receiver)
        msg = Test(name='Test')
        # make sure that the receiver isn't consuming the msg, therefore the trigger will return
        # saying that the message wasn't consumed
        assert not messageManager.trigger(msg)
        
    def test_queueMessage(self):
        receiver = Receiver()
        messageManager.registerReceiver(receiver)
        msg = Test(name='Test')
        messageManager.queueMessage(msg)
        assert len(messageManager.activeQueue) == 1
        assert len(messageManager.processingQueue) == 0
        assert messageManager.tick()
        assert len(messageManager.activeQueue) == 0
        assert len(messageManager.processingQueue) == 0
        
    def test_abortMessage(self):
        receiver = Receiver()
        messageManager.registerReceiver(receiver)
        msg = Test(name='Test')
        messageManager.queueMessage(msg)
        assert len(messageManager.activeQueue) == 1
        assert len(messageManager.processingQueue) == 0
        assert messageManager.abortMessage('Test')
        assert len(messageManager.activeQueue) == 0
        assert len(messageManager.processingQueue) == 0
        
    def test_twoMessages(self):
        receiver = Receiver()
        messageManager.registerReceiver(receiver)
        msg = Test(name='Test')
        messageManager.queueMessage(msg)
        msg2 = Message()
        messageManager.queueMessage(msg2)
        assert not 'Message' in messageManager.messageTypes and 'Test' in messageManager.messageTypes
        assert len(messageManager.activeQueue) == 1
        assert len(messageManager.processingQueue) == 0
        # unhandled messages will be dropped
        assert messageManager.tick()
        assert len(messageManager.activeQueue) == 0
        assert len(messageManager.processingQueue) == 0
        
    def test_slowReceiver(self):
        receiver1 = Receiver()
        receiver2 = SlowReceiver()
        messageManager.registerReceiver(receiver1)
        messageManager.registerReceiver(receiver2)
        msg1 = Test(name='Good')
        msg2 = Test(name='Day')
        messageManager.queueMessage(msg1)
        messageManager.queueMessage(msg2)
        
        assert len(messageManager.activeQueue) == 2
        messageManager.tick(.001)
        assert len(messageManager.activeQueue) == 1
        messageManager.tick(.001)
        assert len(messageManager.activeQueue) == 0
        
    def test_manyMessages(self):
        receiver = ManyMsgReceiver()
        messageManager.registerReceiver(receiver)
        for i in range(5000):
            msg = Test(name='Bla')
            messageManager.queueMessage(msg)
        assert len(messageManager.activeQueue) == 5000
        messageManager.tick()
        assert len(messageManager.activeQueue) == 0
        assert receiver.counter == 5000
        
    def test_receiverProducesMsg(self):
        receiver = MsgProducer()
        messageManager.registerReceiver(receiver)
        messageManager.queueMessage(Test(name='bla'))
        assert len(messageManager.activeQueue) == 1
        messageManager.tick()
        assert len(messageManager.activeQueue) == 2
        messageManager.tick()
        assert len(messageManager.activeQueue) == 4
        
    def test_unregisteredReceiver(self):
        receiver = ManyMsgReceiver()
        messageManager.registerReceiver(receiver)
        for i in range(5000):
            msg = Test(name='bla')
            messageManager.queueMessage(msg)
        messageManager.unregisterReceiver(receiver)
        messageManager.tick()
        assert receiver.counter == 0
        
    def test_propertyRetrieveEarly(self):
        msg = Test()
        assert msg.getProperty('name') == None
        
    def test_propertyDefault(self):
        msg = Test()
        assert msg.getProperty('name', 'bob') == 'bob'
        
    def test_lateErrorChecking(self):
        msg = Test(bad='bad', verybad='bad')
        assert msg
        
    def test_unknownProperty(self):
        msg = Test(bad='bad')
        py.test.raises(InvalidMessageProperty, lambda: messageManager.queueMessage(msg))
        
    def test_propertyGetSet(self):
        msg = Test()
        msg.setProperty('name', 'robin')
        assert msg.getProperty('name') == 'robin'
        
    def test_packing(self):
        msg = MessageToPack(secret='secret')
        assert msg._properties['secret'] == 's'
    
    def test_unpacking(self):
        msg = MessageToPack(secret='secret')
        assert msg._properties['secret'] == 's'
        assert msg.getProperty('secret') == 'secret'
        
    def test_zeroMessageProperty(self):
        msg = Test(name=0)
        assert msg.getProperty('name') == 0
    
    def test_setNonePropertyDefault(self):
        msg = Test(name=None)
        assert msg.getProperty('name', 2) == 2
        
    def teardown_method(self, method):
        messageManager.reset()
        
        