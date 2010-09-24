# server.py
from pysage import *

class RegisterSlaveMessage(Message):
    '''a message a slave sends to the server that it's ready for work'''
    properties = ['cores']
    types = ['i']
    packet_type = 101

class WorkRequestMessage(Message):
    '''server gives slave some work'''
    properties = ['numbers']
    types = ['ai']
    packet_type = 102

class WorkFinishedMessage(Message):
    '''slave tells server it's done the work''' 
    properties = ['result']
    types = ['i']
    packet_type = 103

    

