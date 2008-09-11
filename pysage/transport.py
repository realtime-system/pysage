# transport.py
import pyraknet

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
    def add_handler(self, packet_type, handler):
        '''registers a packet_type with a handler callable'''
        pass
    def remove_handler(self, packet_type):
        '''removes handler for a specific packet type'''
        pass
        

class RakNetTransport(Transport):
    pass