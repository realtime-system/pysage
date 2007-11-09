import logging
from lib.network import *

class CreateGameObjectMessage(Packet):
#    '''Message used to create objects, currently used to create the players'''
    _id = 100
    _LOG_LEVEL = logging.INFO
    properties =  ['gameObjectType']
    _types = ('p',)
    
class TestSystem(object):
    def test_simple(self):
        msg = CreateGameObjectMessage(gameObjectType='dummy')
        
        