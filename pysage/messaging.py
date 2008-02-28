# Messaging.py
# Credits: 
#   this module largely builds on the concepts of a trigger system introduced in
#   the book: "Game Coding Complete - 2nd Edition" by Mike McShaffry
# this module implements a message manager along with message receivers
from collections import deque
import util
import threading
import time
import collections

WildCardMessageType = '*'
PySageInternalMainGroup = '__MAIN_GROUP__'

def MessageID():
    '''generates unique message IDs per runtime'''
    i = 0
    while True:
        yield i
        i += 1
messageID = MessageID()

class InvalidMessageProperty(Exception):
    pass

class GroupAlreadyExists(Exception):
    pass

class GroupDoesNotExist(Exception):
    pass

class InvalidGroupName(Exception):
    pass

class MessageReceiver(object):
    '''generic message receiver class that game object inherits from'''
    # message types this message receiver will subscribe to
    subscriptions = []
    def __init__(self):
        # default update priority is 0
        # determines which object is synced first during update
        self._SYNC_PRIORITY = 0       
    def handleMessage(self, msg):
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

class MessageManager(util.Singleton):
    '''generic message manager singleton class that game object manager inherits from'''
    def init(self):
        self.messageTypes = []
        # WildCardMessageType is the wild card message type, 
        # all receivers that subscribe to this receive all messages
        # however these type of receivers cannot consume the message
        self.messageReceiverMap = {WildCardMessageType: set()}
        # double buffering to avoid infinite cycles
        self.activeQueue = deque()
        self.processingQueue = deque()
        
        # for groups handling
        self.groups = {}
        self.object_group_map = collections.defaultdict(set)
        self.object_group_map[PySageInternalMainGroup] = set()
        self._should_quit = False
    def set_groups(self, gs):
        '''starts the groups in thread objects and let them run their tick as fast as possible'''
        for g in gs:
            # make sure we have a str
            g = str(g)
            if self.groups.has_key(g):
                raise GroupAlreadyExists('Group name "%s" already exists.' % g)
            # empty string is invalid
            if not g:
                raise InvalidGroupName('Group name "%s" is invalid.' % g)
            
            def _run(manager, group, interval):
                '''interval is in milliseconds of how long to sleep before another tick'''
                while not manager._should_quit:
                    start = time.time()
                    manager.tick(group=group)
                    delta = time.time() - start
                    
                    if delta < interval:
                        time.sleep((interval - delta) / 1000.0)
                return False
                        
            self.groups[g] = threading.Thread(target=_run, name=g, kwargs={'manager':self, 'group':g, 'interval':30})
            self.groups[g].start()
            
        # returning myself
        return self
    def validateType(self, messageType):
        if not messageType:
            return False
        else:
            return True
    def validateMessage(self, msg):
        return msg.validate()
    def tick(self, maxTime=None, group=PySageInternalMainGroup):
        '''Process queued messages.
            maxTime: processing time limit so that the event processing does not take too long. 
                     not all messages are guranteed to be processed with this limiter
            return: true if all messages ready for processing were completed
                    false otherwise (i.e.: time out specified by the limiter)
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
                r.handleMessage(msg)
            # now pass msg to message receivers that subscribed to this message type
            if not group in self.object_group_map:
                raise GroupDoesNotExist('Specified group "%s" does not exist.' % group)
            receivers = self.messageReceiverMap.get(msg.messageType, set()) & self.object_group_map[group]
            for r in receivers:
                if not self.designated_to_handle(r, msg):
                    continue
                # finish this message if it was handled or had designated receiver
                if r.handleMessage(msg) or msg.receiverID:
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
            return: True if the receiver is designated to handle the message
                    False otherwise
        '''
        return True
    def abortMessage(self, msgType, abortAll=True):
        '''Find the next-available instance of the named event type and remove it from the processing queue.
            This may be done up to the point that it is actively being processed ...
            e.g.: is safe to happen during event processing itself.
            return: true if the event was found and removed
                    false otherwise
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
        '''Fire off event (asynchronous) will be processed when tick() method is called
            return: true if the message was added to the processing queue
                    false otherwise.
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
        '''Fire off message (synchronous) do it NOW kind of thing, analogous to Win32 SendMessage() API.
            return: true if the event was consumed, false if not. 
            note: that it is acceptable for all event listeners to act on an event and not consume it
                this return signature exists to allow complete propogation of that shred of information from the internals of 
                this system to outside uesrs.
        '''
        if not self.validateType(msg.messageType):
            return False
        # for receivers that register to all events, send the message to them
        map(lambda x: x.handleMessage(msg), self.messageReceiverMap[WildCardMessageType])
        # Now loop thru the receivers that actually subscribed to this particular message type
        processed = False
        for r in self.messageReceiverMap.get(msg.messageType, set()):
            if r.handleMessage(msg):
                processed = True
        return processed
    def addReceiver(self, receiver, msgType):
        '''registers the receiver with the message type
            return: true if success
                    false otherwise
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
            return: true if successfully unregistered
                    false if the pair is not found in registry
        '''
        if not self.validateType(msgType):
            return False
        if not receiver in self.messageReceiverMap[msgType]:
            return False
        else:
            self.messageReceiverMap[msgType].remove(receiver)
            return True
    def registerReceiver(self, receiver, group=''):
        for s in receiver.subscriptions:
            self.addReceiver(receiver, s)
        if group:
            if not self.groups.has_key(group):
                raise GroupDoesNotExist('Group "%s" does not exist.' % group)
            self.object_group_map[group].add(receiver)
        else:
            self.object_group_map[PySageInternalMainGroup].add(receiver)
    def unregisterReceiver(self, receiver):
        for s in receiver.subscriptions:
            self.removeReceiver(receiver, s)
        # remove this receiver from any group that it belongs to
        for members in self.object_group_map.values():
            if receiver in members:
                members.remove(receiver)
    def reset(self):
        '''removes all messages, receivers, used for debugging/testing'''
        self._should_quit = True
        # exist all threads
        for g in self.groups.values():
            g.join() 
            
        self._should_quit = False
        self.messageTypes = []
        self.messageReceiverMap = {WildCardMessageType: set()}
        self.activeQueue = deque()
        self.processingQueue = deque()
        self.groups = {}
        self.object_group_map = collections.defaultdict(set)
        self.object_group_map[PySageInternalMainGroup] = set()
    def __del__(self):
        util.Singleton.__del__(self)
        self.reset()
          
