# server.py
from pysage import *
from pysage import transport
from common import *
import time

mgr = ActorManager.get_singleton()

work = range(1000)

class TestMessageReceiver(Actor):
    subscriptions = ['RegisterSlaveMessage', 'WorkFinishedMessage']
    def __init__(self):
        self.slaves = {}
    def handle_RegisterSlaveMessage(self, msg):
        print '* got a new slave from %s' % str(msg.sender)
        self.slaves[msg.sender] = None
        if len(self.slaves) == 2:
            print '* got two slaves, now distributing work'
            slave_addrs = self.slaves.keys()
            mgr.send_message(WorkRequestMessage(numbers=work[:500]), slave_addrs[0])
            mgr.send_message(WorkRequestMessage(numbers=work[500:]), slave_addrs[1])
        return True
    def handle_WorkFinishedMessage(self, msg):
        print '* slave %s got done with his work: %s' % (str(msg.sender), msg.get_property('result'))
        self.slaves[msg.sender] = msg.get_property('result')

        values = self.slaves.values()
        if values[0] and values[1]:
            print '* work is all done, the final result is: %s' % (values[0] + values[1])
        return True
    
if __name__ == '__main__':
    mgr.listen('localhost', 8000, transport.SelectTCPTransport)
    mgr.register_actor(TestMessageReceiver())

    while True:
        time.sleep(.33)
        mgr.tick()

