Pysage Grouping
================

This section describes Pysage's "Grouping" functionality.

Basics
---------------------------------
Grouping can be very useful in partitioning actors into separate processes.  Actors in different groups have their own independent update/message handling loop.  And messages can be communicated across groups via IPC.  
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
