"""Regression checks for the added league routing and automatic grouping."""
import datetime
import unittest
from unittest.mock import patch
import league_catalog
import match_sources
import live_center

class LeaguesTests(unittest.TestCase):
    def test_azerbaijan_source_id_is_verified(self):
        self.assertEqual(match_sources.SPORTSDB['aze.1'],4693)
        self.assertIn('aze.1',league_catalog.CORE_LEAGUES)
        self.assertEqual(live_center.LEAGUE_NAMES['aze.1'],'Azərbaycan Premyer Liqası')
        url=match_sources.sportsdb_matches_url('2026-11-03','aze.1')
        self.assertIn('l=4693',url)
    def test_only_actual_games_in_all(self):
        checked=[]
        def fake_source(league,date):
            checked.append(league)
            if league=='aze.1':
                return {'items':[{'id':'sportsdb:1234567','state':'scheduled',
                    'home':{'name':'Qarabağ'},'away':{'name':'Sabah'}}],
                    'available':True}
            return {'items':[], 'available':True}
        with patch.object(live_center,'_CACHE',{}):
            d=live_center._compute_view('all','2030-01-02',fake_source)
        self.assertIn('aze.1',checked)
        self.assertEqual(len(d['items']),1)
        self.assertEqual(d['items'][0]['leagueName'],'Azərbaycan Premyer Liqası')
        self.assertEqual(d['liveCount'],0)
    def test_empty_not_invented(self):
        with patch.object(live_center,'_CACHE',{}):
            d=live_center._compute_view('aze.1','2030-01-02',lambda l,day:{'available':True,'items':[]})
        self.assertEqual(d['items'],[])
        self.assertFalse(d['stale'])
if __name__=='__main__':unittest.main()
