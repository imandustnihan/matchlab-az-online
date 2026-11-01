"""MATCHLAB AZ 0.9.27 source-aware league, coach, assists and fixture tests."""
import json
import re
import unittest
from pathlib import Path
from unittest.mock import patch
import server
import league_catalog
import live_center
import match_sources
import free_match_details

ROOT=Path(__file__).resolve().parent

class LeagueCatalog26(unittest.TestCase):
    def test_68_unique_source_codes_but_core_poll_is_bounded(self):
        self.assertEqual(len(league_catalog.CORE_LEAGUES),12)
        self.assertEqual(len(league_catalog.EXTRA_LEAGUES),56)
        self.assertEqual(len(league_catalog.ALL_LEAGUES),68)
        self.assertTrue(all(re.fullmatch(r'[a-z0-9._]+',slug) for slug in league_catalog.ALL_LEAGUES))
        self.assertEqual(server.LEAGUES,set(league_catalog.ALL_LEAGUES))
        self.assertTrue(set(league_catalog.EXTRA_LEAGUES).issubset(live_center.LEAGUE_NAMES))

    def test_api_leagues_reports_real_scope_not_promised_availability(self):
        x=server.send_data('/api/leagues',{})
        self.assertEqual(x['count'],68)
        self.assertEqual(sum(row['automatic'] for row in x['items']),12)
        self.assertIn('demək deyil',x['note'])

    def test_expanded_league_request_queries_single_league_not_68(self):
        expected='jpn.1'; day='2026-10-11'; observed=[]
        def fake(name,date):
            observed.append((name,date))
            return {'available':True,'items':[{'id':'espn:111','home':{'name':'A'},'away':{'name':'B'},'state':'final'}]}
        with patch.object(live_center,'_CACHE',{}):
            r=live_center.view(expected,day,fake)
        self.assertEqual(observed,[(expected,day)])
        self.assertTrue(r['available'])
        self.assertEqual(r['items'][0]['league'],expected)

    def test_all_view_remains_12_not_68(self):
        observed=[]
        def fake(name,date):
            observed.append(name)
            return {'available':True,'items':[]}
        with patch.object(live_center,'_CACHE',{}):
            r=live_center.view('all','2026-09-12',fake)
        self.assertEqual(set(observed),set(league_catalog.CORE_LEAGUES))
        self.assertEqual(len(observed),12)
        self.assertTrue(r['available'])

    def test_espn_actual_goals_form_and_groups_are_preserved(self):
        row=lambda n,more: {'team':{'displayName':n,'logos':[{'href':'https://example.com/logo.png'}]},'stats':[{'name':k,'value':v} for k,v in more.items()]}
        response={'children':[{'name':'Group A','standings':{'entries':[
            row('Club A',{'rank':1,'gamesPlayed':10,'wins':7,'ties':2,'losses':1,'points':23,
                          'pointsFor':20,'pointsAgainst':8,'pointDifferential':12,'lastFive':'WWDLW'})]}},
            {'name':'Group B','standings':{'entries':[row('Club B',{'points':5})]}}]}
        with patch.object(server,'source_call',return_value=response):
            rows=server.espn_standings('uefa.champions')
        self.assertEqual(len(rows),2)
        self.assertEqual((rows[0]['gf'],rows[0]['ga'],rows[0]['gd'],rows[0]['points']), (20,8,12,23))
        self.assertEqual(rows[0]['form'],'WWDLW')
        self.assertEqual(rows[0]['group'],'Group A')
        self.assertIsNone(rows[1]['gf'])
        self.assertIsNone(rows[1]['ga'])
        self.assertEqual(rows[1]['group'],'Group B')

    def test_sportsdb_missing_goals_and_assists_do_not_become_zero(self):
        rows=match_sources.sportsdb_table({'table':[{'strTeam':'Sample','intRank':'1','intPoints':'2'}]})
        self.assertIsNone(rows[0]['gf']); self.assertIsNone(rows[0]['ga'])
        self.assertEqual(rows[0]['points'],2)

    def test_event_assist_only_when_explicitly_provided(self):
        timeline={'timeline':[{'intTime':'52','strTimeline':'Goal','strPlayer':'One','strAssist':'Two','strHome':'Yes'},
                               {'intTime':'81','strTimeline':'Goal','strPlayer':'Three','strAssist':None,'strHome':'No'}]}
        x=free_match_details.sportsdb_details({}, {},timeline)
        self.assertEqual(len(x['events']),2)
        self.assertIn('Asist: Two',x['events'][0]['text'])
        self.assertNotIn('Asist',x['events'][1]['text'])

class CoachPresets26(unittest.TestCase):
    def test_six_dated_sourced_coaches_for_correct_formations(self):
        data=json.loads((ROOT/'coach_tactics.json').read_text(encoding='utf-8'))
        js=(ROOT/'coach_tactics.js').read_text(encoding='utf-8').strip()
        self.assertEqual(len(data),6)
        self.assertEqual(json.loads(js.removeprefix('window.ML_COACH_TACTICS=').removesuffix(';')),data)
        self.assertEqual(len({x['id'] for x in data}),6)
        self.assertEqual({x['coach'] for x in data},{'Pep Guardiola','Mikel Arteta','Jürgen Klopp','Carlo Ancelotti','José Mourinho','Xabi Alonso'})
        for p in data:
            with self.subTest(p=p['id']):
                self.assertEqual(sum(int(n) for n in p['formation'].split('-')),10)
                self.assertIn('learning.coachesvoice.com',p['source'])
                self.assertIn('20',p['season'])
                self.assertLessEqual(p['press'],90)

    def test_old_wikipedia_sources_preserved_and_versions_incremented(self):
        html=(ROOT/'index.html').read_text(encoding='utf-8')
        self.assertIn('coach_tactics.js?v=0927',html)
        self.assertIn('app.js?v=0927',html)
        self.assertIn('styles.css?v=0927',html)
        self.assertIn('0.9.27',(ROOT/'hosting_server.py').read_text(encoding='utf-8'))
        js=(ROOT/'app.js').read_text(encoding='utf-8')
        self.assertIn('Wikipedia və mənbələr',js)
        self.assertIn('Asist',js)
        self.assertIn('Ayarlar',js)

if __name__=='__main__':unittest.main()
