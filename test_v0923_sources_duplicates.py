"""v0.9.23 regression: unique people, assist safety and genuine free providers."""
import datetime as dt
import os
import unittest
from unittest.mock import patch

import free_football_sources as fs
import season_stats as ss
import server

class NewFreeSources(unittest.TestCase):
    def test_openfootball_public_domain_past_only(self):
        date=(dt.date.today()-dt.timedelta(days=30)).isoformat()
        u=fs.openfootball_url('eng.1',date)
        self.assertIn('raw.githubusercontent.com/openfootball/football.json',u)
        self.assertTrue(u.endswith('/en.1.json'))
        self.assertEqual(fs.openfootball_url('eng.1',dt.date.today().isoformat()),'')
        self.assertEqual(fs.openfootball_url('uefa.champions',date),'')

    def test_openfootball_scores_and_unknown_kickoff(self):
        date='2020-09-10'
        data={'matches':[{'date':date,'team1':'A','team2':'B','score':{'ft':[1,2]}},
                         {'date':date,'team1':'C','team2':'D','score':{}},
                         {'date':'2020-09-11','team1':'E','team2':'F','score':{'ft':[1,0]}}]}
        rows=fs.parse_openfootball(data,'eng.1',date)
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]['state'],'final')
        self.assertEqual(rows[0]['homeScore'],1)
        self.assertTrue(rows[0]['kickoffUnverified'])
        self.assertNotEqual(rows[1]['homeScore'],0)
        self.assertNotEqual(rows[1]['state'],'live')

    def test_football_data_delayed_safety(self):
        date='2026-10-20'
        raw={'matches':[{'id':1,'utcDate':date+'T16:00:00Z','status':'IN_PLAY',
                         'homeTeam':{'name':'Madrid'},'awayTeam':{'name':'Barca'},
                         'score':{'fullTime':{'home':1,'away':1}}},
                        {'id':2,'utcDate':date+'T18:00:00Z','status':'FINISHED',
                         'homeTeam':{'name':'Milan'},'awayTeam':{'name':'Inter'},
                         'score':{'fullTime':{'home':2,'away':3}}}]}
        rows=fs.parse_football_data_matches(raw,'esp.1',date)
        self.assertEqual(rows[0]['state'],'scheduled')
        self.assertIsNone(rows[0]['homeScore'])
        self.assertEqual(rows[1]['state'],'final')
        self.assertEqual(rows[1]['homeScore'],2)
        self.assertNotIn('live',[r['state'] for r in rows])

    def test_football_data_table_and_paths(self):
        rows=fs.parse_football_data_table({'standings':[{'type':'HOME','table':[{'team':{'name':'wrong'}}]},
                                  {'type':'TOTAL','table':[{'team':{'name':'A'},'position':1,'playedGames':20,'points':43,'won':13,'draw':4,'lost':3}]}]})
        self.assertEqual(rows[0]['name'],'A')
        self.assertEqual(rows[0]['points'],43)
        self.assertIn('/v4/competitions/PL/standings',fs.football_data_path('eng.1',table=True))
        self.assertFalse(fs.football_data_path('tur.1',table=True))

    def test_token_not_exposed_and_not_required_for_core(self):
        with patch.dict(os.environ,{'FOOTBALL_DATA_TOKEN':'private-demo-value'}):
            r=server.send_data('/api/sources',{})
            self.assertTrue(r['configured']['footballDataFreeToken'])
            self.assertNotIn('private-demo-value',str(r))
        with patch.dict(os.environ,{'FOOTBALL_DATA_TOKEN':''}):
            self.assertFalse(server.send_data('/api/sources',{})['configured']['footballDataFreeToken'])

    def test_football_data_fetch_rejects_arbitrary_urls(self):
        with self.assertRaises(ValueError):fs.fetch_football_data('https://other.example/', 'secret')
        with self.assertRaises(ValueError):fs.fetch_football_data('/v4/teams/123', 'secret')
        with self.assertRaises(ValueError):fs.fetch_football_data('/v4/competitions/PL/standings', '')

    def test_valid_source_callback_in_live_fallback(self):
        # No live sources reply, historical CC0 can be returned explicitly.
        day='2020-09-10'
        with patch.object(server,'source_call',side_effect=lambda name,url,ttl: {'matches':[{'date':day,'team1':'A','team2':'B','score':{'ft':[2,1]}}]} if name=='OpenFootball CC0' else (_ for _ in ()).throw(ConnectionError('offline'))):
            v=server.live_from_sources('eng.1',day)
        self.assertTrue(v['available']);self.assertTrue(v['partial'])
        self.assertEqual(v['items'][0]['state'],'final')
        self.assertIn('OpenFootball',v['source'])

class VerifiedDuplicates(unittest.TestCase):
    def test_ancelotti_father_and_son_are_distinct(self):
        r=server.send_data('/api/search',{'q':['Ancelotti'],'kind':['all']})
        c=[x for x in r['items'] if 'carlo' in x['name'].casefold()]
        d=[x for x in r['items'] if 'davide' in x['name'].casefold()]
        self.assertEqual(len(c),1)
        self.assertEqual(len(d),1)
        self.assertEqual(c[0]['qid'],'Q174614')
        self.assertNotEqual(d[0].get('qid'),c[0].get('qid'))

    def test_known_dual_role_names_single_profile(self):
        for name in ['Pep Guardiola','Xabi Alonso','Mikel Arteta','Jürgen Klopp','Carlo Ancelotti']:
            with self.subTest(name=name):
                rows=server.send_data('/api/search',{'q':[name],'kind':['all']})['items']
                qids=[x['qid'] for x in rows if x.get('qid')]
                self.assertEqual(len(qids),len(set(qids)))

class AssistStrictFallback(unittest.TestCase):
    def test_without_dob_needs_name_nation_and_club(self):
        profile={'kind':'players','name':'Example Striker','country':'Spain',
                 'clubs':[{'name':'Real Madrid'}]}
        player={'idPlayer':'12345','strPlayer':'Example Striker','strSport':'Soccer',
                'strNationality':'Spanish','strTeam':'Real Madrid'}
        self.assertEqual(ss.verified_provider_id(profile,[player])[0],'12345')
        for bad in [dict(player,strPlayer='Example Striker Junior'),dict(player,strTeam='Sevilla'),dict(player,strNationality='Italian')]:
            self.assertIsNone(ss.verified_provider_id(profile,[bad])[0])

    def test_without_dob_identical_candidates_rejected(self):
        profile={'kind':'players','name':'Example Striker','country':'Spain','clubs':['Real Madrid']}
        players=[{'idPlayer':str(i),'strPlayer':'Example Striker','strSport':'Soccer','strNationality':'Spain','strTeam':'Real Madrid'} for i in [1,2]]
        self.assertIsNone(ss.verified_provider_id(profile,players)[0])

if __name__=='__main__':unittest.main()
