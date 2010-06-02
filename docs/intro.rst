Introduction
============

This is the documentation for Pysage, a lightweight high-level message passing library supporting actor based concurrency.
Pysage is written in Python.  It supports **Python 2.5** and up.

Basics
---------

Let's take a look at the code from the front page.  We'll go over this line by line to give you an in-depth idea what pysage is doing for you.
Here is the code:
::

    import time
    from pysage import Actor, ActorManager, Message
    
    mgr = ActorManager.get_singleton()
    
    class BombMessage(Message):
        properties = ['damage']
        packet_type = 101
    
    class Player(Actor):
        subscriptions = ['BombMessage']
        def handle_BombMessage(self, msg):
            print 'I took %s damage from the bomb' % msg.get_property('damage')
    
    mgr.register_actor(Player(), 'player1')
    mgr.queue_message(BombMessage(damage=10))
    
    while True:
        processed = mgr.tick()
        time.sleep(.03)

import time to be able to "sleep" :)
::
    import time

Here, we import pysage base classes:
::

    from pysage import Actor, ActorManager, Message

Next, we will create the actor manager.  Per os process (pysage group), you are guaranteed a single instance of the actor manager.  

The manager instance does all the book-keeping with actors, messages, and communication across processes/networks, so that you don't have to worry about it.  

We will use it to send messages, and manage actors here.  You will find out in later chapters that the actor manager will also assist you with managing pysage groups and networks.

::

    mgr = ActorManager.get_singleton()

To create a message type, define a class that inherits from `"Message"`.  The `"properties"` class variable must be defined and is a list of strings.  The list will contain a set of attributes that this type of message will carry.  The "packet_type" is an integer between 101-255 that uniquely identifies this message type.  This will become especially useful when you need to send this message across groups or networks.
::

    class BombMessage(Message):
        properties = ['damage']
        packet_type = 101

To create an actor type, define a class that inherits from `"Actor"`.  The `"subscriptions"` class variable of an actor is a list of message type names that the actor will subscribe to.  In our example, the "Player" actor will listen to `"BombMessage"` which we defined above.

Additionally, you need to specify what behavior your actor will perform when the message is received.  For each of these message types, the actor class needs to define a method that starts with `"handle_"`, and appended with the message type name.  Again, in our example, we will define a method named `"handle_BombMessage"` to print out something about the bomb.  This method will be called when a `"BombMessage"` is delivered to the actor by pysage.

There is also the `"update"` method that is built-in to pysage "Actor" base class.  This method will be called each time the actor manager "ticks".  We will talk about `"update"` and `"tick"` in a bit.
::

    class Player(Actor):
        subscriptions = ['BombMessage']
        def handle_BombMessage(self, msg):
            print 'I took %s damage from the bomb' % msg.get_property('damage')

When you are ready to create an actor instance and have the actor start listening to messages that it subscribes to, call `"register_actor"` on the manager:
::

    mgr.register_actor(Player(), 'player1')

`"queue_message"` queues an instance of a message in the manager's internal queue to be distributed when the manager `"tick"`s.  This facilitates an asynchronous call because the message is only distributed later when manager's `"tick"` is called.
::

    mgr.queue_message(BombMessage(damage=10))

`"tick"` method first distributes messages to actors, then call the actor's `"update"` method according to their `"priorities"`, which we will discuss later.
::

    while True:
        processed = mgr.tick()
        time.sleep(.03)

the above code runs the game loop, and `"tick"s` roughly 30 times/second.  This concludes the simple game loop example.  To make this more interesting, you may want to define more behaviors on the message handler of the actor.  You may also define the `"update"` method on the `"Player"` actor to do something at every game step.

Sending Messages
-----------------

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

Other useful methods
--------------------
"trigger" is the synchronous version of the `"queue_message"` call, it processes the supplied message immediately and does not wait for the actor manager's `"tick"`
::

    mgr.trigger(BombMessage(damage=10)) # prints "the secret is small secret"

`"find"` returns back the instance of the registered actor with that name
::

    mgr.find('player1') # returns the registered actor instance

Selective Queuing/Triggering
----------------------------
sends a particular actor a message if that actor implements this message type
::

    mgr.trigger_to_actor(self, id, msg)
    mgr.queue_message_to_actor(self, id, msg)

Automatic Message Packing/Unpacking
------------------------------------
packing can be useful for sending messages across network.  This may prove to be useful in the future when pysage supports cross processing message queuing.
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



