# system.py
# implements a distributed system that uses the messaging functionality
# and is responsible for local message propagation as well as network messages propagation
from messaging import *
from network import *

class System(MessageManager):
    def init(self):
        # let the parent message manager init first
        MessageManager.init(self)
        self.network = Network()
        self.network.set_callback(pyraknet.PacketTypes.ID_NEW_INCOMING_CONNECTION, self.incoming_connection)
        self.network.set_callback(100, self.incoming_test_packet)
        # give a name
        self._system_name = ''
    def incoming_connection(self, packet):
        print 'incoming connection from address: %s' % packet.address
        print 'incoming connection player: %s' % packet.player
        print 'incoming connection from address string: %s' % self.network.rn.get_address_string(packet.address)
    def incoming_test_packet(self, packet):
        print 'incoming packet length: %s' % len(packet.data)
    def startMainProcess(self, port, max):
        '''starts the system in main process mode
            this will make the system act like a "server"
            return: true if success
        '''
        self.network.listen(port=port, max_players=max)
        self._system_name = 'Main'
        return True
    def startChildProcess(self, host, port, name):
        '''starts the system in child process mode
            child needs to have a unque name specified
            return: true if success
        '''
        self.network.connect(host=host, port=port)
        self._system_name = name
        return True
    def poll(self):
        '''a combined tick for the system
            this should be called as the main loop for each of the process (group) that is created
            return: true if success
        '''
        # first poll the network for messages
        self.network.poll()
        # then, tick the internal messaging engine
        self.tick()
        return True
    
    
