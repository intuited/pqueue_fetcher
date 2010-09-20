`pqueue_fetcher`
================

Implements a priority-queue-based fetching system.

The `Fetcher` class can be used by passing a `fetch` function
  which accepts locations of an arbitrary type.

Locations can then be added via the fetcher's `add` method.

It is meant to manage fetches by interrupting timed-out calls to `fetch`
  and by re-entering failed fetches back into the queue
  with an altered priority.

HOWEVER, due to deficiencies in Python's threading facilities
  which the author has been unable to work around,
  problems may result if the passed `fetch` blocks on I/O.

An attempt has been made to work around this problem;
  see the `reactor` function for details.
