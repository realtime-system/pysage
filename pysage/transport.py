# transport.py
import process as processing
import socket
import select
import warnings
import struct
import time
import os

try:
    import pyraknet
except ImportError:
    RAKNET_AVAILABLE = False
else:
    RAKNET_AVAILABLE = True
    
logger = processing.get_logger()

class Transport(object):
    '''an interface that all transports must implement'''
    def connect(self, host, port):
        '''connects to a server implementing the same interface'''
        pass
    def disconnect(self):
        '''disconnects all clients and itself'''
        pass
    def listen(self, host, port, connection_handler):
        '''listens for connections, and calls connection_handler upon new connections'''
        pass
    def send(self, data, address=None, broadcast=False):
        '''send data to another transport specified by address'''
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
    
class RawPacket(object):
    def __init__(self, data):
        self.data = data

class SelectUDPTransport(Transport):
    def __init__(self):
        self.socket = None
        self.peers = {}
        self._is_connected = False
    def listen(self, host, port, connection_handler=None):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking(False)
        self.socket.bind((host, port))
        # listen is not needed for UDP socket since it's a connectionless protocol
        # self.socket.listen(5)
    def poll(self, packet_handler):
        processed = False
        inputready, outputready, exceptready = select.select([self.socket.fileno()], [], [], 0)
        for fd in inputready:
            if fd == self.socket.fileno():
                # UDP is connectionless, therefore no accept calls
                packet, address = self.socket.recvfrom(65536)
                if not address in self.peers:
                    self.peers[address] = None
                packet_handler(packet, address)
                processed = True
        return processed
    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking(False)
        self.socket.connect((host, port))
        self._is_connected = True
    def disconnect(self):
        self.socket.close()
    def send(self, data, address=None, broadcast=False):
        if address:
            sent = 0
            while sent != len(data):
                sent = self.socket.sendto(data, address)
        elif self._is_connected:
            # if we are the client, just send it to the server
            sent = 0
            while sent != len(data):
                sent = self.socket.send(data)
        elif broadcast:
            for addr in self.peers.keys():
                sent = 0
                while sent != len(data):
                    sent = self.socket.sendto(data, addr)
    @property
    def address(self):
        return self.socket.getsockname()

class SelectTCPTransport(Transport):
    def __init__(self):
        self.socket = None
        self.peers = [] 
        self.addrs = {}
        self.buffer = {}
        self._is_connected = False
        self.outgoing_queue = []
        self.incoming_queue = []
    def listen(self, host, port, connection_handler=None):
        logger.info("pid %s listening..." % os.getpid())
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(False)
        self.socket.bind((host, port))
        self.socket.listen(5)
    def process_received_data(self, sock, data, packet_handler):
        buf, length = self.buffer[sock]
        
        buf = buf + data
        size = struct.calcsize("!L")
        
        # if length isn't defined, we'll see if we have enough to define it
        if not length:
            if len(buf) >= size:
                length = struct.unpack("!L", buf[:size])[0]
        
        # if length is defined, we've decoded the message length already
        if length:
            # if we've got the complete message, then handle it and remove it from the buffer
            if len(buf) >= (length + size):
                packet_handler(buf[size:length+size], sock.getsockname())
                buf = buf[length + size:]
                length = None
                pass
            # if we haven't gotten the complete message, just hang tight
        self.buffer[sock] = (buf, length)
    def remove_socket(self, sock):
        self.addrs = dict(addr for addr in self.addrs.items() if not addr[1] == sock)
        if sock in self.peers:
            self.peers.remove(sock)
        if sock in self.buffer:
            del self.buffer[sock]
    def poll(self, packet_handler):
        logger.warning('pid %s polling...%s' % (os.getpid(), time.time()))
        processed = False
        try:
            inputready, outputready, exceptready = select.select([self.socket] + self.peers, [], [], 0)
        except select.error, e:
            warnings.warn('Error with network select: %s' % e)
            return processed
        except socket.error, e:
            warnings.warn('Error with network select: %s' % e)
            return processed
        
        for sock in inputready:
            if not self._is_connected and sock == self.socket:
                logger.info('%s accepting...' % ('Client' if self._is_connected else 'Server'))
                # if server socket is readable, we are ready to accept
                clientsock, address = self.socket.accept()
                logger.info('accepted %s' % str(address))
                if not address in self.addrs:
                    self.addrs[address] = clientsock
                if not clientsock in self.peers:
                    self.peers.append(clientsock)
                    self.buffer[clientsock] = ('', None)
            else:
                logger.info('pid %s receiving from %s...' % (os.getpid(), sock.getsockname()))
                # otherwise, we have some data to read from outside
                try:
                    data = sock.recv(1024)
                    if data:
                        self.process_received_data(sock, data, packet_handler)
                    else:
                        # client closed connection, they are done sending the message
                        sock.close()
                        self.remove_socket(sock)
                except socket.error, e:
                    warnings.warn('%s Error receiving data: %s' % ('Client' if self._is_connected else 'Server', e))
                    self.remove_socket(sock)
            processed = True
        return processed
    def connect(self, host, port):
        logger.info("pid %s Connecting to %s,%s" % (os.getpid(), host, port))
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.socket.setblocking(False)
        self._is_connected = True
    def disconnect(self):
        self.socket.close()
    def send(self, data, address=None, broadcast=False):
        logger.warning('pid %s sending...%s' % (os.getpid(), time.time()))
        data = struct.pack("!L",len(data)) + data
        sock = None
        if address:
            logger.info(str(self.addrs))
            sock = self.addrs[address]
        if sock:
            sock.sendall(data)
        elif self._is_connected:
            # if we are the client, just send it to the server
            self.socket.sendall(data)
        elif broadcast:
            for s in self.peers:
                s.sendall(data)
    @property
    def address(self):
        return self.socket.getsockname()
        
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
        '''returns True if transport processed any packet at all'''
        processed = False
        for address, conn in self.peers.items():
            if conn.poll():
                packet = processing.recv_bytes(conn)
                packet_handler(packet, address)
                processed = True
        return processed

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
        processed = False
        packet = self.net.receive()
        if packet:
            packet_handler(packet)
            processed = True
        return processed
        
#class PollUDPTransport(Transport):
#    def __init__(self):
#        # polling object to poll for network events
#        self.p = select.poll()
#        self.socket = None
#        self.connections = {}
#    def listen(self, host, port):
#        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#        self.socket.setblocking(False)
#        self.socket.bind((host, port))
#        # listen is not needed for UDP socket since it's a connectionless protocol
#        # self.socket.listen(5)
#        self.p.register(self.socket)
#    def poll(self, packet_handler):
#        processed = False
#        events = self.p.poll(0)
#        for fd, event in events:
#            # if server socket has events, it's got a connection
#            if fd == self.socket.fileno():
#                conn, addr = self.socket.accept()
#                conn.setblocking(False)
#                self.p.register(conn)
#                self.connections[conn.fileno()] = conn
#            elif event & select.POLLIN:
#                conn = self.connections[fd]
#                packet = RawPacket(conn.recv(64000))
#                packet_handler(packet)
#        return processed
#    def connect(self, host, port):
#        pass
#    def send(self):
#        pass
#    @property
#    def address(self):
#        return self.socket.getsockname()

        
