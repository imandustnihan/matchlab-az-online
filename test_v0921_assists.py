"""v0.9.21: trusted identity matching, bounded free statistics and UI regression."""
import unittest
from pathlib import Path
from unittest.mock import patch
import season_stats as ss
import server

ROOT=Path(__file__).resolve().parent

class SeasonStatsTests(unittest.TestCase):
    def setUp(self):
        self.person={'id':'rpabcdef123456','kind':'players','name':'Lionel Messi','birth':'1987-06-24'}
        self.player={'idPlayer':'34146304','strPlayer':'Lionel Andrés Messi','strSport':'Soccer','dateBorn':'1987-06-24'}

    def test_verified_name_and_birth_only(self):
        self.assertEqual(ss.verified_provider_id(self.person,[self.player])[0],'34146304')
        self.assertIsNone(ss.verified_provider_id(self.person,[{**self.player,'dateBorn':'1986-06-24'}])[0])
        self.assertIsNone(ss.verified_provider_id(self.person,[{**self.player,'strPlayer':'Other Person'}])[0])
        self.assertIsNone(ss.verified_provider_id(self.person,[{**self.player,'strSport':'Basketball'}])[0])

    def test_ambiguous_matches_rejected(self):
        self.assertIsNone(ss.verified_provider_id(self.person,[self.player,{**self.player,'idPlayer':'56'}])[0])

    def test_partial_dates_rejected(self):
        self.assertEqual(ss.iso_birth('1987'),'')
        self.assertEqual(ss.iso_birth('1987-06'),'')
        self.assertEqual(ss.iso_birth('1987-06-24'),'1987-06-24')
        self.assertEqual(ss.iso_birth('1987-02-30'),'')

    def test_lookups_on_demand_with_public_api(self):
        calls=[]
        def getter(url,ttl):
            calls.append(url)
            if 'searchplayers.php' in url:return {'player':[self.player]}
            return {'playerstats':[
                {'idPlayer':'34146304','strSport':'Soccer','strSeason':'2025-2026','strTeam':'Inter Miami','strLeague':'MLS','strStatistic':'Assists','strValue':'7'},
                {'idPlayer':'34146304','strSport':'Soccer','strSeason':'2025-2026','strTeam':'Inter Miami','strLeague':'MLS','strStatistic':'Goals','strValue':'15'},
                {'idPlayer':'34146304','strSport':'Soccer','strSeason':'2025-2026','strTeam':'Inter Miami','strLeague':'MLS','strStatistic':'Games Played','strValue':'19'}]}
        result=ss.lookup(self.person,getter)
        self.assertTrue(result['available']);self.assertTrue(result['identityVerified'])
        self.assertEqual(result['items'][0]['assists'],7)
        self.assertEqual(result['items'][0]['goals'],15)
        self.assertEqual(result['items'][0]['appearances'],19)
        self.assertEqual(len(calls),2)
        self.assertTrue(all(x.startswith(ss.ROOT) for x in calls))

    def test_zero_only_when_source_says_zero(self):
        val=ss.parse_player_stats({'playerstats':[{'idPlayer':'1','strSport':'Soccer','strSeason':'2024','strStatistic':'Assists','strValue':'0'}]},'1')
        self.assertEqual(val['items'][0]['assists'],0)
        val=ss.parse_player_stats({'playerstats':[{'idPlayer':'1','strSport':'Soccer','strSeason':'2024','strStatistic':'Goals','strValue':'2'}]},'1')
        self.assertIsNone(val['items'][0]['assists'])

    def test_free_cap_is_not_full_career(self):
        rows=[{'idPlayer':'1','strSport':'Soccer','strSeason':'2024','strStatistic':'Goals','strValue':str(i),'strTeam':f'Team {i}'} for i in range(10)]
        res=ss.parse_player_stats({'playerstats':rows},'1')
        self.assertTrue(res['partial']);self.assertEqual(res['recordsSeen'],10)

    def test_unknown_stat_not_mislabeled(self):
        rows=[{'idPlayer':'1','strSport':'Soccer','strSeason':'2024','strStatistic':'Goalkeeper Goals Conceded','strValue':'9'}]
        self.assertFalse(ss.parse_player_stats({'playerstats':rows},'1')['available'])

    def test_unverified_person_never_calls_external_source(self):
        with patch.object(ss,'lookup',wraps=ss.lookup) as noop:
            def never(*args):raise AssertionError('external API must not be called')
            result=ss.lookup({**self.person,'birth':'1987'},never)
            self.assertFalse(result['available'])
            self.assertFalse(noop.call_count==0) # test wrapper was invoked

    def test_server_endpoint_uses_verified_profile(self):
        with patch.object(server,'get_json',side_effect=lambda url,ttl=0: {'player':[self.player]} if 'searchplayers.php' in url else {'playerstats':[{'idPlayer':'34146304','strSport':'Soccer','strSeason':'2026','strStatistic':'Assists','strValue':'4'}]}),patch.object(server,'send_data',wraps=server.send_data) as routed:
            # keep profile source deterministic, no external Wikidata/Wikipedia required
            def fake_profile(path,params):
                if path=='/api/profile':return {'profile':self.person}
                return real(path,params)
            real=server.send_data
            with patch.object(server,'send_data',side_effect=fake_profile):
                res=server.send_data('/api/season-stats',{'id':['Q5705']})
                self.assertTrue(res['available']);self.assertEqual(res['items'][0]['assists'],4)

    def test_frontend_shows_source_and_full_database_search(self):
        src=(ROOT/'app.js').read_text(encoding='utf-8')
        self.assertIn('/api/season-stats?id=',src)
        self.assertIn('/api/search?kind=players&q=',src)
        self.assertIn('Mövsüm statistikaları və assistlər',src)
        self.assertIn("sumCareer(a,'assists')",src)
        self.assertIn('data-compare-pick=',src)
        self.assertNotIn('Ətraflı mövsüm statistikası üçün etibarlı lisenziyalı futbol məlumatı tələb olunur.',src)

if __name__=='__main__':unittest.main()
