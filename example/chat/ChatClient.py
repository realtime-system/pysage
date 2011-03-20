# example made by Afan Olovcic afanolovcic@gmail.com
# ChatClient.py
 
from pysage import *
from pysage import transport
from packetType import *
from thread import *
import time,random

buffer=[]

class ChatMessageHandler(Actor):
    def __init__(self):
        self._SYNC_PRIORITY = 1
        t = start_new_thread(self.InputLoop, ())
    subscriptions = ['rcvChatMessage', 'srvConMessage','errMesage']
    def handle_rcvChatMessage(self, msg):
        print '%s>> %s'%(msg.get_property('nick'),msg.get_property('msg'))
        return True
    
    def handle_srvConMessage(self,msg):
        print '%s Conect to Server' % msg.get_property('nick')
        return True
    
    def handle_errMesage(self, e):
        print '* client %s send an Error Message ErrorNumber: %s' % (str(e.sender), e.get_property('err'))
        return True
    def InputLoop(self):
        # horrid threaded input loop
        # continually reads from stdin and sends whatever is typed to the server
        while 1:
            txt=raw_input()
            mgr.broadcast_message(rcvChatMessage(nick='', msg=txt))
        
if __name__ == '__main__':
    #input NickName
    name=raw_input('Nick->')
    mgr = ActorManager.get_singleton()
    mgr.register_actor(ChatMessageHandler())
    mgr.connect('localhost', 8000, transport.SelectUDPTransport)
    mgr.broadcast_message(conMessage(nick=name))
    last_sent = time.time()
    
    while True:
        
        time.sleep(.33)
        mgr.tick()
