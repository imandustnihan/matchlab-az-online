"""Regression checks for responsive cached-first MATCHLAB football score views."""
import threading
import time
import unittest
import live_center


class LiveCacheTests(unittest.TestCase):
    def setUp(self):
        with live_center._LOCK:
            live_center._CACHE.clear()
            live_center._FLIGHT.clear()

    def tearDown(self):
        # Background refreshes are daemon threads; let any test waiter complete.
        time.sleep(.025)
        with live_center._LOCK:
            live_center._CACHE.clear()
            live_center._FLIGHT.clear()

    def test_fresh_cache_does_not_refetch(self):
        date=live_center.baku_today()
        calls=[]
        def fetch(name,day):
            calls.append(name)
            return {'available':True,'items':[{'id':'espn:eng.1:22','state':'scheduled'}],'source':'test'}
        first=live_center.view('eng.1',date,fetch)
        second=live_center.view('eng.1',date,fetch)
        self.assertTrue(first['available'])
        self.assertTrue(second['cached'])
        self.assertEqual(calls,['eng.1'])

    def test_expired_cache_returns_fast_with_explicit_stale_warning(self):
        date=live_center.baku_today()
        started=threading.Event()
        done=threading.Event()
        def fetch(name,day):
            if started.is_set():
                done.wait(timeout=2)
            return {'available':True,'items':[{'id':'espn:eng.1:22','state':'live'}],'source':'test'}
        first=live_center.view('eng.1',date,fetch)
        self.assertEqual(first['liveCount'],1)
        with live_center._LOCK:
            key=('eng.1',date)
            old=live_center._CACHE[key]
            live_center._CACHE[key]=(time.monotonic()-40,old[1])
        started.set()
        before=time.monotonic()
        cached=live_center.view('eng.1',date,fetch)
        elapsed=time.monotonic()-before
        done.set()
        self.assertLess(elapsed,.5)
        self.assertTrue(cached['stale'])
        self.assertTrue(cached['refreshing'])
        self.assertEqual(cached['liveCount'],0)
        self.assertTrue(cached['items'][0]['stale'])
        self.assertIn('CANLI DEYİL',cached['message'])


if __name__=='__main__':
    unittest.main()
