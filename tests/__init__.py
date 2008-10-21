import sys
import os
import logging
import multiprocessing

multiprocessing.get_logger().addHandler(logging.StreamHandler())
multiprocessing.get_logger().setLevel(logging.INFO)

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
