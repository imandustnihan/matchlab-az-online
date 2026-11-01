"""v0.9.16 regression: no fake live/finished fixtures, genuine status, timezone and UI."""
import datetime as dt
import unittest
from pathlib import Path
from zoneinfo import ZoneInfo
import match_sources as feeds
import server

ROOT=Path(__file__).resolve().parent

class ScoreStatusReliability(unittest.TestCase):
    @staticmethod
    def event(status, when, home='2', away='1'):
        return {'idEvent':'1290','strStatus':status,'strSport':'Soccer',
                'strHomeTeam':'Team A','strAwayTeam':'Team B',
                'intHomeScore':home,'intAwayScore':away,
                'dateEvent':when,'strTimestamp':when+'T18:00:00'}

    def test_explicit_not_started_remains_not_started_even_on_old_date_with_score(self):
        past=(dt.date.today()-dt.timedelta(days=30)).isoformat()
        for value in ['NS','Not Started','TBD','PST','Postponed','Abandoned','UNKNOWN']:
            with self.subTest(value=value):
                result=feeds.sportsdb_games({'events':[self.event(value,past)]},'eng.1')[0]
                self.assertEqual(result['state'],'scheduled')
                self.assertIsNone(result['homeScore'])
                self.assertIsNone(result['awayScore'])

    def test_explicit_status_live_and_final(self):
        past=(dt.date.today()-dt.timedelta(days=5)).isoformat()
        for code in ['1H','HT','2H','ET']:
            self.assertEqual(feeds.sportsdb_games({'events':[self.event(code,past)]},'eng.1')[0]['state'],'live')
        for code in ['FT','AET','PEN']:
            self.assertEqual(feeds.sportsdb_games({'events':[self.event(code,past)]},'eng.1')[0]['state'],'final')

    def test_statusless_old_results_may_be_final_but_never_live(self):
        past=(dt.date.today()-dt.timedelta(days=20)).isoformat()
        future=(dt.date.today()+dt.timedelta(days=1)).isoformat()
        self.assertEqual(feeds.sportsdb_games({'events':[self.event('',past)]},'eng.1')[0]['state'],'final')
        x=feeds.sportsdb_games({'events':[self.event('',future)]},'eng.1')[0]
        self.assertEqual(x['state'],'scheduled')
        self.assertIsNone(x['homeScore'])

    @staticmethod
    def open_event(kick,finished=False):
        local=kick.astimezone(ZoneInfo('Europe/Berlin'))
        return {'matchID':90,'matchDateTime':local.strftime('%Y-%m-%dT%H:%M:%S'),
                'matchDateTimeUTC':kick.strftime('%Y-%m-%dT%H:%M:%S'),
                'matchIsFinished':finished,
                'matchResults':[{'resultTypeID':1,'pointsTeam1':1,'pointsTeam2':0}],
                'team1':{'teamId':1,'teamName':'Home'},
                'team2':{'teamId':2,'teamName':'Away'}}

    def test_openliga_never_infers_live_from_future_or_stale_score(self):
        now=dt.datetime.now(dt.timezone.utc)
        for delta in [dt.timedelta(hours=8),-dt.timedelta(days=2)]:
            ev=self.open_event(now+delta)
            date=ev['matchDateTime'][:10]
            match=feeds.openliga_games([ev],'ger.1',date)[0]
            self.assertEqual(match['state'],'scheduled')
            self.assertIsNone(match['homeScore'])
            self.assertIsNone(match['awayScore'])

    def test_openliga_actual_live_and_finished(self):
        now=dt.datetime.now(dt.timezone.utc)
        for finished,expected in [(False,'live'),(True,'final')]:
            ev=self.open_event(now-dt.timedelta(minutes=25),finished=finished)
            rows=feeds.openliga_games([ev],'ger.1',ev['matchDateTime'][:10])
            self.assertEqual(rows[0]['state'],expected)
            self.assertEqual(rows[0]['homeScore'],1)

    def test_browser_does_not_treat_absent_scores_as_zero(self):
        js=(ROOT/'app.js').read_text(encoding='utf8')
        self.assertIn('h.score==null?null:Number(h.score)',js)
        self.assertIn('a.score==null?null:Number(a.score)',js)

    def test_standings_all_fallback_not_discarded(self):
        js=(ROOT/'app.js').read_text(encoding='utf8')
        self.assertIn("league!==(st.league==='all'?'eng.1':st.league)",js)

    def test_health_and_version(self):
        self.assertEqual(server.send_data('/api/status',{})['version'],'0.9.27-local')
        self.assertIn('v=0927',(ROOT/'index.html').read_text(encoding='utf8'))

if __name__=='__main__':unittest.main(verbosity=2)
