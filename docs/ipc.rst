Messaging across Processes
****************************

This section describes Pysage's "Grouping" functionality.

Basics
---------------------------------
Grouping can be very useful in partitioning actors into separate processes.  Actors in the same group are local to each other, so they can have access to each other.  It's kind of like a: "what happens in the group, stays in the group" concept.  Although, using messages are strongly encouraged instead of straight calls for most situations, even in the same pysage group.  Actors in different groups have their own independent update/message handling loop.  And messages can be communicated across groups via IPC.  

The "packet_type" is an integer between 101-255 that uniquely identifies this message type.  This will become especially useful when you need to send this message across groups or networks.
 
::

    class Consumer(MessageReceiver):
        subscriptions = ['SomeWorkDoneMessage']
        packet_type = 102
        def handle_SomeWorkDoneMessage(self, msg):
            pass
    
    class Worker(Actor):
        subscriptions = ['NeedWorkDoneMessage']
        def handle_NeedWorkDoneMessage(self, msg):
            pass
        def update(self):
            '''this gets called in the "worker_group" process ticks'''
            # queues a message to the main group
            mgr.queue_message_to_group(mgr.PYSAGE_MAIN_GROUP, SomeWorkDoneMessage())

calling "add_process_group" will internally start a separate process for the specified group that all actors that belong to that group will run in
::

    # register the consumer in the main group
    mgr.register_actor(Consumer())
    # in our "worker group", register the Worker actor
    mgr.add_process_group('worker_group', Worker)      # spawns a new process that "ticks" independently

As the second argument to "add_process_group", specify a default actor class for the group so an instance of that actor class can be immediately instantiated upon the group being spawned.
