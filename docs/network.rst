Messages Across a Network
============================

This section describes how to send message across a network

Network Messages
------------------

Network messages can automatically pack and unpack themselves for purposes of being transported via UDP across the network.  "types" class variable needs to be defined for each message that is intended for network use.
::

    class SmallMessage(Message):
        properties = ['content']
        types = ['p']
        packet_type = 103
    
    mgr.queue_message(SmallMessage(content="hello world"))
    
    class LargeMessage(Message):
        properties = ['account_numbers']
        types = ['ai']
        packet_type = 104
    
    mgr.queue_message(LargeMessage(account_numbers=[100,101,102,109]))

besides all the format types supported by python's "struct" module, additional ones are supported by pysage:

=======  ===================================================
Type     Description
=======  ===================================================
"an"     array of arbitrary length of type "n"
"S"      a long string of arbitrary size, bigger than 255
=======  ===================================================

Builtin Server
-----------------
There are several builtin transports that come with pysage.  Server uses a select UDP transport by default.  To start listening:
::

    mgr.listen('localhost', 5000) # listening on localhost, and is bound to port 5000

Alternatively, you can have the server listen on an auto-gened port:
::

    mgr.listen('localhost', 0) # server will find an available port and listens on that
    host, port = nmanager.transport.address # this will return the port that the server is now bound to

On the client side, use "send_message" to talk to the server:
::

    mgr.send_message(ACKMessage(), address=('localhost', msg.get_property('port')))



