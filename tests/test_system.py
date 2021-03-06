# test_system.py
# unit test that excercises the object manager system
from pysage import Actor, ActorManager, Message
from pysage.system import ConcreteMessageAlreadyDefined, PacketTypeError
import time
import unittest

mgr = ActorManager.get_singleton()

class TakeDamage(Message):
    properties = ['damageAmount']
    packet_type = 104

class Punk(Actor):
    pass

class RealPunk(Actor):
    subscriptions = ['TakeDamage']
    def __init__(self):
        Actor.__init__(self)
        self.damage = 0
    def handle_TakeDamage(self, msg):
        self.damage += msg.get_property('damageAmount')
        return True
    
class DumbPunk(Actor):
    subscriptions = ['BombMessage']
    def __init__(self):
        Actor.__init__(self)
        self.alive = True
    def handle_BombMessage(self, msg):
        self.alive = False
        return True

class TestGameObject(unittest.TestCase):
    def setUp(self):
        mgr.clear_process_group()
        mgr.reset()
        mgr.enable_groups()
    def tearDown(self):
        mgr.clear_process_group()
        mgr.reset()
    def test_packet_type_error_dup_type(self):
        def register_error_type():
            class TakeDamageFake(Message):
                properties = ['stuff']
                packet_type = 104
        self.assertRaises(PacketTypeError, register_error_type)
    def test_packet_type_error_same_twice(self):
        def register_error_type():
            class TakeDamage(Message):
                properties = ['stuff']
                packet_type = 104
        register_error_type()
    def test_adhoc_message(self):
        obj = DumbPunk()
        assert obj.alive
        mgr.register_actor(obj)
        mgr.trigger_to_actor(obj.gid, 'BombMessage')
        assert not obj.alive
    def test_adhoc_message_with_concrete(self):
        obj = RealPunk()
        mgr.register_actor(obj)
        self.assertRaises(ConcreteMessageAlreadyDefined, mgr.trigger_to_actor, obj.gid, 'TakeDamage')
    def test_createGameObject(self):
        obj = Punk()
        mgr.register_receiver(obj)
        assert obj.gid == (mgr.gid, id(obj))
        obj = Punk()
        mgr.register_receiver(obj)
        assert obj.gid == (mgr.gid, id(obj))
    def test_registerObj(self):
        obj = RealPunk()        
        mgr.register_actor(obj)
        assert mgr.get_actor(obj.gid) == obj
    
    def test_unregisterObj(self):
        obj = RealPunk()
        mgr.register_actor(obj)
        assert mgr.get_actor(obj.gid) == obj
        mgr.unregister_actor(obj)
        assert mgr.get_actor(obj.gid) is None
        
    def test_trigger_to_object(self):
        obj = RealPunk()
        mgr.register_actor(obj)
        msg = TakeDamage(damageAmount = 3)
        assert mgr.trigger_to_actor(obj.gid, msg)
        assert obj.damage == 3
        
    def test_queueToObject(self):
        obj1 = RealPunk()
        obj2 = RealPunk()
        mgr.register_actor(obj1)
        mgr.register_actor(obj2)
        msg = TakeDamage(damageAmount = 3)
        assert mgr.queue_message_to_actor(obj1.gid, msg)
        assert obj1.damage == 0
        assert obj2.damage == 0
        mgr.tick(None)
        assert obj1.damage == 3
        assert obj2.damage == 0
                                
    def test_queue_message(self):
        obj = RealPunk()
        mgr.register_actor(obj)
        msg = TakeDamage(damageAmount = 2)
        mgr.queue_message(msg)
        assert obj.damage == 0
        assert mgr.tick(None)
        assert obj.damage == 2
        
    def test_register_actorWithName(self):
        obj = Punk()
        mgr.register_actor(obj, 'punk')
        assert mgr.get_actor_by_name('punk') == obj
        
    def tearDown(self):
        mgr.reset()
        
