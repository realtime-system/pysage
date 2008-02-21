# system.py
from messaging import MessageReceiver, MessageManager, WildCardMessageType

class ObjectManager(MessageManager):
    '''a generic object manager
    '''
    def init(self):
        MessageManager.init(self)
        self.objectIDMap = {}
        self.objectNameMap = {}
    def find(self, name):
        return self.getObjectByName(name)
    def getObject(self, id):
        return self.objectIDMap.get(id, None)
    def getObjectByName(self, name):
        return self.objectNameMap.get(name, None)
    @property
    def objects(self):
        return self.objectIDMap.values()
    def triggerToObject(self, id, msg):
        '''sends a particular game object a message if that game object implements this message type
            returns True: if event was consumed
                    False: otherwise
        '''
        obj = self.objectIDMap[id]
        for recr in self.messageReceiverMap[WildCardMessageType]:
            recr.handleMessage(msg)
        return obj.handleMessage(msg)
    def queueMessageToObject(self, id, msg):
        msg.receiverID = id
        self.queueMessage(msg)
        return True
    def registerObject(self, obj, name=None):
        MessageManager.registerReceiver(self, obj)
        self.objectIDMap[obj.gid] = obj
        if name:
            self.objectNameMap[name] = obj
    def unregisterObject(self, obj):
        MessageManager.unregisterReceiver(self, obj)
        del self.objectIDMap[obj.gid]
        for i,k in self.objectNameMap.items():
            if k == obj:
                del self.objectNameMap[i]
    def reset(self):
        '''mainly used for testing'''
        MessageManager.reset(self)
        self.objectIDMap = {}
        self.objectNameMap = {}
    def designatedToHandle(self, r, m):
        '''handles designated messages'''
        if m.receiverID:
            if m.receiverID == r.gid:
                return True
            else:
                return False
        else:
            return True
    def tick(self, evt=None, **kws):
        '''calls update on all objects before message manager ticks'''
        # process all messages first
        ret = MessageManager.tick(self, **kws)
        # then update all the game objects
        objs = self.objectIDMap.values()
        objs.sort(lambda x,y: y._SYNC_PRIORITY - x._SYNC_PRIORITY)
        map(lambda x: x.update(evt), objs)
        return ret
