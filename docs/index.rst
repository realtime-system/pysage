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

pysage allows you to use this same simple API, for messaging across processes and networks.  

pysage does not confine you to the constraints of the "actor model".  For example, the "grouping" concept allows many actors to reside in the same process.  This allows you to avoid spawning too many os processes and reduce IPC overhead.  

Further, actors in the same group are local to each other, so they can have access to each other.  It's kind of like a: "what happens in the group, stays in the group" concept.  Although, using messages are encouraged instead of straight calls for most situations, even in the same pysage group.

Look at `Documentation <http://code.google.com/p/pysage/wiki/Documentation>`_ for more.

Status
=======
*stable release 1.5.4*

May 09th, 2010 - pysage grouping has been updated to provide better windows support, and many bug fixes

License
=======
pysage itself uses MIT license.  

pysage provides built-in UDP and TCP transport.  However, if you need reliable/ordered UDP messaging across network, pysage uses `pyraknet <http://pyraknet.slowchop.com/ pyraknet>`_ and therefore `Raknet <http://www.jenkinssoftware.com/>`_ for UDP network implementation.  pyraknet uses the GNU Lesser General Public License.

RakNet is free to use for non-commercial use and purchasable for commercial use. It uses the Creative Commons Attribution - NonCommercial 2.5 license.

==================================

Contents:

.. toctree::
   :maxdepth: 2

   intro.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`






