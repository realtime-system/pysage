.. pysage documentation master file, created by
   sphinx-quickstart on Mon May 31 22:51:37 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

About
======

*pysage* is a lightweight high-level message passing library supporting actor based concurrency.  

It also extends the `actor model <http://en.wikipedia.org/wiki/Actor_model>`_ to support actor partitioning/grouping to further scalability.  pysage has a simple high-level interface.  Messages are serialized and sent lightweight using pipes or domain sockets across local "groups".  In the case of network messages, UDP is used.
  * simple pythonic API
  * efficient message propagation within group, across group, across network
  * network messages can optionally be configured to be reliable and/or ordered using UDP
  * grouping - actors can be partitioned into groups that are run in separate os processes
  * process-local singleton manager - actor registration, discovery, message propagation
  * publisher/subscriber pattern built-in

pysage strives to stay thin and lightweight.

Installation
============
*pysage* can be installed via setuptools::

    easy_install pysage

Usage
=====
Here, we have a simple actor that receives a "take damage" message in a 30 ticks/sec game loop::

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

Run this code, Player would have printed that the message was received.  Hit "ctrl-c" to escape the loop.  

pysage allows you to use this same simple API, for messaging across processes and networks.  

pysage does not confine you to the constraints of the "actor model".  For example, the "grouping" concept allows many actors to reside in the same process.  This allows you to avoid spawning too many os processes and reduce IPC overhead.  

Refer to :doc:`documentation <documentation>` for more.

Status
=======
*stable release 1.5.5*

 * September 10th, 2010 - select TCP transport added to transport collections; enabled atomic property type to use packing/unpacking
 * May 09th, 2010 - pysage grouping has been updated to provide better windows support, and many bug fixes

License
=======
pysage uses MIT license.  

Indices and tables
==================
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`



