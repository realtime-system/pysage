import subprocess
import sys
import pyraknet
import time
from system import *
from network import *


class Test(Message):
    properties = ['name']
    pass

class Receiver(MessageReceiver):
    subscriptions = ['Test']
    def handle_Test(self, msg):
        # don't consume this message
        return False

# Server:
# if i'm the main process, then i will spawn a defined number of subprocesses
if len(sys.argv) == 1:
    # create the message manager for the main process
    system = System()
    system.startMainProcess(8000, 8)
    
    # spawn child processes
    p1 = subprocess.Popen([sys.executable, sys.argv[0], 'render'])
    print 'created render process %s' % p1
    p2 = subprocess.Popen([sys.executable, sys.argv[0], 'physics'])
    print 'created physics process %s' % p2
    
    # going into main process main loop
    while True:
        time.sleep(0.1)
        system.poll()

    print 'finished main process'
        
# Client:
# if i'm the child process, I have a name
else:
    # first create the client system
    system = System()
    system.startChildProcess('localhost', 8000, sys.argv[1])
    
    # then go into client main loop
    while True:
        time.sleep(0.1)
        system.poll()



