"""Historical CC0 football archive contract and no-fabrication tests."""
import unittest
import historical_archive as archive

class HistoryTests(unittest.TestCase):
    def test_leagues_are_source_identified(self):
        self.assertIn("eng.1",archive.LEAGUES)
        self.assertIn("tur.1",archive.LEAGUES)
        self.assertTrue(archive.allowed_season("2025-26"))
        self.assertTrue(archive.allowed_season("2026-27"))
        self.assertFalse(archive.allowed_season("2025-28"))
        self.assertFalse(archive.allowed_season("2100-01"))

    def test_verified_result_and_unknown_score(self):
        urls=[]
        def fetch(url,ttl):
            urls.append(url)
            return {"name":"Premier League","matches":[
                {"round":"Matchday 1","date":"2025-08-15","time":"20:00","team1":"Liverpool FC","team2":"AFC Bournemouth","score":{"ft":[4,2]}},
                {"round":"Matchday 2","date":"2025-08-23","team1":"Leeds","team2":"Everton"},
                {"round":"Matchday 3","date":"2025-08-30","team1":"Arsenal","team2":"Chelsea","score":[1,1]},
            ]}
        result=archive.view("eng.1","2025-26",fetch)
        self.assertTrue(result["available"])
        self.assertFalse(result["live"])
        self.assertEqual(result["count"],3)
        self.assertEqual(result["items"][0]["homeScore"],4)
        self.assertEqual(result["items"][1]["homeScore"],None)
        self.assertFalse(result["items"][1]["resultRecorded"])
        self.assertTrue(result["items"][2]["resultRecorded"])
        self.assertIn("/2025-26/en.1.json",urls[0])
        self.assertEqual(archive.view("eng.1","2025-26",fetch,team="liverpool")["count"],1)

    def test_failed_source_returns_unavailable(self):
        def broken(url,ttl):raise OSError("offline")
        r=archive.view("eng.1","2025-26",broken)
        self.assertFalse(r["available"])
        self.assertEqual(r["items"],[])
        self.assertFalse(r["live"])

    def test_source_must_be_dict_with_matches(self):
        r=archive.view("eng.1","2025-26",lambda u,t:{"name":"empty"})
        self.assertFalse(r["available"])

    def test_invalid_search_has_no_fetch(self):
        def fail(u,t):raise AssertionError("must not fetch")
        self.assertFalse(archive.view("unknown","2025-26",fail)["available"])
        self.assertFalse(archive.view("eng.1","2025-35",fail)["available"])

    def test_full_season_bundle_for_local_filtering(self):
        calls=[]
        def fetch(url,ttl):
            calls.append((url,ttl))
            return {"matches":[
                {"date":"2025-08-15","team1":"Liverpool FC" if i%2 else "Arsenal",
                 "team2":"Bournemouth","score":{"ft":[1,0]}} for i in range(145)
            ]}
        bundle=archive.bundle("eng.1","2025-26",fetch)
        self.assertTrue(bundle["bundle"])
        self.assertTrue(bundle["complete"])
        self.assertFalse(bundle["live"])
        self.assertEqual(bundle["count"],145)
        self.assertEqual(len(bundle["items"]),145)
        self.assertTrue(all(item["resultRecorded"] for item in bundle["items"]))
        self.assertEqual(len(calls),2)  # One season source reused across pages.

    def test_bundle_source_failure_is_not_a_fixture(self):
        def fail(url,ttl):raise TimeoutError("offline")
        payload=archive.bundle("eng.1","2025-26",fail)
        self.assertFalse(payload["available"])
        self.assertFalse(payload["live"])
        self.assertEqual(payload["items"],[])

    def test_pagination_and_clamping(self):
        def fetch(u,t):
            return {"matches":[{"date":"2025-08-15","team1":str(i),"team2":"B","score":[0,0]} for i in range(115)]}
        r=archive.view("eng.1","2025-26",fetch,limit=60,offset=60)
        self.assertEqual(len(r["items"]),55)
        self.assertIsNone(r["nextOffset"])
        self.assertEqual(r["items"][0]["home"],"60")

if __name__=="__main__":unittest.main()
