# system.py
from __future__ import with_statement
import threading
import messaging

# use this lock because (un)registering requires manipulating a list that's stored
# in a dictionary, concurrent manipulation by multiple threads is unsafe
# could result in loss of registration, etc...
# this lock could in the future be developed to cover a tight part of the section that requires
# mutual exclusion, righ tnow it's a decorator on the entire method
def subscription_lock(func):
    '''decorator that wraps a lock around a member method'''
    def deco(self, *args, **kws):
        with self._subscription_lock:
            return func(self, *args, **kws)
    return deco

MessageReceiver = messaging.MessageReceiver

class Message(messaging.Message):
    def assign_id(self):
        '''return a globally unique id that is good cross processes'''
        return ObjectManager.get_singleton().gid + ':' +  messaging.Message.assign_id(self)

class ObjectManager(messaging.MessageManager):
    '''a generic object manager
    '''
    def init(self):
        messaging.MessageManager.init(self)
        self.objectIDMap = {}
        self.objectNameMap = {}
        self._subscription_lock = threading.RLock()
        self.gid = '0'
    def find(self, name):
        '''returns an object by its name, None if not found'''
        return self.get_object_by_name(name)
    def get_object(self, id):
        return self.objectIDMap.get(id, None)
    def get_object_by_name(self, name):
        return self.objectNameMap.get(name, None)
    @property
    def objects(self):
        return self.objectIDMap.values()
    def trigger_to_object(self, id, msg):
        '''
        sends a particular game object a message if that game object implements this message type
        
        return:
        
        - `True`: if event was consumed
        - `False`: otherwise
        '''
        obj = self.objectIDMap[id]
        for recr in self.messageReceiverMap[messaging.WildCardMessageType]:
            recr.handleMessage(msg)
        return obj.handleMessage(msg)
    def queue_message_to_object(self, id, msg):
        msg.receiverID = id
        self.queue_message(msg)
        return True
    @subscription_lock
    def register_object(self, obj, name=None, group=''):
        messaging.MessageManager.registerReceiver(self, obj, group)
        self.objectIDMap[obj.gid] = obj
        if name:
            self.objectNameMap[name] = obj
        return obj
    @subscription_lock
    def unregister_object(self, obj):
        messaging.MessageManager.unregisterReceiver(self, obj)
        del self.objectIDMap[obj.gid]
        
        # deleting the object from the dictionary the safe way
        n = None
        for name,o in self.objectNameMap.items():
            if o == obj:
                n = name
                break
        if not n == None:
            del self.objectNameMap[n]
                
        return self
    def reset(self):
        '''mainly used for testing'''
        messaging.MessageManager.reset(self)
        self.objectIDMap = {}
        self.objectNameMap = {}
    def designated_to_handle(self, r, m):
        '''handles designated messages'''
        if m.receiverID:
            if m.receiverID == r.gid:
                return True
            else:
                return False
        else:
            return False
    def tick(self, evt=None, group=messaging.PySageInternalMainGroup, maxTime=None, **kws):
        '''calls update on all objects before message manager ticks'''
        # process all messages first
        ret = messaging.MessageManager.tick(self, maxTime=maxTime, group=group, **kws)
        # then update all the game objects
        if group:
            objs = list(self.object_group_map.get(group, set()))
        else:
            objs = self.objectIDMap.values()
        objs.sort(lambda x,y: y._SYNC_PRIORITY - x._SYNC_PRIORITY)
        map(lambda x: x.update(evt), objs)
        return ret



