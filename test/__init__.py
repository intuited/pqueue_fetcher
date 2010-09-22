from unittest import defaultTestLoader, TestCase, main
from Queue import Queue
from pqueue_fetcher import Fetcher

import logging
logger = logging.getLogger('pqueue_fetcher test trace')
logger.addHandler((type("NullHandler", (logging.Handler, object),
                        {'emit': lambda *args: None}))())
trace = logger.debug

def suite():
    """Returns the module test suite."""
    return defaultTestLoader.loadTestsFromTestCase(FetcherTester)


class Location(object):
    """A location for which get attempts initially fail `failures` times.
    
    Setting `delays` to a an iterable of numbers of seconds
      will cause successive gets to be delayed by the yielded amounts.
    """
    import time
    def __init__(self, value, failures=0, delays=(0,)):
        self.attempts = 0
        self.delays = iter(delays)
        self.value = value
        self.failures = failures

    def __str__(self):
        return 'Location{0}'.format((self.value, self.failures,
                                       self.delays))

    def __repr__(self):
        return self.__str__()

    def get(self):
        try:
            self.time.sleep(self.delays.next())
        except StopIteration:
            pass
        if self.attempts >= self.failures:
            return self.value
        else:
            self.attempts += 1

def fetch(location):
    """Fetch function fed to the fetcher in test cases."""
    return location.get()

class FetcherTester(TestCase):
    def setUp(self):
        self.results = Queue()

    def assertTuple(self, tuple_=(1, 2, 3), queue=None):
        from itertools import islice
        queue = queue or self.results
        self.assertEqual(tuple_, tuple(islice(iter(queue.get, object()), len(tuple_))))

    def _fetch(self, add_locations, threadcount=1, results=None, timeout=0.1, **kwargs):
        results = results or self.results
        fetcher = Fetcher(fetch, threadcount, results, timeout=timeout, **kwargs)
        add_locations(fetcher)
        fetcher.fetch()

    def test_reprioritization(self):
        """The location with value 2 should be reprioritized to priority 0.44.

        This should cause it to be retrieved second.
        """
        def add_locations(fetcher):
            fetcher.add(Location(3), priority=0.9)
            fetcher.add(Location(1, delays=(0,)), priority=0.42)
            fetcher.add(Location(2, delays=(0.2, 0)), priority=0.40)
        self._fetch(add_locations)
        self.assertTuple()

    def test_multiple_delays(self):
        """Test that gets with multiple long delays come out correctly."""
        def add_locations(fetcher):
            fetcher.add(Location(3, delays=(0.2, 0.2, 0.2)), priority=0.6)
            fetcher.add(Location(2, delays=(0.2, 0.2, 0.2)), priority=0.42)
            fetcher.add(Location(1, delays=(0.2, 0.2, 0.2)), priority=0.2)
        self._fetch(add_locations)
        self.assertTuple()

    def test_incorrect_fission(self):
        """Like test_reprioritization, with a useless fission function.

        This causes the inner try clause in Worker._fetch_and_put
          to fail to catch the FetchFailureError exception,
          with the result that execution instead
          proceeds to the outer `except` clause in that function.

        The end result is that the first fetched location,
          with value 2, is put to the results queue first
          instead of being re-put to the locations queue.

        See the docs for `pqueue_fetcher.reactor` for more info.
        """
        def add_locations(fetcher):
            fetcher.add(Location(3), priority=0.9)
            fetcher.add(Location(1, delays=(0,)), priority=0.42)
            fetcher.add(Location(2, delays=(0.2, 0)), priority=0.40)
        self._fetch(add_locations, fission=lambda *args: None)
        self.assertTuple((2, 1, 3))

if __name__ == '__main__':
    main()
