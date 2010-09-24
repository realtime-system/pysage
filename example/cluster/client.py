# client.py
from pysage import *
from pysage import transport
from common import *
import time

class Slave(Actor):
    subscriptions = ['WorkRequestMessage']
    def handle_WorkRequestMessage(self, msg):
        mgr.broadcast_message(WorkFinishedMessage(result=sum(msg.get_property('numbers'))))
        return True

if __name__ == '__main__':
    mgr = ActorManager.get_singleton()
    mgr.register_actor(Slave())
    mgr.connect('localhost', 8000, transport.SelectTCPTransport)
    mgr.broadcast_message(RegisterSlaveMessage(cores=2))
    
    while True:
        time.sleep(.33)
        mgr.tick()


