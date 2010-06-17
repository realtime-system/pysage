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
Let's go through an example:

Here we are creating a message that will get delivered across processes:

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
            print 'Yummy! I had % pancakes!' % (msg.get_property('amount'))

Pretty straight-forward.  The consumer gets a ``FoodAvailableMessage`` and prints out that he enjoys the "amount" number of pancakes given to him.

Now, let's look at making a "chef" actor that will make the food for our hungry fellow:

::

    import time

    class Chef(Actor):
        def __init__(self):
            self.last_sent = time.time()
        def update(self):
            '''every 2 seconds, this chef makes a random amount of pancakes'''
            if time.time() - self.last_sent > 2.0:
                mgr.queue_message_to_group(mgr.PYSAGE_MAIN_GROUP, SomeWorkDoneMessage())
                self.last_sent = time.time()

This chef actor is not subscribed to any messages.  Because he is so dedicated in making pancakes.

Now let's spawn some instances of these guys and see how they do.

::

    mgr.add_process_group('chefs', Chef)      # spawns a new process that "ticks" independently

This starts up a new pysage "group".  The "Chef" actor class is our default actor for the new group.  The group will automatically spawn a "Chef" actor once it's initialized itself.  Internally, calling "add_process_group" will start a separate OS process for the specified group that all actors that belong to that group will "run" in.  

In our current(main) group, we will create 1 consumer to eat the chef's cakes.  Yumm!!

::

    mgr.register_actor(Consumer())

Now we just need to create a loop and watch the show:
::

    while True:
        processed = mgr.tick()
        time.sleep(.03)

Questions?  Feel free to ask in our `mailing list <http://groups.google.com/group/pysage>`_.

