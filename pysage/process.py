# processing.py
import logging

processing = None
connection = None

try:
    import processing as processing
    import processing.connection as connection
except ImportError:
    pass
else:
    def send_bytes(conn, data):
        return conn.sendbytes(data)
    def recv_bytes(conn):
        return conn.recvbytes()
    def get_pid(p):
        return p.getPid()
    def is_alive(p):
        return p.isAlive()
    enable_groups = processing.freezeSupport
    processing.enableLogging(level=logging.INFO)
    get_logger = processing.getLogger
    current_process = processing.currentProcess

try:
    import multiprocessing as processing
    import multiprocessing.connection as connection
except ImportError:
    pass
else:
    def send_bytes(conn, data):
        return conn.send_bytes(data)
    def recv_bytes(conn):
        return conn.recv_bytes()
    def get_pid(p):
        return p.pid
    def is_alive(p):
        return p.is_alive()
    enable_groups = processing.freeze_support
    get_logger = processing.get_logger
    current_process = processing.current_process

if not processing:
    raise Exception('pysage requires either python2.6 or the "processing" module')

if not connection:
    raise Exception('pysage requires either python2.6 or the "processing" module')

Value = processing.Value
Process = processing.Process




