import subprocess
import sys
import pyraknet
import time
from network import *

SERVER_PORT = 1000

# Server:
# if i'm the main process, then i will spawn a defined number of subprocesses
if len(sys.argv) == 1:
    # first create the network server in the main process
    def incoming_connection(packet, s):
        print 'incoming connection from address: %s' % packet.address
        print 'incoming connection player: %s' % packet.player
        print 'incoming connection from address string: %s' % s.rn.get_address_string(packet.address)
    def incoming_test_packet(packet):
        print 'incoming packet length: %s' % len(packet.data)

    s = Network()
    s.set_callback(pyraknet.PacketTypes.ID_NEW_INCOMING_CONNECTION, lambda packet, server=s: incoming_connection(packet, server))
    s.set_callback(100, incoming_test_packet)
    s.listen(port=SERVER_PORT, max_players=8)
    
    p1 = subprocess.Popen([sys.executable, sys.argv[0], 'render'])
    print 'created render process %s' % p1
    p2 = subprocess.Popen([sys.executable, sys.argv[0], 'physics'])
    print 'created physics process %s' % p2
    
    # going into main process main loop
    while True:
        time.sleep(0.1)
        s.poll()

    print 'finished main process'
        
# Client:
# if i'm the child process, I have a name
else:
    # first create the client network
    c = Network()
    c.connect(host='localhost', port=SERVER_PORT)
    
    # then go into client main loop
    while True:
        time.sleep(0.1)
        c.poll()
    
    print 'finished %s process' % sys.argv[1]



