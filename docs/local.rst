Messaging Locally
*******************

This is the documentation for Pysage, a lightweight high-level message passing library supporting actor based concurrency.
Pysage is written in Python.  It supports **Python 2.5** and up.

Introduction
============

Step by step example
--------------------

Let's take a look at the code from the front page.  We'll go over this line by line to give you an in-depth idea what pysage is doing for you.
Here is the code:
::

    import time
    from pysage import Actor, ActorManager, Message
    
    mgr = ActorManager.get_singleton()
    
    class BombMessage(Message):
        properties = ['damage']
    
    class Player(Actor):
        subscriptions = ['BombMessage']
        def handle_BombMessage(self, msg):
            print 'I took %s damage from the bomb' % msg.get_property('damage')
    
    mgr.register_actor(Player(), 'player1')
    mgr.queue_message(BombMessage(damage=10))
    
    while True:
        processed = mgr.tick()
        time.sleep(.03)

First of all, import time to be able to "sleep" :)
::

    import time

Here, we import pysage base classes:
::

    from pysage import Actor, ActorManager, Message

Next, we will get a reference to the actor manager.  Per os process (pysage group), you are guaranteed a single instance of the actor manager.  

The manager instance does all the book-keeping with actors, messages, and communication across processes/networks, so that you don't have to worry about it.  

We will use it to send messages, and manage actors.  However, you will find out in later chapters that the actor manager will also assist you with managing pysage groups and networks.

::

    mgr = ActorManager.get_singleton()

To create a message type, define a class that inherits from ``Message``.  The ``properties`` class variable must be defined and is a list of strings.  The list will contain a set of attributes that this type of message will carry. 
::

    class BombMessage(Message):
        properties = ['damage']

To create an actor class, define a class that inherits from ``Actor``.  The ``subscriptions`` class variable of an actor is a list of message type names that the actor will subscribe to.  In our example, the "Player" actor will listen to ``BombMessage`` which we defined above.

Additionally, you need to specify what behavior your actor will perform when the message is received.  For each of these message types, the actor class needs to define a method that starts with ``handle_``, and appended with the message type name.  Again, in our example, we will define a method named ``handle_BombMessage`` to print out something about the bomb.  This method will be called when a ``BombMessage`` is delivered to the actor by pysage.
::

    class Player(Actor):
        subscriptions = ['BombMessage']
        def handle_BombMessage(self, msg):
            print 'I took %s damage from the bomb' % msg.get_property('damage')

When you are ready to create an actor instance and have the actor start listening to messages that it subscribes to, call ``register_actor`` on the manager. 
::

    >>> mgr.register_actor(Player(), 'player1')
    <__main__.Player object at 0x7fa91183a2d0>

You can optionally give it a name so that you can "find" it later by its name:
::

    >>> mgr.find('player1')
    <__main__.Player object at 0x7fa91183a2d0>

``queue_message`` queues an instance of a message in the manager's internal queue to be distributed when the manager ``tick``s.  This facilitates an asynchronous call because the message is only distributed later when manager's ``tick`` is called.
::

    mgr.queue_message(BombMessage(damage=10))

``tick`` method first distributes messages to actors, then call the actor's ``update`` method according to their ``priorities``, which we will discuss later.
::

    while True:
        processed = mgr.tick()
        time.sleep(.03)

the above code runs the game loop, and ``tick"s` roughly 30 times/second.  However, you may call "mgr.tick" however often to suit your own need.  This concludes our simple example.  To make this more interesting, you may want to add more actors/behaviors.  You may also define the ``update`` method on the ``Player`` actor to do something at every game step.  We will talk about ``update`` and ``tick`` in a bit.

Advanced
==========

Synchronous Messaging
-----------------------
``trigger`` is the synchronous version of the ``queue_message`` call, it processes the supplied message immediately and does not wait for the actor manager's ``tick``
::

    >>> mgr.register_actor(Player(), 'player1')
    >>> mgr.trigger(BombMessage(damage=10)) 
    actor prints that it received the message

Selective Queuing/Triggering
-----------------------------
At times, you may find that you want to "queue" or "trigger" a message to a specific actor and bypass broadcasting the message to all its subscribers.  You may do so with ``queue_message_to_actor`` or ``trigger_to_actor``.
::
    
    >>> mgr.register_actor(Player(), 'player1')

    >>> actor_id = mgr.find('player1').gid

Each registered actor has an attribute ``gid``, it is a unique id for that actor in the process that the actor belongs to.  Both ``queue_message_to_actor`` and ``trigger_to_actor`` take the actor's ``gid``:
::

    >>> mgr.queue_message_to_actor(actor_id, BombMessage(damage=10))
    >>> mgr.tick()
    actor prints that it received the message

    >>> mgr.trigger_to_actor(actor_id, BombMessage(damage=10))
    actor prints that it received the message

Actor's Update each tick
------------------------------------
There is also the ``update`` method that is built-in to pysage "Actor" base class.  This method will be called each time the actor manager "ticks".  



