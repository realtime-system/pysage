# network.py
import struct
import system
import transport

def generate_network_id():
    '''a generator that yeilds ids'''
    counter = 0
    while True:
        yield counter
        counter += 1
        
network_id = generate_network_id()

class PacketError(Exception):
    pass

class Packet(system.Message):
    '''a packet is a network message'''
    types = []
    packet_type = None
    def to_string(self):
        '''packs message into binary stream'''
        # first encode the message type identifier
        buf = struct.pack('!B', self.packet_type)
        # iterate thru all attributes
        for i,_type in enumerate(self.types):
            # get name and value of the attribute
            name = self.properties[i]
            value = self.get_property(name)
            # for composite type, pack it looping over each subtype
            if type(_type) == type(()):
                for j,v in enumerate(getattr(self, 'pack_' + name)(value)):
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
                self.set_property(name, getattr(self, 'unpack_' + name)(values))
            # if not composite, just unpack them and set the property
            else:
                value, size = self.unpack_attr(_type, data, pos)
                pos += size
                self.set_property(name, value)
        if pos != len(data):
            raise PacketError('incorrect length upon unpacking %s: got %i expected %i' % (self.__class__.__name__, len(data), pos))
    def pack_attr(self, _type, buf, value, name):
        '''pack a single attribute into the running buffer'''
        # custom types
        # p: pascal string, a short variable length string
        # packed like this:
        # [unsigned char: length of string][string itself]
        if _type == 'p':
            buf += struct.pack('!B%is' % len(value), len(value), value)
        # tn: variable length list of type 'n'
        # packed like this:
        # [int: items in list][item1][item2][...]
        elif _type[0] == 't':
            buf += struct.pack('!i', len(value))
            for item in value:
                buf += struct.pack('!%s' % _type[1], item)
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
        # handle variable length list type
        elif _type[0] == 't':
            # get the size of the list, first 4 bytes (type "i")
            items = struct.unpack('!i', data[pos:pos+4])[0]
            # type of the items on this list is given as the second element in the type tuple
            list_type = '!%s' % _type[1]
            list_type_size = struct.calcsize(list_type)
            # total size is the 4 bytes (length) plus the type size times number of elements
            size = 4 + items * list_type_size
            value = []
            for a in range(items):
                offset = list_type_size*a+pos+4
                value.append(struct.unpack(list_type, data[offset:offset+list_type_size])[0])
        # handle built-in struct type
        else:
            size = struct.calcsize(_type)
            try:
                value = struct.unpack('!'+_type, data[pos:pos+size])[0]
            except struct.error, err:
                raise PacketError('Error unpacking "%s": %s' % (self.__class__.__name__, err))
        return value, size

class NetworkManager(system.ObjectManager):
    '''extends objectmanager to provide network functionality'''
    def init(self):
        system.ObjectManager.init(self)
        self.gid = network_id.next()
        self.transport = transport.RakNetTransport()
    def start_server(self, port):
        '''TODO: finish this before implementing the transport'''
        def connection_handler(client_address):
            '''keeps books about this client and tell it a new id'''
            pass
        self.transport.listen(port, connection_handler)
        return self

class PacketReceiver(system.MessageReceiver):
    @property
    def gid(self):
        '''return a globally unique id that is good cross processes'''
        return (NetworkManager.get_singleton().gid, id(self))


    