# transport.py
import process as processing
try:
    import pyraknet
except ImportError:
    RAKNET_AVAILABLE = False
else:
    RAKNET_AVAILABLE = True

class Transport(object):
    '''an interface that all transports must implement'''
    def connect(self, host, port):
        '''connects to a server implementing the same interface'''
        pass
    def listen(self, port, connection_handler):
        '''listens for connections, and calls connection_handler upon new connections'''
        pass
    def send(self, data, id=-1, broadcast=False):
        '''send data to another transport specified by "id"'''
        pass
    def poll(self, packet_handler):
        '''polls network data, pass any packet to the packet_handler'''
        pass
    def packet_type_info(self, packet_type_id):
        '''returns information about the packet type'''
        pass
    @property
    def address(self):
        '''returns the address this transport is bound to'''
        pass
    
class IPCPacket(object):
    def __init__(self, data):
        self.data = data

class IPCTransport(Transport):
    def __init__(self):
        self._connection = None
        self.peers = {}
    def listen(self):
        self._connection = processing.connection.Listener()
    def connect(self, address):
        self._connection = processing.connection.Client(address)
        self.peers[address] = self._connection
    @property
    def address(self):
        return self._connection.address
    def accept(self):
        c = self._connection.accept()
        _clientid = self._connection.last_accepted
        if not _clientid:
            _clientid = c.fileno()
        self.peers[_clientid] = c
        return _clientid
    def disconnect(self, _id):
        del self.peers[_id]
    def send(self, data, id=-1, broadcast=False):
        return processing.send_bytes(self.peers[id], data)
    def poll(self, packet_handler):
        for _id, conn in self.peers.items():
            while conn.poll():
                packet = IPCPacket(processing.recv_bytes(conn))
                packet_handler(packet)

class RakNetTransport(Transport):
    def __init__(self):
        self.net = pyraknet.Peer()
        self.connection_handler = None
        self.id_map = {}
        for t in dir(pyraknet.PacketTypes):
            if t.startswith('ID_'):
                self.id_map[getattr(pyraknet.PacketTypes, t)] = t
    def packet_type_info(self, packet_type_id):
        return self.id_map[packet_type_id]
    def connect(self, host, port):
        self.net.init(peers=1, thread_sleep_timer=10)
        self.net.connect(host=host, port=port)
    def listen(self, port, connection_handler):
        self.net.init(peers=8, port=port, thread_sleep_timer=10)
        self.net.set_max_connections(8)
        self.connection_handler = connection_handler
    def send(self, data, id=-1, broadcast=False):
        if id >= 0:
            address = self.net.get_address_from_id(id)
        elif broadcast:
            address = pyraknet.PlayerAddress()
        self.net.send(data, len(data), pyraknet.PacketPriority.LOW_PRIORITY, pyraknet.PacketReliability.RELIABLE_ORDERED, 0, address, broadcast)
    def poll(self, packet_handler):
        packet = self.net.receive()
        while packet:
            packet_handler(packet)
            packet = self.net.receive()
        
        
