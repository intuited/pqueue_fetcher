"""Implements a priority-queue-based fetching system.

The `Fetcher` class can be used by passing a `fetch` function
  which accepts locations of an arbitrary type.

Locations can then be added via the fetcher's `add` method.

It is meant to manage fetches by interrupting timed-out calls to `fetch`
  and by re-entering failed fetches back into the queue
  with an altered priority.

HOWEVER, due to deficiencies in Python's threading facilities
  which the author has been unable to work around,
  problems may result if the passed `fetch` blocks.

An attempt has been made to work around this problem;
  see the `reactor` function for details.

Unless a more reliable method is found for ensuring proper code execution,
  this module should not be used for production code.
"""
import threading
from Queue import PriorityQueue, Queue
from terminable_thread import Thread

import logging
logger = logging.getLogger('pqueue_fetcher trace')
logger.addHandler((type("NullHandler", (logging.Handler, object),
                        {'emit': lambda *args: None}))())
_trace = logger.debug


def reactor():
    """
    Returns a function which can be used to break the atomicity
      of the return from a blocking call.
    This is used in Worker._fetch_and_put.
    
    This is almost certainly implementation-dependent,
      and as such this module should not be used in production code
      unless it is known that `fetch` will not block.

    The author is not entirely sure why this technique fixes this problem.

    See the function FetcherTester.test_incorrect_fission in the test suite
      for an example of an ineffective fission and the ramifications thereof.

    See the docs for `terminable_thread` for more info.
    """
    def fission():
        i = 0
        while True:
            yield i
    return fission().next
fission = reactor()

class FetchInterruptError(Exception):
    pass

class FetchFailureError(Exception):
    pass

def reduce_priority(priority):
    """Slightly reduce a priority.

    Assumes that floating-point priorities are being used,
      and that a lower value means a higher priority.
    """
    return priority * 1.1

class Worker(object):
    """Returns a worker function that fetches locations from `locations`.

        The resulting function does not modify any instance variables,
          making it possible to pass it as the `target` of multiple threads.
    
        This code makes a "best effort" to not drop completed fetches.
        However, due to the possibility of a thread interruption occurring
          between the end of the fetch and the beginning of the handling code,
          this cannot be guaranteed.
    
        In order to ensure that,
          a fetch routine should be used which accepts a timeout parameter;
          however, this code provides no facilities to use such an option.
    
        `locations` is a Queue, typically a PriorityQueue,
          whose `get` method returns (priority, location) pairs.

        The fetched results are `put` to the Queue `results`.

        If the fetch is interrupted, the location is re-added to the queue
          with an adjusted priority.

        The location will also be returned to the queue
          if success(result) is not truthy.
    """
    def __init__(self, locations, fetch, results,
                 timeout=1,
                 success=bool,
                 adjust_priority=reduce_priority,
                 fission=fission):
        self.locations = locations
        self.fetch = fetch
        self.results = results
        self.timeout = timeout
        self.success = success
        self.adjust_priority = adjust_priority
        self.fission = fission

    def _reput_location(self, priority, location):
        """Redirects interrupted fetches back to the `locations` queue."""
        _trace("reputting {0}".format((priority, location)))
        self.locations.put((self.adjust_priority(priority), location))
        _trace("...reput complete.")

    def _put_result(self, priority, location, result):
        """Directs successful fetches to the `results` queue."""
        if self.success(result):
            _trace("_put_result: putting {0}".format(result))
            self.results.put(result)
            _trace("...put complete.")
        else:
            _trace("_put_result: reputting {0}".format((priority, location)))
            self._reput_location(priority, location)

    def _fetch_and_put(self, priority, location):
        """Fetches from the location, handling a single FetchInterruptError.
        
        If the fetch fails due to interruption or due to a bad result,
          self._reput_location will be called.
        
        Otherwise, _put_result is called.
        """
        result = None
        _trace("fetching ({0}, {1})".format(priority, location))
        try:
            try:
                _trace('calling fetch({0})...'.format(location))
                # If self.fetch directly returns from a blocking function,
                #   this will effectively be atomic, meaning that on interruption,
                #   execution will bounce to the *outer* `except` clause.  No good.
                result = self.fetch(location)
                # So we do something in between.
                self.fission()
                # This trace will break up the atomicity by itself
                #   if a standard error StreamHandler has been added.
                _trace('...fetch completed.  exiting try clause...')
            except FetchInterruptError:
                _trace("---interrupted.")
                self._reput_location(priority, location)
                return
            _trace("...fetched {0}".format(result))
            self._put_result(priority, location, result)
            return
        except FetchInterruptError:
            _trace("---interrupted during _put_result({0})".format(result))
            # Catch the interrupt if it comes after the fetch.
            self._put_result(priority, location, result)
            return

    def __call__(self):
        while True:
            priority, location = self.locations.get()
            _trace("____  got new location:  priority: {0};  location: {1}".format(priority, location))
            fetchingthread = Thread(target=self._fetch_and_put,
                                    args=(priority, location))
            fetchingthread.daemon = True
            fetchingthread.start()
            _trace('__call__: thread started.  joining...')
            fetchingthread.join(self.timeout)
            _trace('__call__: ...joined.')
            try:
                _trace('__call__: raising FetchInterruptError...')
                fetchingthread.raise_exc(FetchInterruptError)
                _trace('__call__: ...raised.  joining...')
                fetchingthread.join()
                _trace('__call__: ...joined.')
            except threading.ThreadError:
                # Happens when the thread completes before the timeout.
                _trace('__call__ got ThreadError.')
                pass
            finally:
                self.locations.task_done()


class Fetcher(object):
    """Manages repeated attempts to fetch locations.
    
    Locations are added via the `add` method.
    
    `fetch` is a function which will be called to fetch a location.

    `results` is a Queue to which successfully fetched results will be `put`.

    `Worker` is a function which generates worker functions
      given a fetch function and other parameters;
      see `pqueue_fetcher.Worker` for the signature
      and for the definition of `success` and `adjust_priority`.
    """
    def __init__(self, fetch, threadcount,
                 results=None, timeout=0.1, Worker=Worker,
                 success=bool, adjust_priority=reduce_priority,
                 **worker_kwargs):
        self.locations = PriorityQueue()
        self.results = results if results is not None else Queue()
        worker = Worker(self.locations, fetch, self.results, 
                        timeout=timeout, success=success,
                        adjust_priority=adjust_priority, **worker_kwargs)
        self.threads = tuple(Thread(target=worker, args=())
                             for i in range(threadcount))
        for thread in self.threads:
            thread.daemon = True

    def add(self, location, priority=.5):
        self.locations.put((priority, location))

    def fetch(self):
        """Fetches the results.  Returns a Queue of them."""
        for thread in self.threads:
            thread.start()
        return self.results
