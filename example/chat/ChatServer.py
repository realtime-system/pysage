# example made by Afan Olovcic afanolovcic@gmail.com
# in real life for chat is better to use transport.SelectTCPTransport with UDP some message can be undelivered
# ChatServer.py

from pysage import *
from pysage import transport
from packetType import *
import time, random

mgr = ActorManager.get_singleton()

class ChatMessageHandler(Actor):
    subscriptions = ['rcvChatMessage', 'conMessage', 'errMesage']
    def __init__(self):
        self.slaves = {}
        
    def handle_rcvChatMessage(self, msg):
        print '* %s>> %s' % (str(msg.sender),msg.get_property('msg'))
        sNick=self.slaves[msg.sender]
        slave_addrs = self.slaves.keys()
        for addrs in  slave_addrs:
            #We don't want to send message to our self
            if addrs!=msg.sender:
                mgr.send_message(rcvChatMessage(nick=sNick, msg=msg.get_property('msg')), addrs)
        return True
    
    def handle_conMessage(self, msg):
        print '* got a new slave from %s Nick: %s' % (str(msg.sender), msg.get_property('nick'))
        self.slaves[msg.sender] = msg.get_property('nick')
        slave_addrs = self.slaves.keys()
        for addrs in  slave_addrs:
            mgr.send_message(srvConMessage(id=0,nick=msg.get_property('nick')), addrs)
        return True
    
    def handle_errMesage(self, e):
        print '* client %s send an Error Message ErrorNumber: %s' % (str(e.sender), e.get_property('err'))
        return True
    
if __name__ == '__main__':
    mgr.listen('localhost', 8000, transport.SelectUDPTransport)#transport.SelectTCPTransport 
    mgr.register_actor(ChatMessageHandler())

    while True:
        time.sleep(.33)
        mgr.tick()