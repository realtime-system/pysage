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

Other useful methods
--------------------
"trigger" is the synchronous version of the `"queue_message"` call, it processes the supplied message immediately and does not wait for the actor manager's `"tick"`
::

    mgr.trigger(BombMessage(damage=10)) # prints "the secret is small secret"

`"find"` returns back the instance of the registered actor with that name
::

    mgr.find('player1') # returns the registered actor instance

Prerequisites
-------------

Sphinx needs at least **Python 2.4** to run.  If you like to have source code
highlighting support, you must also install the Pygments_ library, which you can
do via setuptools' easy_install.  Sphinx should work with docutils version 0.4
or some (not broken) SVN trunk snapshot.

.. _reStructuredText: http://docutils.sf.net/rst.html
.. _Pygments: http://pygments.org


Setting up the documentation sources
------------------------------------

The root directory of a documentation collection is called the :dfn:`source
directory`.  Normally, this directory also contains the Sphinx configuration
file :file:`conf.py`, but that file can also live in another directory, the
:dfn:`configuration directory`.

.. versionadded:: 0.3
   Support for a different configuration directory.

Sphinx comes with a script called :program:`sphinx-quickstart` that sets up a
source directory and creates a default :file:`conf.py` from a few questions it
asks you.  Just run ::

   $ sphinx-quickstart

and answer the questions.


Running a build
---------------

A build is started with the :program:`sphinx-build` script.  It is called
like this::

     $ sphinx-build -b latex sourcedir builddir

where *sourcedir* is the :term:`source directory`, and *builddir* is the
directory in which you want to place the built documentation (it must be an
existing directory).  The :option:`-b` option selects a builder; in this example
Sphinx will build LaTeX files.

The :program:`sphinx-build` script has several more options:

**-a**
   If given, always write all output files.  The default is to only write output
   files for new and changed source files.  (This may not apply to all
   builders.)

**-E**
   Don't use a saved :term:`environment` (the structure caching all
   cross-references), but rebuild it completely.  The default is to only read
   and parse source files that are new or have changed since the last run.

**-t** *tag*
   Define the tag *tag*.  This is relevant for :dir:`only` directives that only
   include their content if this tag is set.

   .. versionadded:: 0.6

**-d** *path*
   Since Sphinx has to read and parse all source files before it can write an
   output file, the parsed source files are cached as "doctree pickles".
   Normally, these files are put in a directory called :file:`.doctrees` under
   the build directory; with this option you can select a different cache
   directory (the doctrees can be shared between all builders).

**-c** *path*
   Don't look for the :file:`conf.py` in the source directory, but use the given
   configuration directory instead.  Note that various other files and paths
   given by configuration values are expected to be relative to the
   configuration directory, so they will have to be present at this location
   too.

   .. versionadded:: 0.3

**-C**
   Don't look for a configuration file; only take options via the ``-D`` option.

   .. versionadded:: 0.5

**-D** *setting=value*
   Override a configuration value set in the :file:`conf.py` file.  The value
   must be a string or dictionary value.  For the latter, supply the setting
   name and key like this: ``-D latex_elements.docclass=scrartcl``.

   .. versionchanged:: 0.6
      The value can now be a dictionary value.

**-A** *name=value*
   Make the *name* assigned to *value* in the HTML templates.

**-N**
   Do not do colored output.  (On Windows, colored output is disabled in any
   case.)

**-q**
   Do not output anything on standard output, only write warnings and errors to
   standard error.

**-Q**
   Do not output anything on standard output, also suppress warnings.  Only
   errors are written to standard error.

**-w** *file*
   Write warnings (and errors) to the given file, in addition to standard error.

**-W**
   Turn warnings into errors.  This means that the build stops at the first
   warning and ``sphinx-build`` exits with exit status 1.

**-P**
   (Useful for debugging only.)  Run the Python debugger, :mod:`pdb`, if an
   unhandled exception occurs while building.


You can also give one or more filenames on the command line after the source and
build directories.  Sphinx will then try to build only these output files (and
their dependencies).

