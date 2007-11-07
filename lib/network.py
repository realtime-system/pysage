# network.py
# Credits:
#   this module uses pyraknet and consequently the underlying RakNet networking
#   library.  
import pyraknet

class Error(Exception):
    pass

class SendError(Error):
    pass

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

if __name__ == '__main__':
    def incoming_connection(packet):
        global s
        print 'incoming connection from address: %s' % packet.address
        print 'incoming connection player: %s' % packet.player
        print 'incoming connection from address string: %s' % s.rn.get_address_string(packet.address)
    def incoming_test_packet(packet):
        print 'incoming packet length: %s' % len(packet.data)
    import time
    s = Network()
    s.set_callback(pyraknet.PacketTypes.ID_NEW_INCOMING_CONNECTION, incoming_connection)
    s.set_callback(100, incoming_test_packet)
    help(s.listen)
    s.listen(port=1000, max_players=8)
    count = 5
    c = {}
    for i in range(count):
        c[i] = Network()
        c[i].connect(host='localhost', port=1000)
    while 1:
        time.sleep(0.1)
        s.poll()
        data = '%c%s' % (100,  'a' * 1024*1024)
        for i in range(count):
            c[i].poll()
            c[i].send(data, broadcast=True)
            
            
            
        
        
        
        