FAQ
============================

How do I create a actor manager?
--------------------------------
::

    # actor manager is a singleton class.  Per process, there is ever only one manager instance.
    # you can access it via:
    manager = ActorManager.get_singleton()


What to call to propogate messages and call actor.update(...)?
----------------------------------------------------------------
::

    manager.tick(...)

What is the "subscriptions" actor class variable for?
----------------------------------------------------------------
::

    # it is used to denote what kind of messages this actor is subscribed to.  
    # The name in this list needs to match the Message class name for which the actor is subscribing to.
    class SimpleMessage(Message):
        pass
    
    class SimpleActor(Actor):
        subscriptions = ['SimpleMessage']
    
How to implement a message handler for the subscribed message types?
-----------------------------------------------------------------------
::

    # implement a method for the actor named "handle_MessageType".  I.E.:
    class SimpleActor(Actor):
        subscriptions = ['SimpleMessage']
        def handle_SimpleMessage(self, msg):
            pass




