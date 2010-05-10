# sample_multigroups.py
# 
# contributed by: Jay Herrmann
# edited by: Shuo (John) Yang
import sys
sys.path.insert(0, '.\\')


import time
from pysage import Actor, ActorManager, Message
from pysage.process import enable_groups

mgr = ActorManager.get_singleton()

class MainGroupMessage(Message):
    properties = ['TenSecCount','ThreeSecCount']
    types = ['i','i']
    packet_type = 101

class ThreeSecGroupMessage(Message):
    properties = []
    packet_type = 102

class TenSecGroupMessage(Message):
    properties = []
    packet_type = 103

class MainAction(Actor):
    subscriptions = ['MainGroupMessage']
    def __init__(self):
        Actor.__init__(self)
        self.TenSecCount = 0
        self.ThreeSecCount = 0
    def handle_MainGroupMessage(self, msg):
        if msg.get_property('TenSecCount') != 0 and msg.get_property('TenSecCount')!= self.TenSecCount:
            self.TenSecCount=msg.get_property('TenSecCount')
        if msg.get_property('ThreeSecCount') != 0 and msg.get_property('ThreeSecCount')!= self.ThreeSecCount:
            self.ThreeSecCount=msg.get_property('ThreeSecCount')
        print 'Ten Second Count %s -- Three Second Count %s' % (self.TenSecCount,self.ThreeSecCount)

class ThreeSecAction(Actor):
    subscriptions = ['ThreeSecGroupMessage']
    def __init__(self):
        Actor.__init__(self)
        self.Count=0
        self.startTime = time.time()
    def handle_ThreeSecGroupMessage(self, msg):
        self.Count=self.Count+1
        ActorManager.get_singleton().queue_message_to_group(ActorManager.get_singleton().PYSAGE_MAIN_GROUP,MainGroupMessage(ThreeSecCount=self.Count, TenSecCount=0))
    def update(self):
        if time.time() - self.startTime >= 3.0:
            ActorManager.get_singleton().queue_message(ThreeSecGroupMessage())
            self.startTime=time.time()

class TenSecAction(Actor):
    subscriptions = ['TenSecGroupMessage']
    def __init__(self):
        Actor.__init__(self)
        self.Count=0
        self.startTime = time.time()
    def handle_TenSecGroupMessage(self, msg):
        self.Count=self.Count+1
        ActorManager.get_singleton().queue_message_to_group(ActorManager.get_singleton().PYSAGE_MAIN_GROUP,MainGroupMessage(TenSecCount=self.Count, ThreeSecCount=0))
    def update(self):
        if time.time() - self.startTime >= 10.0:
            ActorManager.get_singleton().queue_message(TenSecGroupMessage())
            self.startTime=time.time()

if __name__ == '__main__':
    # note VERY IMPORT TO HAVE THE FOLLOWING THREE LINES UNDER __NAME__ == __MAIN__, ADD TO DOCUMENTATION
    enable_groups()
    mgr.register_actor(MainAction())
    mgr.add_process_group('ThreeSecGroup',ThreeSecAction)
    mgr.add_process_group('TenSecGroup',TenSecAction)
    while True:
        # TODO: make this mandatory for groups usage
        processed = ActorManager.get_singleton().tick()
        time.sleep(.03) 
    
    
    