"""Automatic football profile watchlist: bounded, verified and crash-safe."""
import unittest
import tempfile
from pathlib import Path
import profile_auto_updates as p

class ProfileAutoUpdateTests(unittest.TestCase):
    def setUp(self):
        self.oldfile=p.FILE
        self.dir=tempfile.TemporaryDirectory()
        p.FILE=Path(self.dir.name)/"watch.json"
        with p.LOCK:p.WATCHED.clear()
    def tearDown(self):
        with p.LOCK:p.WATCHED.clear()
        p.FILE=self.oldfile
        self.dir.cleanup()

    def test_only_verified_qid_and_kind(self):
        self.assertIsNone(p.watch("12345","players"))
        self.assertIsNone(p.watch("Q12345","unknown"))
        watched=p.watch("Q12345","players")
        self.assertTrue(watched["autoRefresh"])
        self.assertEqual(watched["coverage"],"recently_viewed_only")
        self.assertIn("Q12345",p.WATCHED)
        self.assertTrue(p.FILE.exists())

    def test_expired_items_refresh_no_more_than_limit(self):
        for i in range(12):
            p.watch("Q"+str(2000+i),"players")
        for v in p.WATCHED.values():v["checked"]=0
        calls=[]
        def enriched(qid,fetch,refresh,kind):
            calls.append((qid,refresh,kind))
            return {"wikiMatch":True}
        result=p.refresh_once(enriched,lambda url,ttl:None,max_items=2)
        self.assertEqual(result,{"attempted":2,"verified":2})
        self.assertEqual(len(calls),2)
        self.assertTrue(all(refresh is True for _,refresh,_ in calls))

    def test_no_data_is_not_verified(self):
        p.watch("Q500","teams")
        result=p.refresh_once(lambda q,f,refresh,kind:{"wikiMatch":False},None,max_items=2)
        self.assertEqual(result["verified"],0)

    def test_source_failure_is_nonfatal_and_does_not_loop(self):
        p.watch("Q600","coaches")
        def offline(*args,**kwargs):raise ConnectionError("offline")
        result=p.refresh_once(offline,None,max_items=2)
        self.assertEqual(result["attempted"],1)
        self.assertEqual(p.refresh_once(offline,None,max_items=2)["attempted"],0)

if __name__=="__main__":unittest.main()
