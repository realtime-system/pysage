# Messaging.py
# Credits: 
#   this module builds on the concepts of a trigger system introduced in
#   the book: "Game Coding Complete - 2nd Edition" by Mike McShaffry
# this module implements a message manager along with message receivers
import util
import threading
import collections
import time

__all__ = ['InvalidMessageProperty', 'GroupAlreadyExists', 'GroupDoesNotExist', 'InvalidGroupName']

WildCardMessageType = '*'
PySageInternalMainGroup = '__MAIN_GROUP__'

class InvalidMessageProperty(Exception):
    pass

class GroupAlreadyExists(Exception):
    pass

class GroupDoesNotExist(Exception):
    pass

class InvalidGroupName(Exception):
    pass

class MessageReceiver(object):
    '''generic message receiver class that object message receivers inherit from'''
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
    def __init__(self, receiverID=None, **kws):
        self._properties = dict( (x, None) for x in self.properties )
        for name, value in kws.items():
            self.lazySetProperty(name, value)
        self.gid = self.assign_id()
        self.receiverID = receiverID
    def assign_id(self):
        return str(id(self))
    def __repr__(self):
        return 'Message %s %s' % (self.messageType, self.gid)
    @property
    def messageType(self):
        return self.__class__.__name__
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

class MessageManager(util.ThreadLocalSingleton):
    '''generic message manager singleton class that game object manager inherits from'''
    def init(self):
        self.messageTypes = []
        # WildCardMessageType is the wild card message type, 
        # all receivers that subscribe to this receive all messages
        # however these type of receivers cannot consume the message
        self.messageReceiverMap = {WildCardMessageType: set()}
        
        # we will need a queue per group here
        # because even if one group could not process the message, it does not mean
        # that other groups could not process the message
        # since deques are thread-safe, a group that could not process a message could potentially
        # pop it off of the central queue and "waste it"
        # therefore we want it enqueue a message to every group's queue for simultaneous processing
        # note that this also means that when a message receiver decides that it "handled" the message,
        # it can only stop propagating that message further within its own group
        self.message_queues = {PySageInternalMainGroup: collections.deque()}
        
        # for groups handling
        self.groups = {}
        self.object_group_map = {PySageInternalMainGroup: set()}
        self._should_quit = False
    def set_groups(self, gs):
        '''starts the groups in thread objects and let them run their tick at specified intervals'''
        for g in gs:
            self.add_group(g)
        # returning myself
        return self
    def add_group(self, name, max_tick_time=None, interval=.03, minimum_sleep=.001):
        # make sure we have a str
        g = str(name)
        if self.groups.has_key(g):
            raise GroupAlreadyExists('Group name "%s" already exists.' % g) 
        # validating group name 
        if not g and not g == PySageInternalMainGroup:
            raise InvalidGroupName('Group name "%s" is invalid.' % g) 
            
        def _run(manager, group, interval, minimum_sleep):
            '''interval is in milliseconds of how long to sleep before another tick'''
            while not manager._should_quit:
                start = util.get_time()
                manager.tick(maxTime=max_tick_time, group=group)
                     
                # we want to sleep the different between the time it took to process and the interval desired
                _time_to_sleep = interval - (util.get_time() - start)
                # incase we have less than minimum required to sleep, we will sleep the minimum
                if _time_to_sleep < minimum_sleep:
                    _time_to_sleep = minimum_sleep
                   
                time.sleep(_time_to_sleep)
            return False
                        
        self.message_queues[g] = collections.deque()
        self.groups[g] = threading.Thread(target=_run, name=g, kwargs={'manager':self, 'group':g, 'interval':interval, 'minimum_sleep':minimum_sleep})
        self.groups[g].start()
       
        return self
    def validateType(self, messageType):
        if not messageType:
            return False
        else:
            return True
    def validateMessage(self, msg):
        return msg.validate()
    def validate_group(self, group):
        # validate that the group exists
        if not group == PySageInternalMainGroup and not group in self.groups:
            raise GroupDoesNotExist('Specified group "%s" does not exist.' % group)
    def tick(self, maxTime=None, group=PySageInternalMainGroup):
        '''
        Process queued messages.
        
        :Parameters:
            - `maxTime`: processing time limit so that the event processing does not take too long. 
              not all messages are guranteed to be processed with this limiter

        :Return:
            - true: if all messages ready for processing were completed
            - false: otherwise (i.e.: processing took more than maxTime)
        '''
        self.validate_group(group)
        # save off the number of messages that we have at this point
        # so that we never process more than this amount of messages to prevent infinite cycle
        # if a message receiver sends a message to the queue while processing
        message_count = len(self.message_queues[group])
        message_processed = 0
        
        startTime = util.get_time()
        while len(self.message_queues[group]) and message_processed < message_count:
            # keep track of the count so that we do not process more than necessary
            message_processed += 1
            
            # in another multh-threaded environment, another thread that calls tick could have empties the queue here
            try:
                # always pop the message off the queue, if there is no listeners for this message yet
                # then the message will be dropped off the queue
                msg = self.message_queues[group].popleft()
            # if someone else popped off my message, I just move on
            except IndexError:
                break
                
            # for receivers that handle all messages let them handle this
            for r in self.messageReceiverMap[WildCardMessageType] & self.object_group_map.get(group, set()):
                r.handleMessage(msg)
            # now pass msg to message receivers that subscribed to this message type
            receivers = self.messageReceiverMap.get(msg.messageType, set()) & self.object_group_map.get(group, set())
            for r in receivers:
                # this message will only be processed by potentially one receiver
                if msg.receiverID:
                    if self.designated_to_handle(r, msg):
                        r.handleMessage(msg)
                        # break regardless because the receiver is the only one handling this message
                        break
                else:
                    # if this message was handled within this group, then stop propagating the message to the
                    # rest of the group
                    # Note: this does not stop the message from being further propagated in other groups
                    #       cannot prevent multiple receivers processing the same message without a lock
                    if r.handleMessage(msg):
                        break
            if maxTime and util.get_time() - startTime > maxTime:
                break
            
        return len(self.message_queues[group]) == 0
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
        '''find the next message that is of the type msgType and remove it from each queue
            return: true if the event was found and removed, false otherwise
        '''
        if not self.validateType(msgType):
            return False
        success = False
        for queue in self.message_queues.values():
            for i in [x for x in queue if x.messageType == msgType]:
                # queue.remove(v) only available in python 2.5
                queue.remove(i)
                success = True
                if not abortAll:
                    break
        return success
    def get_message_count(self, group=PySageInternalMainGroup):
        self.validate_group(group)
        return len(self.message_queues[group])
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
            map(lambda q: q.append(msg), self.message_queues.values())
            return True
    def trigger(self, msg):
        '''synchronously processes a message without putting it on the queue
            return: true if the event was consumed, false if not. 
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
    def registerReceiver(self, receiver, group=''):
        for s in receiver.subscriptions:
            self.addReceiver(receiver, s)
        if group:
            if not self.groups.has_key(group):
                raise GroupDoesNotExist('Group "%s" does not exist.' % group)
            if not group in self.object_group_map:
                self.object_group_map[group] = set()
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
        self.message_queues = {PySageInternalMainGroup: collections.deque()}
        self.groups = {}
        self.object_group_map = {PySageInternalMainGroup: set()}
          
