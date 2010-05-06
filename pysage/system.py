'''pysage is a high-level message passing library with currency in mind.

For more information: http://code.google.com/p/pysage/

Copyright (c) 2007-2008 Shuo Yang (John) <bigjhnny@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''
# system.py
import struct
import messaging
import transport
import util
import time
import process as processing
import logging

__all__ = ('Message', 'ActorManager', 'Actor', 'PacketError', 'PacketTypeError', 'GroupAlreadyExists', 'GroupDoesNotExist', 'CreateGroupError',
           'DefaultActorFailed', 'GroupFailed', 'get_logger', 'WrongMessageTypeSpecified')

GROUP_WARNING_MESSAGE = '''Please call mgr.enable_groups() first before using "groups" mode.  This ensures that your app is safe when "frozen" into an executable in Windows.  Also ensure any "add_process_group" calls happen under the main function (i.e.: if __name__ == '__main__' ...).  This is required under Windows.  See "Grouping" documentation.'''

class PacketError(Exception):
    pass

class PacketTypeError(Exception):
    pass

class GroupAlreadyExists(Exception):
    pass

class GroupDoesNotExist(Exception):
    pass

class CreateGroupError(Exception):
    pass

class DefaultActorFailed(Exception):
    pass

class GroupFailed(Exception):
    pass

class WrongMessageTypeSpecified(Exception):
    pass

class ConcreteMessageAlreadyDefined(Exception):
    pass

class GroupsNotEnabled(Exception):
    pass

def get_logger():
    return processing.get_logger()
    
def _subprocess_main(name, default_actor_class, max_tick_time, interval, server_addr, _should_quit, packet_types):
    '''interval is in milliseconds of how long to sleep before another tick'''
    # creating a client mode manager
    # after forking, we would already have an instance tied to the parent PID, simply change that to our PID
    ActorManager._switch_instance_after_fork()
    manager = ActorManager.get_singleton()
    manager.reset_to_client_mode()
    # under non-forking systems, this would simply create a new manager
    # the new manager may not have all packet types registered, register them here
    # on windows, packet types will be auto-registered
    # on *nix, we would have whatever packets that were registered by the parent process
    if manager.packet_types:
        assert set(manager.packet_types) == set(packet_types)
    else:
        manager.packet_types = packet_types
    manager._ipc_connect(server_addr, _should_quit)
    manager.log(logging.INFO, 'current process "%s" is bound to address: "%s"' % (processing.get_pid(processing.current_process()), manager.ipc_transport._connection.fileno()))
    try:
        default_actor = default_actor_class()
    except Exception, e:
        raise DefaultActorFailed('Default actor class "%s" failed to initialize. ("%s")' % (default_actor_class, e))
    else:
        manager.register_actor(default_actor)
    # manager is now seen as a child
    assert not manager.is_main_process
    while not manager._should_quit.value:
        start = util.get_time()
        manager.tick(max_time=max_tick_time)
        # we want to sleep the difference between the time it took to process and the interval desired
        _time_to_sleep = interval - (util.get_time() - start)
        if _time_to_sleep > 0.0:
            time.sleep(_time_to_sleep)
    return False

class ActorManager(messaging.MessageManager):
    '''provides actor, IPC and network functionality'''
    PYSAGE_MAIN_GROUP = '__MAIN_GROUP__'
    def init(self):
        messaging.MessageManager.init(self)
        self.objectIDMap = {}
        self.objectNameMap = {}
        
        self.gid = 0
        self.transport = None
        self.packet_types = {}
        self.message_map = {}
        # using either Domain Socket (Unix) or Named Pipe (windows) as means
        # for IPC
        self.groups = {}
        self.is_main_process = True
        self._groups_enabled = False
        self.ipc_transport = transport.IPCTransport()
    def find(self, name):
        '''returns an actor by its name, None if not found'''
        return self.get_actor_by_name(name)
    def get_actor(self, id):
        return self.objectIDMap.get(id, None)
    def get_actor_by_name(self, name):
        return self.objectNameMap.get(name, None)
    @property
    def actors(self):
        return self.objectIDMap.values()
    def trigger_to_actor(self, id, msg):
        '''
        sends a particular game actor a message if that game actor implements this message type
        
        return:
        
        - `True`: if event was consumed
        - `False`: otherwise
        '''
        # if we are sending adhoc messages, we'll create a message instance with the adhoc type
        if type(msg) == type(''):
            # adhoc messages are only allowed if a concrete message class is not constructed
            if self.message_map.has_key(msg):
                raise ConcreteMessageAlreadyDefined('A concrete message class of the name "%s" is already defined.  Adhoc messages of this type are not allowed.' % msg)
            msg = Message(message_type = msg)
        obj = self.objectIDMap[id]
        for recr in self.message_receiver_map[messaging.WildCardMessageType]:
            recr.handle_message(msg)
        return obj.handle_message(msg)
    def queue_message_to_actor(self, id, msg):
        '''
        queues message designated for a specific actor

        :Parameters:
            - `id`: the "id" of the actor
            - `msg`: the message to be queued
        '''
        msg.receiverID = id
        self.queue_message(msg)
        return True
    def register_actor(self, obj, name=None):
        '''
        register the actor with the actor manager so that the actor can receive messages as well as having "update" called
        
        :Parameters:
            - `obj`: the actor to be registered
            - `name`: optional.  The name of the actor for which you can refer back to the actor later
        '''
        messaging.MessageManager.register_receiver(self, obj)
        self.objectIDMap[obj.gid] = obj
        if name:
            self.objectNameMap[name] = obj
        return obj
    def unregister_actor(self, obj):
        '''
        unregister the actor from the actor manager.  actor will no longer receive messages or have its "update" method called
        
        :Parameters:
            - `obj`: the actor being unregistered
        '''
        messaging.MessageManager.unregister_receiver(self, obj)
        del self.objectIDMap[obj.gid]
        
        # deleting the actor from the dictionary the safe way
        n = None
        for name,o in self.objectNameMap.items():
            if o == obj:
                n = name
                break
        if not n == None:
            del self.objectNameMap[n]
                
        return self
    def designated_to_handle(self, r, m):
        '''handles designated messages'''
        if m.receiverID:
            if m.receiverID == r.gid:
                return True
            else:
                return False
        else:
            # if receiverID isn't specified, whoever registers can handle this message
            return True
    def tick(self, max_time=None, *args, **kws):
        '''
        first poll process for packets, then network messages, then actor updates

        note: the max_time takes a "best effort" approach.  It does not gurantee that processing will always
        finish on time (duration less than max_time specified)
        However, it does insure that it poll at least one ipc and one network message
        per iteration, to avoid "starvation"

        :Parameters:
            - `max_time`: processing time limit in seconds so that the event processing does not take too long. 
              not all messages are guranteed to be processed with this limiter
        
        :Return:
            - true: if all messages ready for processing were completed
            - false: otherwise (i.e.: processing took more than max_time)
        '''
        cut_off_time = None
        if max_time:
            cut_off_time = util.get_time() + max_time
        # server manager need to monitor sub-groups
        if self.is_main_process:
            for group, (p, _id, switch) in self.groups.items():    
                if not processing.is_alive(p):
                    raise GroupFailed('Group "%s" failed' % group)

        # always poll at least one ipc message here
        has_more = True
        while has_more:
            has_more = self.ipc_transport.poll(self.packet_handler)
            if cut_off_time and util.get_time() > cut_off_time:
                break
        
        # always poll at least one network message here
        if self.transport:
            has_more = True
            while has_more:
                has_more = self.transport.poll(self.packet_handler)
                if cut_off_time and util.get_time() > cut_off_time:
                    break

        self.log(logging.DEBUG, 'process "%s" queue length: %s' % (processing.get_pid(processing.current_process()), self.queue_length))
        
        # process all messages first
        new_max_time = None
        if cut_off_time:
            new_max_time = cut_off_time - util.get_time()
        # process these messages given the newly calculated max time
        ret = messaging.MessageManager.tick(self, max_time = new_max_time, **kws)
        # then update all actors
        map(lambda x: x.update(*args, **kws), sorted(self.objectIDMap.values(), lambda x,y: y._SYNC_PRIORITY - x._SYNC_PRIORITY))
        return ret
    def log(self, level, msg):
        '''process aware logging'''
        return processing.get_logger().log(level, msg)
    def _ipc_listen(self):
        # starting server mode
        self.ipc_transport.listen()
    def _ipc_connect(self, server_addr, _should_quit):
        # starting client mode
        self.ipc_transport.connect(server_addr)
        self._should_quit = _should_quit
        self.groups[self.PYSAGE_MAIN_GROUP] = (None,server_addr,None)
    def listen(self, host, port, transport_class=transport.SelectUDPTransport):
        '''
        starts listening for network messages given the port and the transport class

        :Parameters:
            - `host`: the host for which the server will bind to
            - `port`: the port for which the server will listen on
            ` `transport_class`: optional.  the transport class that will be used to define the protocol
        '''
        def connection_handler(client_address):
            self.log(logging.DEBUG, 'connected to client: %s' % client_address)
        self.transport = transport_class()
        self.transport.listen(host, port, connection_handler)
        return self
    def connect(self, host, port, transport_class=transport.SelectUDPTransport):
        '''
        connects to a server so that message communication can be started

        :Parameters:
            - `host`: the host for which to connect to
            - `port`: the port for which to connect to
        '''
        self.transport = transport_class()
        self.transport.connect(host, port)
        return self
    def send_message(self, msg, address=None):
        '''
        send a message to a network
        
        :Parameters:
            - `msg`: the message to send
            - `clientid`: the network for which to send the message to
        '''
        self.transport.send(msg.to_string(), address=address)
        return self
    def queue_message_to_group(self, group, msg):
        '''message is serialized and sent to the group (process) specified'''
        if not self.groups.has_key(group):
            raise GroupDoesNotExist('Group "%s" does not exist' % group)
        p, _clientid, switch = self.groups[group]
        self.log(logging.INFO, 'queuing message "%s" to "%s"' % (msg, _clientid))
        self.ipc_transport.send(msg.to_string(), _clientid)
    def broadcast_message(self, msg):
        self.transport.send(msg.to_string(), broadcast=True)
        return self
    def packet_handler(self, packet, address):
        packetid = ord(packet[0])
        processing.get_logger().debug('Received packet of type "%s"' % type)
        if packetid < 100:
            processing.get_logger().warning('internal packet unhandled: "%s"' % self.transport.packet_type_info(packetid))
            return self
        p = self.packet_types[packetid]().from_string(packet)
        p.sender = address
        self.queue_message(p)
        return self
    def register_packet_type(self, packet_class):
        # skip the base packet class
        if packet_class.__name__ == 'Message':
            return
        if not packet_class.packet_type:
            raise PacketTypeError('Packet_type must be specified by class "%s"' % packet_class)
        if packet_class.packet_type <= 100:
            raise PacketTypeError('Packet_type must be greater than 100.  Had "%s"' % packet_class.packet_type)
        if self.packet_types.has_key(packet_class.packet_type):
            raise PacketTypeError('Packet_type is already registered with packet "%s"' % self.packet_types[packet_class.packet_type])
        self.packet_types[packet_class.packet_type] = packet_class
        self.message_map[packet_class.__name__] = packet_class
    def validate_groups_mode(self):
        if not self._groups_enabled:
            raise GroupsNotEnabled(GROUP_WARNING_MESSAGE)
    def enable_groups(self):
        '''enable freeze support'''
        processing.enable_groups()
        self._groups_enabled = True
    def add_process_group(self, name, default_actor_class=None, max_tick_time=None, interval=.03):
        '''adds a process group to the pool'''
        assert self.is_main_process, 'Pysage currently only supports spawning child groups from the Main Group'
        self.validate_groups_mode()
        self._ipc_listen()
        # make sure we have a str
        g = str(name)
        if self.groups.has_key(g):
            raise GroupAlreadyExists('Group name "%s" already exists.' % g) 
        server_addr = self.ipc_transport.address
        # shared should quit switch
        switch = processing.Value('B', 0)
        actor_class = default_actor_class or DefaultActor
        p = processing.Process(target=_subprocess_main, name=name, args=(name, actor_class, max_tick_time, interval, server_addr, switch, self.packet_types))
        p.start()
        processing.get_logger().info('started group "%s" in process "%s"' % (name, processing.get_pid(p)))
        _clientid = self.ipc_transport.accept()
        self.groups[g] = (p, _clientid, switch)
    def remove_process_group(self, name):
        '''removes a process group from the pool'''
        if not self.groups.has_key(name):
            raise GroupDoesNotExist('Group "%s" does not exist' % name)
        p, _clientid, switch = self.groups[name]
        switch.value = 1
        p.join()
        self.ipc_transport.disconnect(_clientid)
        del self.groups[name]
        return self
    def clear_process_group(self):
        '''shuts down all children processes'''
        if self.is_main_process:
            # if we are the server manager, take care to shut down all children
            for name in self.groups.keys():
                self.remove_process_group(name)
        self.groups = {}
    @property
    def queue_length(self):
        return len(self.active_queue)
    def reset_to_client_mode(self):
        '''after forking in *nix systems, we need to clean up the current manager'''
        super(ActorManager, self).reset_to_client_mode()
        self.is_main_process = False
        self.groups = {}
        self.ipc_transport = transport.IPCTransport()
        self.objectIDMap = {}
        self.objectNameMap = {}
        self.transport = None
    def reset(self):
        '''mainly used for testing'''
        messaging.MessageManager.reset(self)
        self.objectIDMap = {}
        self.objectNameMap = {}
        
        self.clear_process_group()
        self.gid = 0
        if transport.RAKNET_AVAILABLE:
            self.transport = transport.RakNetTransport()
        else:
            self.transport = transport.Transport()
        # not removing the auto-registered packet types
        # self.packet_types = {}
        self.groups = {}
        self.ipc_transport = transport.IPCTransport()
                
class Actor(messaging.MessageReceiver):
    '''actor class extends the message receiver class to provide actor like functionality'''
    @property
    def gid(self):
        '''return a globally unique id that is good cross processes'''
        return (ActorManager.get_singleton().gid, id(self))
    
class DefaultActor(Actor):
    '''default actor for a group - group is assigned this actor if no default actor is specified'''
    subscriptions = [messaging.WildCardMessageType]
    def handle_message(self, msg):
        processing.get_logger().info('Default actor received message "%s"' % msg)
        return False

class AutoMessageRegister(type):
    '''metaclass that auto register all message classes with the actor manager'''
    def __init__(cls, name, bases, dct):
        super(AutoMessageRegister, cls).__init__(name, bases, dct)
        ActorManager.get_singleton().register_packet_type(cls)
        
class Message(messaging.Message):
    '''extends messaging.Message to provide network functionality'''
    __metaclass__ = AutoMessageRegister
    types = []
    packet_type = None
    def to_string(self):
        '''packs message into binary stream'''
        if not len(self.types) == len(self.properties):
            raise WrongMessageTypeSpecified('Message "%s" has %s properties, but %s types specified.  Check the "types" and "properties" class attribute of the "%s" class' % (self, len(self.properties), len(self.types), type(self)))
        # first encode the message type identifier
        buf = struct.pack('!B', self.packet_type)
        # iterate thru all attributes
        for i,_type in enumerate(self.types):
            # get name and value of the attribute
            name = self.properties[i]
            value = self._properties[name]
            # for composite type, pack it looping over each subtype
            if type(_type) == type(()):
                pack_func = getattr(self, 'pack_' + name, None)
                if pack_func:
                    for j,v in enumerate(pack_func(value)):
                        buf = self.pack_attr(_type[j], buf, v, name)
                else:
                    for j,v in enumerate(value):
                        buf = self.pack_attr(_type[j], buf, v, name)
            # for mono types, just pack it
            else:
                buf = self.pack_attr(_type, buf, value, name)
        return buf
    def from_string(self, data):
        '''unpacks the property data into the object, from binary stream'''
        pos = 1
        # iterate over all types we need to unpack
        for i, _type in enumerate(self.types):
            # get the name of the property we are currently unpacking
            name = self.properties[i]
            # if type of this value is a composite one, unpack subtypes individually
            # then pass all of them together to unpack the higher level property
            if type(_type) == type(()):
                values = []
                # after packing children, pass children to parent to process
                for subtype in _type:
                    value, size = self.unpack_attr(subtype, data, pos)
                    values.append(value)
                    pos += size
                unpack_func = getattr(self, 'unpack_' + name, None)
                if unpack_func:
                    self.set_property(name, getattr(self, 'unpack_' + name)(values))
                else:
                    self.set_property(name, values)
            # if not composite, just unpack them and set the property
            else:
                value, size = self.unpack_attr(_type, data, pos)
                pos += size
                self.set_property(name, value)
        if pos != len(data):
            raise PacketError('incorrect length upon unpacking %s: got %i expected %i' % (self.__class__.__name__, len(data), pos))
        return self
    def pack_attr(self, _type, buf, value, name):
        '''pack a single attribute into the running buffer'''
        # custom types
        # p: pascal string, a short variable length string
        # packed like this:
        # [unsigned char: length of string][string itself]
        if _type == 'p':
            length = len(value)
            if not length <= 255:
                raise ValueError('pascal string cannot exceed 255 chars. Given %s' % length)
            buf += struct.pack('!B%is' % length, length, value)
        # an: array of type 'n'
        # packed like this:
        # [int: items in list][item1][item2][...]
        elif _type[0] == 'a':
            buf += struct.pack('!i', len(value))
            for item in value:
                buf += struct.pack('!%s' % _type[1], item)
        # S: long string of length more than 255
        # packed like:
        # [int: length of string][string itself]
        elif _type[0] == 'S':
            length = len(value)
            buf += struct.pack('!i%is' % length, length, value)
        # default types
        else:
            try:
                buf += struct.pack('!' + _type, value)
            except struct.error, err:
                raise PacketError('%s.%s(%s,%s): %s' % (self.__class__.__name__, name, value, type(value), err))
        return buf
    def unpack_attr(self, _type, data, pos):
        '''unpack a single attribute from binary stream given current pos'''
        # handle pascal string
        if _type == 'p':
            # the first byte in pascal string is the length of the string
            size = struct.unpack('!B', data[pos:pos+1])[0]
            value = struct.unpack('!%is' % size, data[pos+1:pos+1+size])[0]
            # add one byte to the total size of this attribute
            size += 1
        # handle array type
        elif _type[0] == 'a':
            # get the size of the array, first 4 bytes (type "i")
            length = struct.unpack('!i', data[pos:pos+4])[0]
            # type of the items on this array is given as the second element in the type tuple
            list_type = '!%s' % _type[1]
            list_type_size = struct.calcsize(list_type)
            # total size is the 4 bytes (length) plus the type size times number of elements
            size = 4 + length  * list_type_size
            value = []
            for a in range(length):
                offset = list_type_size*a+pos+4
                value.append(struct.unpack(list_type, data[offset:offset+list_type_size])[0])
        # handle long string, this can handle string of size more than 255
        elif _type[0] == 'S':
            # get the size of the string, first 4 bytes (type "i")
            length = struct.unpack('!i', data[pos:pos+4])[0]
            value = struct.unpack('!%is' % length, data[pos+4:pos+4+length])[0]
            # the size of this struct is the length of string + 4 bytes of the integer
            size = length + 4
        # handle built-in struct type
        else:
            size = struct.calcsize(_type)
            try:
                value = struct.unpack('!'+_type, data[pos:pos+size])[0]
            except struct.error, err:
                raise PacketError('Error unpacking "%s": %s' % (self.__class__.__name__, err))
        return value, size

