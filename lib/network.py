# network.py
# Credits:
#   this module uses pyraknet and consequently the underlying RakNet networking
#   library.  
import pyraknet
from messaging import Message

class Error(Exception):
    pass

class SendError(Error):
    pass

class PacketError(Exception):
    pass

class Packet(Message):
    def encode(self):
        '''put property data into binary stream, returns the string'''
        ret = struct.pack('!B', self._id)
        for i,_type in enumerate(self._types):
            name = self.properties[i]
            value = self.getProperty(name)
            # if this type of this value is a composite one, loop over it's subtypes and pack them individually into the stream
            if type(_type) == type(()):
                for j,v in enumerate(getattr(self, 'pack_' + name)(value)):
                    ret = self.packAttr(_type[j], ret, v, name)
            else:
                ret = self.packAttr(_type, ret, value, name)
        return ret
    def packAttr(self, _type, str, value, name):
        '''depending on the type of the value to pack, returns the binary representation of it'''
        # p - variable length string (max 255 chars)
        # [unsigned char: length of string][string]
        if _type == 'p':
            str += struct.pack('!B%is' % len(value), len(value), value)
        # tn - variable length list of type 'n'
        # [int: items in list][item][item][...]
        elif _type[0] == 't':
            str += struct.pack('!i', len(value))
            for item in value:
                str += struct.pack('!%s' % _type[1], item)
        # default struct types
        else:
            try:
                str += struct.pack('!' + _type, value)
            except struct.error, err:
                raise PacketError('%s.%s(%s,%s): %s' % (self.__class__.__name__, name, value, type(value), err))
        return str
    def decode(self, data):
        '''restores the property data from binary string'''
        pos = 1
        for i, _type in enumerate(self._types):
            name = self.properties[i]
            # if type of this value is a composite one, unpack subtypes individually
            # then pass all of them together to unpack the higher level property
            if type(_type) == type(()):
                values = []
                # after packing children, pass children to parent to process
                for subtype in _type:
                    value, size = self.unpackAttr(subtype, data, pos)
                    values.append(value)
                    pos += size
                else:
                    self.setProperty(name, getattr(self, 'unpack_' + name)(values))
            # if not composite, just unpack them and set the property
            else:
                value, size = self.unpackAttr(_type, data, pos)
                pos += size
                self.setProperty(name, value)
        if pos != len(data):
            raise PacketError('length mismatch on decoding %s: got %i expected %i' % (self.__class__.__name__, len(data), pos))
    def unpackAttr(self, _type, data, pos):
        if _type == 'p':
            size = struct.unpack('!B', data[pos:pos+1])[0]
            value = struct.unpack('!%is' % size, data[pos+1:pos+1+size])[0]
            size += 1
        elif _type[0] == 't':
            items = struct.unpack('!i', data[pos:pos+4])[0]
            list_type = '!%s' % _type[1]
            list_type_size = struct.calcsize(list_type)
            size = 4 + items * list_type_size
            value = []
            for a in range(items):
                offset = list_type_size*a+pos+4
                tmp = struct.unpack(list_type, data[offset:offset+list_type_size])[0]
                value.append(tmp)
        else:
            size = struct.calcsize(_type)
            try:
                value = struct.unpack('!'+_type, data[pos:pos+size])[0]
            except struct.error, err:
                raise PacketError('length mismatch on decoding %s' % (self.__class__.__name__))
        return value, size

class Network(object):
    def __init__(self):
        self.rn = pyraknet.Peer()
        self.callbacks = {}
        self.default_callback = None
    def connect(self, host, port, thread_sleep_timer=10):
        self.rn.init(peers=1, thread_sleep_timer=thread_sleep_timer)
        self.rn.connect(host=host, port=port)
        self.default_peer = 0
    def listen(self, port, max_players, thread_sleep_timer=10):
        self.rn.init(peers=max_players, port=port, thread_sleep_timer=thread_sleep_timer)
        self.rn.set_max_connections(max_players)
    def send(self, data, id=-1, reliability=pyraknet.PacketReliability.RELIABLE_ORDERED, priority=0, channel=0, broadcast=False):
        '''Send a packet to a peer.

        data: A string of data to send. Set the first byte to be an unused packet type. See pyraknet.PacketTypes.
        id: The player ID to send to. When broadcast=True, it will send to everyone except this player.
        '''
        if id == -1 and not broadcast:
            try:
                id = self.default_peer
            except AttributeError:
                raise SendError('Tried to send a packet to no one')
        if id >= 0:
            address = self.rn.get_address_from_id(id)
        elif broadcast:
            address = pyraknet.PlayerAddress()
        self.rn.send(data, len(data), pyraknet.PacketPriority.LOW_PRIORITY - priority, reliability, channel, address, broadcast)
    def poll(self):
        packet = self.rn.receive()
        while packet:
            self.process_packet(packet)
            packet = self.rn.receive()
    def set_callback(self, packet_type, function):
        self.callbacks[packet_type] = function
    def set_default_callback(self, function):
        self.default_callback = function
    def del_callback(self, packet_type):
        del self.callbacks[packet_type]
    def get_packet_type_name(self, id):
        for a in dir(pyraknet.PacketTypes):
            if a[0:3] == 'ID_' and eval('pyraknet.PacketTypes.%s' % (a)) == id:
                return a
        return 'ID_UNKNOWN (%i)' % id
    def process_packet(self, packet):
        type = ord(packet.data[0])
        try:
            self.callbacks[type](packet)
        except KeyError:
            try:
                if self.default_callback:
                    self.default_callback(packet)
            except TypeError:
                name = self.get_packet_type_name(type)
                print 'Got unhandled packet: %i %s (tried to call default callback)' % (type, name)
                raise  
            
            
        
        
        
        