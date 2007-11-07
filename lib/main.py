import subprocess
import sys

# if i'm the main process, then i will spawn a defined number of subprocesses
if len(sys.argv) == 1:
    p1 = subprocess.Popen([sys.executable, sys.argv[0], 'render'])
    print 'created render process %s' % p1
    p2 = subprocess.Popen([sys.executable, sys.argv[0], 'physics'])
    print 'created physics process %s' % p2
    p1.wait()
    p2.wait()
    print 'finished main process'
# if i'm the child process, I have a name
else:
    print 'finished %s process' % sys.argv[1]




