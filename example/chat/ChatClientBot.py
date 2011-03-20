# client.py
from pysage import *
from pysage import transport
from packetType import *

import time,random

buffer=[]

class ChatMessageHandler(Actor):
    def __init__(self):
        self._SYNC_PRIORITY = 1
        
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
    
        
if __name__ == '__main__':
    names = ["John","Afan","Adam","Glazner","Cosmin","Enrique","Bob","Jack"]
    items = ["It would seem easy to extend", "I've been googling for some time now", "for the struct module suggests that", "You might wan", "I love Python", "I love Pysage", "There may be"]
    name=names[random.randint(0,7)]
    #name=raw_input('Nick->')
    mgr = ActorManager.get_singleton()
    mgr.register_actor(ChatMessageHandler())
    mgr.connect('localhost', 8000, transport.SelectUDPTransport)
    mgr.broadcast_message(conMessage(nick=name))
    last_sent = time.time()
    nextTime=random.randint(1,5)
    
    while True:
        
        if time.time() - last_sent > nextTime:
            s=items[random.randint(0,6)]
            mgr.broadcast_message(rcvChatMessage(nick='', msg=s))
            nextTime=random.randint(4,10)
            last_sent = time.time()
        
        time.sleep(.33)
        mgr.tick()
