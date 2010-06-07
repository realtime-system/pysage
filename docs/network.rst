Messaging across Network
***************************

This section describes how to send message across a network

Sending Messages
=================

For networked messages, first connect to the server.
::

    mgr.connect(host, port)

Pass in your message properties as keyword arguments to the constructor.
::

    mgr.send_message(MyMessage(content="1234"), address=(host, port))

This is how you can send a message to another pysage group:
::

    mgr.send_message_to_group("group_name", MyMessage(data='asdf'))

Pysage will automatically pack your message according to the types you give and send it via the default transport.  You can also build your own custom transport.

Messages can be sent through three different kinds of channels:

#. Local: messages are delivered to actors in the local process.  No serialization or deserialization is done on the message.  The message is delivered as is, a python object.

#. IPC: messages can be delivered to another pysage group.  Messages will be serialized and deserailized and sent over a platform specific channel (domain socket or a named pipe).

#. Network: messages will be serialized and deserialized.  The delivery depends on the network transport protocol chosen by the user.  (so far raknet is offered, raw TCP/UDP coming).

ActorManager class offers the following types of methods:

=========================  ======   =========   =======  ================================================================================================================================================================
Function                   Local    IPC         Network  Description
=========================  ======   =========   =======  ================================================================================================================================================================
`trigger`                  y        _           _        used to immediately process a message synchronously.  Returns after the message has been processed.
`queue_message`            y        _           _        puts the message on a queue.  Returns immediately.  Message will be processed next time "tick" is called locally
`queue_message_to_group`   _        y           _        immediately delivers the message to another pysage group via IPC.  It is up to the called group to process the message
`send_message`             _        _           y        immediately delivers the message to another pysage compatible node via a chosen protocol transport.  It's up to the called node to process the message 
=========================  ======   =========   =======  ================================================================================================================================================================

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

Automatic Message Packing/Unpacking
------------------------------------
packing can be useful for sending messages across network/process.  Pysage internally packs messages into C structs and sends them in a packet when messaging across network/process.  Complex types that are not otherwise packable need to get processed and decomposed down to simple C types.  ``pack_xxx`` and ``unpack_xxx`` let you implement serialization behaviour.
::

    class MessageToPack(Message):
        properties = ['number']
        packet_type = 101
        def pack_number(self, value):
            return (value.x, value.y)
        def unpack_number(self, value):
            return vector2(value[0], value[1])

now this message will automatically be stored as a tuple (1,2)
upon accessing, it will be converted to a vector object transparently
::

    mgr.queue_message(MessageToPack(number=vector2(1,2)))

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



