``pqueue_fetcher``
==================

Implements a priority-queue-based fetching system.

The ``Fetcher`` class can be used by passing a ``fetch`` function
which accepts locations of an arbitrary type.

Locations can then be added via the fetcher's ``add`` method.

It is meant to manage fetches by interrupting timed-out calls to ``fetch``
and by re-entering failed fetches back into the queue
with an altered priority.

Fetches which fail, either due to timeout
or by virtue of being filtered out by a passed ``success`` function,
are routed back into the source queue
with their priority altered by another passed function.

Succeeding fetches are passed on to the ``results`` queue.

The ``fetch`` function may be any function which accepts a single parameter:
thus the scope of tasks it may perform is relatively unrestricted.

The ``Fetcher`` constructor also accepts a numeric ``threadcount`` argument,
which will determine the number of concurrent ``fetch`` functions to run.

Each ``fetch`` call will be made in a newly spawned thread.
This is done as a relatively simple way to allow interruption
of the call using the C ``PyThreadState_SetAsyncExc`` function.


Portability
-----------

Because of its use of CPython's underlying C API,
this module is not portable to other Python implementations.


Issues
------

Due to deficiencies in Python's threading facilities
which the author has been unable to work around,
problems may result if the passed ``fetch`` blocks on I/O.

An attempt has been made to work around these issues;
see the ``reactor`` function for details.

Despite this attempt, the code is still markedly sketchy.
Consider yourself warned.

Of related note is the method ``test.FetcherTester.test_incorrect_fission``.
This test highlights the fragility of the I/O block workaround.
See the documentation for that method for more information.


License
-------

``pqueue_fetcher`` is licensed under the MIT license.

License details are provided in the file ``COPYING``.


Status
------

Although the module does pass its fairly simplistic test suite,
this is no guarantee of usability.

In particular, the module hasn't been used
to do anything other than pass its test suite.

Developers in search of a robust solution for multithreaded document retrieval
are well advised to look elsewhere,
probably starting with the `twisted`_ framework.

``pqueue_fetcher`` was undertaken
more as an exercise in multithreading and the use of queues
than for the sake of creating a usable body of code.

It is being published mostly as an example of these techniques,
and for the sake of highlighting some of the difficulties
in writing threaded Python code.

The module is also missing some obvious bits of functionality,
such as the ability to set a retry limit.

Should work continue on ``pqueue_fetcher``,
it may prove more useful to allow the timeout logic
to be handled by the ``fetch`` functions.


.. _twisted: http://twistedmatrix.com/trac/
