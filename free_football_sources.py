"""Free, source-labeled football fixture/table adapters for MATCHLAB AZ.

OpenFootball football.json is public-domain historical data (CC0). It is *not*
a real-time score feed. football-data.org's free tier needs a separately
registered token, exposes delayed scores and limits requests to 10/minute.
No credentials are stored in the repository or returned through the API.
"""
import datetime as dt
import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

OPENFOOTBALL_CODES={
    'eng.1':'en.1','ger.1':'de.1','esp.1':'es.1','ita.1':'it.1',
    'fra.1':'fr.1','ned.1':'nl.1','por.1':'pt.1','tur.1':'tr.1',
}
FOOTBALL_DATA_CODES={
    'eng.1':'PL','ger.1':'BL1','esp.1':'PD','ita.1':'SA','fra.1':'FL1',
    'ned.1':'DED','por.1':'PPL','uefa.champions':'CL',
}
LOCK=threading.Lock()
_REQUESTS=[]
_CACHE={}


def openfootball_url(league,date):
    if league not in OPENFOOTBALL_CODES:return ''
    day=dt.date.fromisoformat(date)
    # The public-domain archive is a historical fallback, not a live source.
    if day>dt.date.today()-dt.timedelta(days=2) or day.year<1990:
        return ''
    year=day.year if day.month>=7 else day.year-1
    folder=f'{year}-{str((year+1)%100).zfill(2)}'
    return f'https://raw.githubusercontent.com/openfootball/football.json/master/{folder}/{OPENFOOTBALL_CODES[league]}.json'


def _score(value):
    if isinstance(value,bool):return None
    if isinstance(value,int) and 0<=value<=60:return value
    return None


def parse_openfootball(data,league,date):
    if not isinstance(data,dict) or not isinstance(data.get('matches'),list):
        raise ValueError('OpenFootball formatı gözlənilən kimi deyil')
    rows=[]
    for i,match in enumerate(data['matches'][:2000]):
        if not isinstance(match,dict) or match.get('date')!=date:continue
        home=str(match.get('team1') or '').strip()[:110]
        away=str(match.get('team2') or '').strip()[:110]
        if not home or not away:continue
        ft=(match.get('score') or {}).get('ft') if isinstance(match.get('score'),dict) else None
        hs,as_=(ft[0],ft[1]) if isinstance(ft,list) and len(ft)==2 else (None,None)
        hs,as_=_score(hs),_score(as_)
        final=hs is not None and as_ is not None
        rows.append({
            'id':f'openfootball:{league}:{date}:{i}',
            'eventId':'', 'league':league,
            'home':{'id':'','name':home,'image':''},
            'away':{'id':'','name':away,'image':''},
            'homeScore':hs if final else None,'awayScore':as_ if final else None,
            'state':'final' if final else 'scheduled',
            'date':date+'T12:00:00Z','minute':'',
            'kickoffUnverified':True,
            'source':'OpenFootball · CC0 tarixi arxiv (canlı deyil)',
        })
        if len(rows)>=70:break
    return rows


def football_data_path(league,date=None,table=False):
    code=FOOTBALL_DATA_CODES.get(league)
    if not code:return ''
    if table:return f'/v4/competitions/{code}/standings'
    dt.date.fromisoformat(date)
    return f'/v4/competitions/{code}/matches?'+urllib.parse.urlencode({'dateFrom':date,'dateTo':date})


def _num(x):
    return int(x) if type(x) is int and 0<=x<=100000 else None


def parse_football_data_matches(data,league,date):
    if not isinstance(data,dict) or not isinstance(data.get('matches'),list):
        raise ValueError('football-data.org formatı gözlənilən kimi deyil')
    rows=[]
    for match in data['matches'][:100]:
        home=match.get('homeTeam') or {};away=match.get('awayTeam') or {}
        when=match.get('utcDate') or ''
        if not (isinstance(when,str) and when.startswith(date)):
            continue
        if not (home.get('name') and away.get('name')):continue
        status=str(match.get('status') or '').upper()
        # The free plan is delayed; NEVER advertise this as real-time.
        state='final' if status=='FINISHED' else 'scheduled'
        score=(match.get('score') or {}).get('fullTime') or {}
        hs,as_=_num(score.get('home')),_num(score.get('away'))
        rows.append({
            'id':'football-data:'+str(match.get('id') or ''),'eventId':str(match.get('id') or ''),
            'league':league,
            'home':{'id':str(home.get('id') or ''),'name':home['name'],'image':''},
            'away':{'id':str(away.get('id') or ''),'name':away['name'],'image':''},
            'homeScore':hs if state=='final' else None,'awayScore':as_ if state=='final' else None,
            'state':state,'date':when,'minute':'',
            'source':'football-data.org · pulsuz gecikmiş məlumat',
        })
    return rows


def parse_football_data_table(data):
    standings=data.get('standings') if isinstance(data,dict) else None
    if not isinstance(standings,list):raise ValueError('football-data.org cədvəli yanlışdır')
    total=next((x for x in standings if x.get('type')=='TOTAL' and isinstance(x.get('table'),list)),None)
    if not total:return []
    rows=[]
    for item in total['table'][:30]:
        club=item.get('team') or {}
        if not club.get('name'):continue
        rows.append({
            'name':str(club['name'])[:120],'image':'',
            'rank':_num(item.get('position')),
            'played':_num(item.get('playedGames')),
            'win':_num(item.get('won')),
            'draw':_num(item.get('draw')),
            'loss':_num(item.get('lost')),
            'points':_num(item.get('points')),
            'gf':_num(item.get('goalsFor')),'ga':_num(item.get('goalsAgainst')),
        })
    return rows


def fetch_football_data(path,token,opener=None):
    """Safe allowlisted official API with free-tier throttling and cached JSON."""
    if not re.fullmatch(r'/v4/competitions/(?:PL|BL1|PD|SA|FL1|DED|PPL|CL)/(?:standings|matches\?dateFrom=\d{4}-\d{2}-\d{2}&dateTo=\d{4}-\d{2}-\d{2})',path):
        raise ValueError('Yalnız təsdiqlənmiş sorğular icazəlidir')
    if not token or not isinstance(token,str) or len(token)>250 or any(ord(c)<33 or ord(c)>126 for c in token):
        raise ValueError('football-data.org pulsuz tokeni konfiqurasiya edilməyib')
    if opener is None:opener=urllib.request.urlopen
    now=time.monotonic()
    key=(path,token)
    with LOCK:
        cached=_CACHE.get(key)
        if cached and cached[0]>now:return cached[1]
        _REQUESTS[:]=[t for t in _REQUESTS if now-t<60]
        if len(_REQUESTS)>=9:raise ConnectionError('football-data.org pulsuz 10 sorğu/dəqiqə limitinə yaxındır')
        _REQUESTS.append(now)
    req=urllib.request.Request('https://api.football-data.org'+path,headers={
        'X-Auth-Token':token,'Accept':'application/json','User-Agent':'MATCHLAB-AZ/0.9.23'})
    with opener(req,timeout=8) as response:
        if int(response.headers.get('Content-Length','0') or 0)>2_000_000:
            raise ValueError('Böyük mənbə cavabı')
        data=response.read(2_000_001)
        if len(data)>2_000_000:raise ValueError('Böyük mənbə cavabı')
    result=json.loads(data)
    with LOCK:
        _CACHE[key]=(time.monotonic()+300,result)
        if len(_CACHE)>100:
            for k in list(_CACHE)[:len(_CACHE)-100]:_CACHE.pop(k,None)
    return result
