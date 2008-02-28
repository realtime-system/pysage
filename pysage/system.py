# system.py
from messaging import MessageReceiver, MessageManager, WildCardMessageType, PySageInternalMainGroup

class ObjectManager(MessageManager):
    '''a generic object manager
    '''
    def init(self):
        MessageManager.init(self)
        self.objectIDMap = {}
        self.objectNameMap = {}
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
        '''sends a particular game object a message if that game object implements this message type
            returns True: if event was consumed
                    False: otherwise
        '''
        obj = self.objectIDMap[id]
        for recr in self.messageReceiverMap[WildCardMessageType]:
            recr.handleMessage(msg)
        return obj.handleMessage(msg)
    def queue_message_to_object(self, id, msg):
        msg.receiverID = id
        self.queue_message(msg)
        return True
    def register_object(self, obj, name=None, group=''):
        MessageManager.registerReceiver(self, obj, group)
        self.objectIDMap[obj.gid] = obj
        if name:
            self.objectNameMap[name] = obj
        return obj
    def unregister_object(self, obj):
        MessageManager.unregisterReceiver(self, obj)
        del self.objectIDMap[obj.gid]
        for i,k in self.objectNameMap.items():
            if k == obj:
                del self.objectNameMap[i]
        return self
    def reset(self):
        '''mainly used for testing'''
        MessageManager.reset(self)
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
    def tick(self, evt=None, group=PySageInternalMainGroup, maxTime=None, **kws):
        '''calls update on all objects before message manager ticks'''
        # process all messages first
        ret = MessageManager.tick(self, maxTime=maxTime, group=group, **kws)
        # then update all the game objects
        if group:
            objs = list(self.object_group_map.get(group, set()))
        else:
            objs = self.objectIDMap.values()
        objs.sort(lambda x,y: y._SYNC_PRIORITY - x._SYNC_PRIORITY)
        map(lambda x: x.update(evt), objs)
        return ret



