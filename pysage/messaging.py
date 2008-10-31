# Messaging.py
# Credits: 
#   this module builds on the concepts of a trigger system introduced in
#   the book: "Game Coding Complete - 2nd Edition" by Mike McShaffry
# this module implements a message manager along with message receivers
import collections
import time
import util

WildCardMessageType = '*'

def MessageID():
    '''generates unique message IDs per runtime'''
    i = 0
    while True:
        yield i
        i += 1
messageID = MessageID()

class InvalidMessageProperty(Exception):
    pass

class MessageReceiver(object):
    '''generic message receiver class that game object inherits from'''
    # message types this message receiver will subscribe to
    subscriptions = []
    def __init__(self):
        # default update priority is 0
        # determines which object is synced first during update
        self._SYNC_PRIORITY = 0       
    def handle_message(self, msg):
        '''handles a message received
            returns: True if a message is consumed
        ''' 
        # see if this mssage receiver implements a handler for this msg
        method = 'handle_' + msg.messageType
        if hasattr(self, method):
            return getattr(self, method)(msg)
        else:
            return False
    def update(self, evt=None):
        pass
    @property
    def gid(self):
        return id(self)
        
class Message(object):
    '''generic message class'''
    properties= []
    _LOG_LEVEL = 0
    def __init__(self, sender=None, receiverID=None, **kws):
        self._properties = dict( (x, None) for x in self.properties )
        for name, value in kws.items():
            self.lazySetProperty(name, value)
        self.sender = sender
        self.gid = messageID.next()
        self.receiverID = receiverID
    def __repr__(self):
        return 'Message %s %s' % (self.messageType, self.gid)
    @property
    def messageType(self):
        return self.__class__.__name__
    def get_sender(self):
        return self.sender
    def lazySetProperty(self, name, value):
        '''this does same as set_property, without validation'''
        self._properties[name] = self.pack_property(name, value)        
    def set_property(self, name, value):
        '''set required property of the message'''
        if name not in self.properties:
            raise InvalidMessageProperty('Invalid Message Property: %s' % name)
        self._properties[name] = self.pack_property(name, value)
    def get_property(self, name, default=None):
        if name not in self.properties:
            raise InvalidMessageProperty('Invalid Message Property: %s' % name)
        if not self._properties[name] is None:
            return self.unpack_property(name, self._properties[name])
        else:
            return default
    def pack_property(self, name, value):
        '''how to store this property for network message'''
        packMethod = 'pack_' + name
        if hasattr(self, packMethod):
            return getattr(self, packMethod)(value)
        else:
            return value
    def unpack_property(self, name, value):
        '''how to unpack the stored message from network'''
        unpackMethod = 'unpack_' + name
        if hasattr(self, unpackMethod):
            return getattr(self, unpackMethod)(value)
        else:
            return value
    def validate(self):
        '''returns true if this message is valid with the given properties
                false otherwise
        '''
        if set(self._properties.keys()) ^ set(self.properties):
            raise InvalidMessageProperty('Message %s received invalid properties: %s' % (self.messageType, list(set(self._properties.keys()) ^ set(self.properties))))
        return True
    def on_receipt(self, *args, **kws):
        '''abstract method to be implemented with application
            defines behavior when the message is received
        '''
        pass
    def __getstate__(self):
        return dict( [(i,v) for i,v in self.__dict__.items() if i in ('gid', 'properties', '_properties', 'receiverID')] )
    def __setstate__(self, d):
        self.__dict__.update(d)

