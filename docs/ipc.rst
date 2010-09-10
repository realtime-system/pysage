Messaging across Processes
****************************

This section describes Pysage's "Grouping" functionality.

Basics
================
Grouping can be very useful in partitioning actors into separate processes.  Actors in the same group are local to each other, so they can have access to each other.  It's kind of like a: "what happens in the group, stays in the group" concept.  Although, using messages are strongly encouraged instead of straight calls for most situations, even in the same pysage group.  Actors in different groups have their own independent update/message handling loop.  And messages can be communicated across groups via IPC.  

Unlike messages that are sent locally within a process, messages sent across pysage ``groups`` get internally serialized and requires a ``packet_type``.

A "packet_type" is an integer between "101-255" that uniquely identifies this message type.  This is required when you need to send a message across groups or networks.
 
Example
--------------------
::

    from pysage import *
    
    class FoodAvailableMessage(Message):
        properties = ['amount']
        types = ['i']
        packet_type = 101
    
    class Consumer(Actor):
        subscriptions = ['FoodAvailableMessage']
        def handle_FoodAvailableMessage(self, msg):
            print 'Yummy! I had %d pancakes!' % (msg.get_property('amount'))
    
    import time, random
    
    class Chef(Actor):
        def __init__(self):
            self.last_sent = time.time()
        def update(self):
            '''every 2 seconds, this chef makes a random amount of pancakes'''
            if time.time() - self.last_sent > 2.0:
                mgr.queue_message_to_group(mgr.PYSAGE_MAIN_GROUP, FoodAvailableMessage(amount=random.randint(0,10)))
                self.last_sent = time.time()
    
    mgr = ActorManager.get_singleton()
    mgr.register_actor(Consumer())
    
    if __name__ == '__main__':
        mgr.enable_groups()
        mgr.add_process_group('chefs', Chef)      # spawns a new process that "ticks" independently
        while True:
            processed = mgr.tick()
            time.sleep(.03)

Let's go through this example line by line:

Here we are creating a message that will get delivered across processes:

::

    from pysage import *

The usual "imports" from pysage.

::

    class FoodAvailableMessage(Message):
        properties = ['amount']
        types = ['i']
        packet_type = 101

The message has an ``amount`` of ``int`` as its only property.  We define this to be packet type "101".  This message will get delivered from our new "chefs" Group to the main group.  Under the covers, this message gets "IPC" delivered from a child OS process to the main process.

Below, let's define our consumer that will "eat" the food given to him.  This actor will later reside in our main group.

::

    class Consumer(Actor):
        subscriptions = ['FoodAvailableMessage']
        def handle_FoodAvailableMessage(self, msg):
            print 'Yummy! I had %d pancakes!' % (msg.get_property('amount'))

Pretty straight-forward.  The consumer gets a ``FoodAvailableMessage`` and prints out that he enjoys the "amount" number of pancakes given to him.

Now, let's look at making a "chef" actor that will make the food for our hungry fellow:

::

    import time, random

    class Chef(Actor):
        def __init__(self):
            self.last_sent = time.time()
        def update(self):
            '''every 2 seconds, this chef makes a random amount of pancakes'''
            if time.time() - self.last_sent > 2.0:
                mgr.queue_message_to_group(mgr.PYSAGE_MAIN_GROUP, FoodAvailableMessage(amount=random.randint(1,10)))
                self.last_sent = time.time()

This chef actor is not subscribed to any messages because he is so dedicated in making pancakes.  He will make between 1 to 10 pancakes at once and let the consumer know.

Below, in our current(main) group, we will create 1 consumer to eat the chef's cakes.  Yumm!!
::

    mgr = ActorManager.get_singleton()
    mgr.register_actor(Consumer())


Now we just need to create a pysage group to spawn some "chefs" and watch the show:
::

    if __name__ == '__main__':
        mgr.enable_groups()
        mgr.add_process_group('chefs', Chef)      # spawns a new process that "ticks" independently
        while True:
            processed = mgr.tick()
            time.sleep(.03)

``enable_groups`` call enables pysage grouping.  Internally, it does some bookkeeping to get ready for IPC.

The ``add_process_group`` calls starts up a new pysage group called ``chefs``.  The "Chef" actor class is our default actor in this new group.  The group will automatically spawn a "Chef" actor once it's initialized itself.  Internally, calling ``add_process_group`` will spawn a child OS process for the specified group that all actors that belong to that group will reside.

**IMPORTANT**: You need to make sure that calls to ``enable_groups`` and ``add_process_group`` are within the ``if __name__ == '__main__'`` scope.  This ensures that on windows systems you won't have a loop spawning processes endlessly.

Questions?  Feel free to ask in our `mailing list <http://groups.google.com/group/pysage>`_.

Another Example
--------------------
Here is an example of group messaging using custom packing/unpacking functions:
::

    from pysage import *
    import json
    import time, random
    
    class FoodAvailableMessage(Message):
        properties = ['food']
        types = ['S']
        packet_type = 101 
        def pack_food(self, food):
            return json.dumps(food)
        def unpack_food(self, food_s):
            return json.loads(food_s)
    
    class Consumer(Actor):
        subscriptions = ['FoodAvailableMessage']
        def handle_FoodAvailableMessage(self, msg):
            print 'Yummy! I had %d %s pancakes!' % (msg.get_property('food')['amount'], msg.get_property('food')['color'])
    
    class Chef(Actor):
        def __init__(self):
            self.last_sent = time.time()
        def update(self):
            '''every 2 seconds, this chef makes a random amount of pancakes'''
            if time.time() - self.last_sent > 2.0:
                mgr.queue_message_to_group(mgr.PYSAGE_MAIN_GROUP, FoodAvailableMessage(food={'amount': random.randint(0,10), 'color': 'red'}))
                self.last_sent = time.time()
    
    mgr = ActorManager.get_singleton()
    mgr.register_actor(Consumer())
    
    if __name__ == '__main__':
        mgr.enable_groups()
        mgr.add_process_group('chefs', Chef)      # spawns a new process that "ticks" independently
        while True:
            processed = mgr.tick()
            time.sleep(.03)


