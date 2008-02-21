# test_system.py
# unit test that excercises the object manager system
from pysage.messaging import *
from pysage.system import *
import py
import time

gameObjectManager = ObjectManager.getSingleton()

class TakeDamage(Message):
    properties = ['damageAmount']

class Punk(MessageReceiver):
    pass

class RealPunk(Actor):
    subscriptions = ['TakeDamage']
    def __init__(self):
        GameObject.__init__(self)
        self.damage = 0
    def handle_TakeDamage(self, msg):
        self.damage += msg.getProperty('damageAmount')
        return True

class TestGameObject(object):
    def setup_method(self, method):
        pass
        
    def test_createGameObject(self):
        obj = Punk()
        gameObjectManager.registerReceiver(obj)
        assert obj.gid == 0
        obj = Punk()
        gameObjectManager.registerReceiver(obj)
        assert obj.gid == 1
        obj = Punk(1)
        gameObjectManager.registerReceiver(obj)
        assert obj.gid == 1
        
    def test_registerObj(self):
        obj = RealPunk()        
        gameObjectManager.registerObject(obj)
        assert gameObjectManager.getObject(obj.gid) == obj
    
    def test_unregisterObj(self):
        obj = RealPunk()
        gameObjectManager.registerObject(obj)
        assert gameObjectManager.getObject(obj.gid) == obj
        gameObjectManager.unregisterObject(obj)
        assert gameObjectManager.getObject(obj.gid) is None
        
    def test_triggerToObject(self):
        obj = RealPunk()
        gameObjectManager.registerObject(obj)
        msg = TakeDamage(damageAmount = 3)
        assert gameObjectManager.triggerToObject(obj.gid, msg)
        assert obj.damage == 3
        
    def test_queueToObject(self):
        obj1 = RealPunk()
        obj2 = RealPunk()
        gameObjectManager.registerObject(obj1)
        gameObjectManager.registerObject(obj2)
        msg = TakeDamage(damageAmount = 3)
        assert gameObjectManager.queueMessageToObject(obj1.gid, msg)
        assert obj1.damage == 0
        assert obj2.damage == 0
        gameObjectManager.tick(None)
        assert obj1.damage == 3
        assert obj2.damage == 0
                                
    def test_queueMessage(self):
        obj = RealPunk()
        gameObjectManager.registerObject(obj)
        msg = TakeDamage(damageAmount = 2)
        gameObjectManager.queueMessage(msg)
        assert obj.damage == 0
        assert gameObjectManager.tick(None)
        assert obj.damage == 2
        
    def test_registerObjectWithName(self):
        obj = Punk()
        gameObjectManager.registerObject(obj, 'punk')
        assert gameObjectManager.getObjectByName('punk') == obj
        
    def teardown_method(self, method):
        gameObjectManager.reset()
        