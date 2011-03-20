from pysage import *

class rcvChatMessage(Message):
    '''regular chat Message'''
    properties = ['nick', 'msg']
    types = ['p','p']
    packet_type = 101

class conMessage(Message):
    '''client connect to server and send nickName''' 
    properties = ['nick']
    types = ['p']
    packet_type = 102

class srvConMessage(Message):
    '''server send connection data to clients''' 
    properties = ['id','nick']
    types = ['i', 'p']
    packet_type = 103
    
class errMessage(Message):
    '''error Messages sending id of error''' 
    properties = ['err']
    types = ['i']
    packet_type = 104
    
class inputMsg(Message):
    '''client input Messages''' 
    properties = ['msg']
    types = ['p']
    packet_type = 105