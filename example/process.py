import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
# import multiprocessing
# import multiprocessing.connection
# import time
# 
# def run(address):
#     c = multiprocessing.connection.Client(address)
#     print c
#     while True:
#         print 'hi'
#         time.sleep(3)
#         
# if __name__ == '__main__':
#     c = multiprocessing.connection.Listener()
#     p1 = multiprocessing.Process(target=run, args=(c.address,))
#     p2 = multiprocessing.Process(target=run, args=(c.address,))
    
import multiprocessing, logging
multiprocessing.get_logger().addHandler(logging.StreamHandler())
multiprocessing.get_logger().setLevel(logging.INFO)
from pysage import network  
mgr = network.NetworkManager.get_singleton()

    
