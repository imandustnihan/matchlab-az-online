"""Provider adapters for verifiable football matches, tables and media.
Only published upstream results are shown. All network calls are injected for testing.

ESPN endpoints are undocumented/unlicensed for production. OpenLigaDB is
community-maintained. TheSportsDB v1 free endpoints may cap returned matches.
"""
import datetime as dt
import re
import urllib.parse

SPORTSDB = {
 'eng.1': 4328, 'ger.1': 4331, 'ita.1': 4332, 'fra.1': 4334,
 'esp.1': 4335, 'ned.1': 4337, 'tur.1': 4339,
}
OPENLIGA = {'ger.1':'bl1','eng.1':'pl','esp.1':'la1'}


def _num(x):
 try:
  if x is None or x == '': return None
  return int(float(str(x)))
 except (TypeError, ValueError, OverflowError):return None


def season_year(date):
 d=dt.date.fromisoformat(date)
 return d.year if d.month>=7 else d.year-1


def espn_games(raw, league):
 items=[]
 for event in raw.get('events') or []:
  competition=(event.get('competitions') or [{}])[0]
  comps=competition.get('competitors') or []
  home=next((x for x in comps if x.get('homeAway')=='home'),None)
  away=next((x for x in comps if x.get('homeAway')=='away'),None)
  if home is None or away is None:continue
  status=event.get('status') or {}
  st=status.get('type') or {}
  state={'pre':'scheduled','in':'live','post':'final'}.get(st.get('state'),'scheduled')
  def team(c):
   t=c.get('team') or {}
   pics=t.get('logos') or []
   return {'id':str(t.get('id','')),'name':t.get('displayName') or t.get('name') or '—',
    'image':t.get('logo') or (pics[0].get('href','') if pics else '')}
  returnscore=lambda c: None if state=='scheduled' else _num(c.get('score'))
  items.append({'id':f"espn:{league}:{event.get('id')}", 'eventId':str(event.get('id') or ''),
   'league':league,'home':team(home),'away':team(away),
   'homeScore':returnscore(home),'awayScore':returnscore(away),'state':state,
   'minute':status.get('displayClock') or st.get('shortDetail') or '',
   'date':event.get('date') or '', 'source':'ESPN (qeyri-rəsmi)'})
 return items


def openliga_games(raw, league, date):
 if not isinstance(raw,list):raise ValueError('Unexpected OpenLigaDB response')
 items=[]
 for event in raw:
  when=event.get('matchDateTimeUTC') or event.get('matchDateTime') or ''
  # UTC can be +/-1 day from the local calendar. Prefer local source date.
  local=event.get('matchDateTime') or when
  if local[:10]!=date:continue
  results=event.get('matchResults') or []
  full=next((r for r in results if r.get('resultTypeID')==2),None)
  partial=next((r for r in results if r.get('resultTypeID')==1),None)
  result=full or partial or (results[-1] if results else None)
  done=bool(event.get('matchIsFinished'))
  has_scores=result is not None and _num(result.get('pointsTeam1')) is not None and _num(result.get('pointsTeam2')) is not None
  state='final' if done else 'live' if has_scores else 'scheduled'
  def team(v):
   v=v or {}
   return {'id':str(v.get('teamId') or ''),'name':v.get('teamName') or '—','image':v.get('teamIconUrl') or ''}
  a=event.get('team1') or {};b=event.get('team2') or {}
  items.append({'id':'open:'+str(event.get('matchID') or ''),'eventId':str(event.get('matchID') or ''),
   'league':league,'home':team(a),'away':team(b),
   'homeScore':_num(result.get('pointsTeam1')) if has_scores else None,
   'awayScore':_num(result.get('pointsTeam2')) if has_scores else None,
   'state':state,'minute':'','date':local,
   'source':'OpenLigaDB (icma məlumatı)'})
 return items


def sportsdb_games(raw, league):
 rows=raw.get('events') or []
 if not isinstance(rows,list):raise ValueError('Unexpected TheSportsDB response')
 out=[]
 for ev in rows:
  if (ev.get('strSport') or 'Soccer')!='Soccer':continue
  status=str(ev.get('strStatus') or '').lower()
  hs=_num(ev.get('intHomeScore'));as_=_num(ev.get('intAwayScore'))
  finished=any(x in status for x in ('finished','full time','match ended','after extra','penalty'))
  in_play=any(x in status for x in ('live','in progress','half time','1st half','2nd half'))
  state='final' if finished else 'live' if in_play else 'scheduled'
  # If feed supplies scores without status, don't assume they are current live goals.
  if state=='scheduled' and hs is not None and as_ is not None:
   # Old scheduled date plus reported score is a past result, not a live event.
   old=(ev.get('dateEvent') or '') < dt.date.today().isoformat()
   state='final' if ev.get('strStatus')=='FT' or (old and ev.get('dateEvent')) else 'scheduled'
  out.append({'id':'sportsdb:'+str(ev.get('idEvent') or ''),'eventId':str(ev.get('idEvent') or ''),
   'league':league,'home':{'id':str(ev.get('idHomeTeam') or ''),'name':ev.get('strHomeTeam') or '—','image':ev.get('strHomeTeamBadge') or ''},
   'away':{'id':str(ev.get('idAwayTeam') or ''),'name':ev.get('strAwayTeam') or '—','image':ev.get('strAwayTeamBadge') or ''},
   'homeScore':hs if state!='scheduled' else None,'awayScore':as_ if state!='scheduled' else None,
   'state':state,'minute':ev.get('strProgress') or '',
   'date':ev.get('strTimestamp') or ((ev.get('dateEvent') or '')+'T'+(ev.get('strTime') or '00:00:00')),
   'source':'TheSportsDB (pulsuz, qismən)'})
 return out


def sportsdb_table(raw):
 rows=raw.get('table') or []
 if not isinstance(rows,list):raise ValueError('Unexpected TheSportsDB table')
 return [{'name':r.get('strTeam') or '—','image':r.get('strBadge') or r.get('strTeamBadge') or '',
  'rank':_num(r.get('intRank')) or i+1,'played':_num(r.get('intPlayed')),
  'win':_num(r.get('intWin')),'draw':_num(r.get('intDraw')),
  'loss':_num(r.get('intLoss')),'points':_num(r.get('intPoints'))}
  for i,r in enumerate(rows)]


def openliga_table(raw):
 if not isinstance(raw,list):raise ValueError('Unexpected OpenLigaDB table')
 items=[]
 for i,r in enumerate(raw):
  team=r.get('teamInfo') or {}
  items.append({'name':team.get('teamName') or r.get('teamName') or '—',
   'image':team.get('teamIconUrl') or '',
   'rank':i+1,'played':_num(r.get('matches')),
   'win':_num(r.get('won')),'draw':_num(r.get('draw')),
   'loss':_num(r.get('lost')),'points':_num(r.get('points'))})
 return items


def sportsdb_matches_url(date,league):
 id_=SPORTSDB[league]
 return f'https://www.thesportsdb.com/api/v1/json/123/eventsday.php?'+urllib.parse.urlencode({'d':date,'s':'Soccer','l':id_})


def sportsdb_table_url(league):
 return 'https://www.thesportsdb.com/api/v1/json/123/lookuptable.php?l='+str(SPORTSDB[league])


def openliga_matches_url(date,league):
 return f'https://api.openligadb.de/getmatchdata/{OPENLIGA[league]}/{season_year(date)}'


def openliga_table_url(league,date):
 return f'https://api.openligadb.de/getbltable/{OPENLIGA[league]}/{season_year(date)}'