class MessageManager(util.ProcessLocalSingleton):
    '''generic message manager singleton class that game object manager inherits from'''
    def init(self):
        self.messageTypes = []
        # WildCardMessageType is the wild card message type, 
        # all receivers that subscribe to this receive all messages
        # however these type of receivers cannot consume the message
        self.messageReceiverMap = {WildCardMessageType: set()}
        
        # double buffering to avoid infinite cycles
        self.activeQueue = collections.deque()
        self.processingQueue = collections.deque()
    def validateType(self, messageType):
        if not messageType:
            return False
        else:
            return True
    def validateMessage(self, msg):
        return msg.validate()
    def tick(self, maxTime=None):
        '''
        Process queued messages.
        
        :Parameters:
            - `maxTime`: processing time limit so that the event processing does not take too long. 
              not all messages are guranteed to be processed with this limiter

        :Return:
            - true: if all messages ready for processing were completed
            - false: otherwise (i.e.: processing took more than maxTime)
        '''
        # swap queues and clear the activeQueue
        self.activeQueue, self.processingQueue = self.processingQueue, self.activeQueue
        self.activeQueue.clear()
        startTime = time.time()
        while len(self.processingQueue):
            # always pop the message off the queue, if there is no listeners for this message yet
            # then the message will be dropped off the queue
            msg = self.processingQueue.popleft()
            # for receivers that handle all messages let them handle this
            for r in self.messageReceiverMap[WildCardMessageType]:
                r.handle_message(msg)
            # now pass msg to message receivers that subscribed to this message type
            for r in self.messageReceiverMap.get(msg.messageType, []):
                if not self.designated_to_handle(r, msg):
                    continue
                # finish this message if it was handled or had designated receiver
                if r.handle_message(msg) or msg.receiverID:
                    break
            if maxTime and time.time() - startTime > maxTime:
                break
            
        flushed = len(self.processingQueue) == 0
        # push any left over messages to the active queue
        # bottom-up on the processQueue and push to the front of activeQueue
        if not flushed:
            while len(self.processingQueue):
                self.activeQueue.appendleft(self.processingQueue.pop())
        return flushed
    def designated_to_handle(self, r, m):
        '''this method is called before a receiver handles a message
        
           note: this is used to control the optional "designated receiver" behavior using message receiverID
           receivers that pass this function are assumed designated receivers
           
           :Returns:
               - true: if the receiver is designated to handle the message
               - false: otherwise
        '''
        return True
    def abort_message(self, msgType, abortAll=True):
        '''
        Find the next-available instance of the named event type and remove it from the processing queue.
        This may be done up to the point that it is actively being processed ...
        e.g.: is safe to happen during event processing itself.

        return: 

        - 'True': if the event was found and removed
        - 'False': otherwise
        '''
        if not self.validateType(msgType):
            return False
        success = False
        for i in [x for x in self.activeQueue if x.messageType == msgType]:
            # queue.remove(v) only available in python 2.5
            self.activeQueue.remove(i)
            success = True
            if not abortAll:
                return True
        return success
    def queue_message(self, msg):
        '''asychronously queues a message to be processed
        
           :Return: 
               - true: if the message was added to the processing queue
               - false: otherwise.
        '''
        if not self.validateMessage(msg):
            return False
        if not self.validateType(msg.messageType):
            return False
        # Here we need to gracefully handle messages of type that isn't subscribed by any receivers
        if not self.messageReceiverMap.has_key(msg.messageType) and not self.messageReceiverMap[WildCardMessageType]:
            return False
        else:
            self.activeQueue.append(msg)
            return True
    def trigger(self, msg):
        '''
        same as queue_message, except that this is synchronous

        return:

        - 'True': if the event was consumed
        - 'False': otherwise

        it is acceptable for all event listeners to act on an event and not consume it 
        this return signature exists to allow complete propogation of that shred of information 
        from the internals of this system to outside uesrs.
        '''
        if not self.validateType(msg.messageType):
            return False
        # for receivers that register to all events, send the message to them
        map(lambda x: x.handle_message(msg), self.messageReceiverMap[WildCardMessageType])
        # Now loop thru the receivers that actually subscribed to this particular message type
        processed = False
        for r in self.messageReceiverMap.get(msg.messageType, []):
            if r.handle_message(msg):
                processed = True
        return processed
    def addReceiver(self, receiver, msgType):
        '''
        registers the receiver with the message type
        
        :Return: 
            - true: if success
            - false: otherwise
        '''
        if not self.validateType(msgType):
            return False
        # if this is a new type, add to message types and register receiver
        if not msgType in self.messageTypes:
            self.messageTypes.append(msgType)
            self.messageReceiverMap[msgType] = set([receiver])
        # known msg type, just register receiver
        else:
            self.messageReceiverMap[msgType].add(receiver)
        return True
    def removeReceiver(self, receiver, msgType):
        '''un-register the receiver with the message type
        
           :Return:
               - true: if successfully unregistered
               - false: if the pair is not found in registry
        '''
        if not self.validateType(msgType):
            return False
        if not receiver in self.messageReceiverMap[msgType]:
            return False
        else:
            self.messageReceiverMap[msgType].remove(receiver)
            return True
    def registerReceiver(self, receiver):
        for s in receiver.subscriptions:
            self.addReceiver(receiver, s)
    def unregisterReceiver(self, receiver):
        for s in receiver.subscriptions:
            self.removeReceiver(receiver, s)
    def get_message_count(self):
        return len(self.activeQueue)
    def reset(self):
        '''removes all messages, receivers, used for debugging/testing'''
        self.messageTypes = []
        self.messageReceiverMap = {WildCardMessageType: []}
        self.activeQueue = collections.deque()
        self.processingQueue = collections.deque()
          
