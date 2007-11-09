# test_raknet.py
import sys, os
pth = os.getcwd()
if pth not in sys.path:
    sys.path.append(pth)
    
import time
from lib.network import *
    
class TestNetwork(object):
    def test_main(self):
        def incoming_connection(packet, server):
            print 'incoming connection from address: %s' % packet.address
            print 'incoming connection player: %s' % packet.player
            print 'incoming connection from address string: %s' % s.rn.get_address_string(packet.address)
        def incoming_test_packet(packet):
            print 'incoming packet length: %s' % len(packet.data)

        s = Network()
        s.set_callback(pyraknet.PacketTypes.ID_NEW_INCOMING_CONNECTION, lambda packet, server=s: incoming_connection(packet, server))
        s.set_callback(100, incoming_test_packet)
        help(s.listen)
        s.listen(port=8000, max_players=8)
        count = 5
        c = {}
        for i in range(count):
            c[i] = Network()
            c[i].connect(host='localhost', port=8000)
        while 1:
            time.sleep(0.1)
            s.poll()
            data = '%c%s' % (100,  'a' * 1024*1024)
            for i in range(count):
                c[i].poll()
                c[i].send(data, broadcast=True)    
