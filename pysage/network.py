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
# network.py
import struct
import system
import transport
import logging

class PacketError(Exception):
    pass

class PacketTypeError(Exception):
    pass

class NetworkManager(system.ObjectManager):
    '''extends objectmanager to provide network functionality'''
    def init(self):
        system.ObjectManager.init(self)
        # self.gid = network_id.next()
        self.gid = 0
        if transport.RAKNET_AVAILABLE:
            self.transport = transport.RakNetTransport()
        else:
            self.transport = transport.Transport()
        self.clients = {}
        self.packet_types = {}
    def start_server(self, port):
        def connection_handler(client_address):
            logging.debug('connected to client: %s' % client_address)
        self.transport.listen(port, connection_handler)
        return self
    def connect(self, host, port):
        self.transport.connect(host, port)
        return self
    def send_message(self, msg, clientid):
        self.transport.send(msg.to_string(), id=self.clients[clientid])
        return self
    def broadcast_message(self, msg):
        self.transport.send(msg.to_string(), broadcast=True)
        return self
    def tick(self, *args, **kws):
        '''first poll network for packets, then process messages, then object updates'''
        self.transport.poll(self.packet_handler)
        return system.ObjectManager.tick(self, *args, **kws)
    def packet_handler(self, packet):
        packetid = ord(packet.data[0])
        logging.debug('Received packet of type "%s"' % type)
        if packetid < 100:
            logging.warning('internal packet unhandled: "%s"' % self.transport.packet_type_info(packetid))
            return self
        
        self.queue_message(self.packet_types[packetid]().from_string(packet.data)) 
        return self
    def register_packet_type(self, packet_class):
        # skip the base packet class
        if packet_class.__name__ == 'Packet':
            return
        if packet_class.packet_type <= 100:
            raise PacketTypeError('Packet_type must be greater than 100.  Had "%s"' % packet_class.packet_type)
        self.packet_types[packet_class.packet_type] = packet_class
        
class PacketReceiver(system.MessageReceiver):
    @property
    def gid(self):
        '''return a globally unique id that is good cross processes'''
        return (NetworkManager.get_singleton().gid, id(self))

class AutoRegister(type):
    def __init__(cls, name, bases, dct):
        super(AutoRegister, cls).__init__(name, bases, dct)
        NetworkManager.get_singleton().register_packet_type(cls)

class Packet(system.Message):
    '''a packet is a network message'''
    __metaclass__ = AutoRegister
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
        return self
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



