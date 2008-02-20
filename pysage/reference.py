import time
import struct 

import pyraknet
from pyraknet import PacketTypes, PacketReliability, PacketPriority

class PeerBase(object):
        def loop(self):
                while not self.quit:
                        time.sleep(0.5)
                        packet = self.net.receive()
                        if packet:
                                self.handle_packet(packet)

class Client(PeerBase):
        def __init__(self):
                self.net = pyraknet.Peer()
                self.net.init(thread_sleep_timer=30)
                self.net.connect('localhost', 5555)
                self.quit = False
                print 'Connecting to server...'
        def handle_packet(self, packet):
                packet_type = ord(packet.data[0])
                if packet_type == PacketTypes.ID_CONNECTION_ATTEMPT_FAILED:
                        print 'Could not connect. Quitting...'
                        self.quit = True
                elif packet_type == PacketTypes.ID_CONNECTION_REQUEST_ACCEPTED:
                        print 'Connecetd to server!'
                elif packet_type == PacketTypes.ID_USER_PACKET_ENUM:
                        print 'Server told me to quit. Quitting...'
                        self.quit = True

class Server(PeerBase):
        def __init__(self):
                self.net = pyraknet.Peer()
                self.net.init(peers=10, port=5555, thread_sleep_timer=30)
                self.net.set_max_connections(10)
                self.quit = False
                print 'Waiting for a connection'
        def handle_packet(self, packet):
                packet_type = ord(packet.data[0])
                if packet_type == PacketTypes.ID_NEW_INCOMING_CONNECTION:
                        print 'A client just connected. Sending a quit order.'
                        data = struct.pack('B', PacketTypes.ID_USER_PACKET_ENUM)
                        self.net.send(data, len(data), PacketPriority.MEDIUM_PRIORITY, PacketReliability.RELIABLE, 0, packet.address)
                
if __name__ == '__main__':
        what = raw_input('(C)lient or (S)erver? ')
        if what[0] == 'C' or what[0] == 'c':
                me = Client()
        else:
                me = Server()
        me.loop()
        
        