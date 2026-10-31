import copy
import datetime
import http.server
import json
import os
import pathlib
import sys
import threading
import unittest
import urllib.request

ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import free_match_details as details
import match_sources as feeds
import server

class SourceParserTests(unittest.TestCase):
    def test_sportsdb_partial_lineup_and_real_stats(self):
        data=details.sportsdb_details({'lineup':[{'strHome':'Yes','strSubstitute':'No','strPlayer':'A. One','intSquadNumber':'9','strPosition':'Striker'},
            {'strHome':'No','strSubstitute':'Yes','strPlayer':'B. Two','intSquadNumber':'15','strPosition':'Defender'}]},
            {'eventstats':[{'strStat':'Shots on Goal','intHome':'11','intAway':'8'}]},
            {'timeline':[{'intTime':'41','strEvent':'Goal','strPlayer':'A. One','strHome':'Yes'}]})
        self.assertTrue(data['available']);self.assertEqual(data['lineup']['home']['starters'][0]['name'],'A. One')
        self.assertTrue(data['lineup']['home']['incomplete']);self.assertFalse(data['lineup']['home']['formationVerified'])
        self.assertEqual(data['statistics'][0]['home'],11);self.assertEqual(data['statistics'][0]['away'],8)
        self.assertEqual(data['events'][0]['clock'],"41'")

    def test_sportsdb_missing_data_never_becomes_fake(self):
        x=details.sportsdb_details({}, {}, {})
        self.assertFalse(x['available']);self.assertEqual(x['events'],[])
        self.assertEqual(x['lineup']['home']['starters'],[]);self.assertEqual(x['statistics'],[])

    def test_espn_real_formation_and_starters(self):
        players=[{'starter':True,'formationPlace':str(i),'athlete':{'displayName':f'Futbolçu {i}','id':str(i)},
            'position':{'abbreviation':'G' if i==1 else 'DF'},'jersey':str(i)} for i in range(1,12)]
        raw={'rosters':[{'homeAway':'home','formation':'4-3-3','roster':players}]}
        d=details.espn_details(raw)
        self.assertEqual(d['lineup']['home']['formation'],'4-3-3')
        self.assertTrue(d['lineup']['home']['formationVerified'])
        self.assertEqual(len(d['lineup']['home']['starters']),11)
        self.assertFalse(d['lineup']['home']['incomplete'])
        raw['rosters'][0]['formation']='5-6-6'
        self.assertEqual(details.espn_details(raw)['lineup']['home']['formation'],'')

    def test_espn_nonstarter_is_sub_not_initial_lineup(self):
        x=details.espn_details({'rosters':[{'homeAway':'home','formation':'4-4-2','roster':[
            {'starter':False,'athlete':{'displayName':'Reserve'},'jersey':'22'}]}]})
        self.assertEqual(len(x['lineup']['home']['starters']),0)
        self.assertEqual(len(x['lineup']['home']['substitutes']),1)

    def test_openliga_goal(self):
        d=details.openliga_details({'goals':[{'goalGetterName':'İ. Hücumçu','matchMinute':79,'scoreTeam1':2,'scoreTeam2':1}]})
        self.assertTrue(d['available']);self.assertIn('İ. Hücumçu',d['events'][0]['text'])
        self.assertFalse(d['lineup']['home']['formationVerified'])

    def test_scores_short_status_codes(self):
        def ev(s):return {'idEvent':s,'strStatus':s,'strSport':'Soccer','idHomeTeam':'1','idAwayTeam':'2',
                           'strHomeTeam':'A','strAwayTeam':'B','intHomeScore':'2','intAwayScore':'1',
                           'strTimestamp':'2026-10-31T19:00:00','dateEvent':'2026-10-31'}
        v=feeds.sportsdb_games({'events':[ev('1H'),ev('FT'),ev('NS'),ev('HT'),ev('2H'),ev('AET')]},'eng.1')
        state={x['eventId']:x['state'] for x in v}
        self.assertEqual(state,{'1H':'live','FT':'final','NS':'scheduled','HT':'live','2H':'live','AET':'final'})
        self.assertEqual(v[0]['date'],'2026-10-31T19:00:00Z')
        self.assertIsNone(next(x for x in v if x['eventId']=='NS')['homeScore'])

    def test_server_rejects_invalid_ids_before_remote_requests(self):
        bad=server.send_data('/api/match-detail',{'provider':['sportsdb'],'id':['https://example.com/']})
        self.assertFalse(bad['available'])
        bad=server.send_data('/api/match-detail',{'provider':['espn'],'id':['55'],'league':['unknown.1']})
        self.assertFalse(bad['available'])

    def test_server_sportsdb_mock_integration(self):
        old=server.source_call
        try:
            def stub(source,url,ttl):
                if 'lookuplineup' in url:return {'lineup':[{'strHome':'Yes','strSubstitute':'No','strPlayer':'Test Player'}]}
                if 'lookupeventstats' in url:return {'eventstats':[{'strStat':'Corners','intHome':3,'intAway':4}]}
                return {'timeline':[]}
            server.source_call=stub
            d=server.send_data('/api/match-detail',{'provider':['sportsdb'],'id':['12345']})
            self.assertTrue(d['available']);self.assertEqual(d['statistics'][0]['name'],'Corners')
        finally:
            server.source_call=old

    def test_server_registry_status(self):
        data=server.send_data('/api/status',{})
        self.assertEqual(data['world']['total'],506207)
        self.assertEqual(data['version'],'0.9.14-local')

    def test_local_asset_security(self):
        httpd=http.server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        t=threading.Thread(target=httpd.serve_forever,daemon=True);t.start()
        try:
            origin='http://127.0.0.1:'+str(httpd.server_address[1])
            for path in ('/index.html','/app.js','/styles.css','/api/status'):
                with urllib.request.urlopen(origin+path,timeout=3) as r:
                    self.assertEqual(r.status,200);r.read()
            for path in ('/world_football.sqlite','/server.py','/data_manifest.json','/free_match_details.py'):
                with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(origin+path,timeout=3)
                self.assertEqual(e.exception.code,404)
        finally:httpd.shutdown();httpd.server_close();t.join(3)

if __name__=='__main__':unittest.main(verbosity=2)
