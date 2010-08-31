from pysage import *
from pysage import transport
import time

mgr = ActorManager.get_singleton()
mgr.listen('localhost', 24000, transport.SelectTCPTransport)

while 1:
	mgr.tick()
	time.sleep(.3)
