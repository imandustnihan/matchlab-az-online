"""MATCHLAB AZ v0.9.52 HTML + local Python server (stdlib only, no user API key).
Respects upstream failures, returns explicit availability flags, never synthesizes match results.
Sources: Wikidata CC0, Wikipedia pageimages (image rights vary), OpenLigaDB and unofficial ESPN.
"""
import argparse, json, re, threading, time, urllib.error, urllib.parse, urllib.request, webbrowser, os, hashlib
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import world_db
import match_sources as feeds
import free_match_details as details
import datetime as _dt
import wikipedia_enrichment as wiki
import live_center
import media_expansion as extra_media
import identity_unification as people
import club_history
import season_stats
import league_catalog
import historical_archive
import profile_auto_updates
import free_football_sources as open_feeds

ROOT=Path(__file__).resolve().parent
INSTALL={'state':'idle','message':'Hələ quraşdırılmayıb','bytes':0,'done':False,'error':''}
INSTALL_LOCK=threading.Lock()
CATALOG=json.loads((ROOT/'catalog.json').read_text(encoding='utf-8'))
CATBYID={x['id']:x for x in CATALOG}
QID=re.compile(r'^Q[1-9]\d{0,11}$')
LEAGUES=set(league_catalog.ALL_LEAGUES)
CACHE={}; CACHE_LOCK=threading.Lock(); HOST_COOLDOWN={}; UPSTREAM_TIMEOUT=8
SOURCE_STATUS={}
SCORE_CACHE=ROOT/'score_cache'
SCORE_CACHE.mkdir(exist_ok=True)
USER_AGENT=os.environ.get('MATCHLAB_WIKIMEDIA_UA','MatchlabAZ/0.9.52 (https://github.com/imandustnihan/matchlab-az-online; community football archive)')
WIKI_REQUEST_LOCK=threading.Lock()
WIKI_NEXT_REQUEST=0.0

def norm(s):
 import unicodedata
 return ''.join(c for c in unicodedata.normalize('NFKD',s.casefold().replace('ə','e').replace('ı','i')) if not unicodedata.combining(c))

def local_search(q,kind='all',limit=50):
 q=norm(q.strip()); terms=[t for t in re.split(r'\s+',q) if t]
 if not terms:return []
 hits=[]
 for r in CATALOG:
  if kind!='all' and kind!=r['kind']:continue
  text=norm(r['name']); meta=norm(' '.join([r.get('country',''),r.get('position','')]+r.get('clubs',[])+r.get('coached',[])))
  if all(t in text or t in meta for t in terms):
   score=(100 if text==q else 60 if text.startswith(q) else 30 if q in text else 5)
   hits.append((score,r))
 hits.sort(key=lambda x:(-x[0],x[1]['name']))
 return [r for _,r in hits[:limit]]

def get_json(url,ttl=300):
 """HTTP JSON with finite timeout and a cooldown ONLY for real rate-limit responses.
 DNS delays must not poison all unrelated requests from the same host.
 """
 now=time.monotonic()
 host=urllib.parse.urlsplit(url).netloc
 with CACHE_LOCK:
  if HOST_COOLDOWN.get(host,0)>now:
   raise ConnectionError('Mənbə sorğu limitini keçib; sonra yenidən yoxlanacaq.')
  entry=CACHE.get(url)
  if entry and entry[0]>now:
   if isinstance(entry[1],Exception):raise entry[1]
   return entry[1]
 # Wikimedia's 2026 anonymous API limits apply to our server too. Throttle
 # on cache miss, and share the pace across Wikipedia + Wikidata requests.
 if host=='www.wikidata.org' or host.endswith('.wikipedia.org'):
  global WIKI_NEXT_REQUEST
  with WIKI_REQUEST_LOCK:
   pause=max(0,WIKI_NEXT_REQUEST-time.monotonic())
   if pause:time.sleep(pause)
   WIKI_NEXT_REQUEST=time.monotonic()+0.55
 req=urllib.request.Request(url,headers={
  'Accept':'application/json','User-Agent':USER_AGENT,
  'Accept-Encoding':'identity','Cache-Control':'no-cache'})
 try:
  with urllib.request.urlopen(req,timeout=UPSTREAM_TIMEOUT) as resp:
   if int(resp.headers.get('Content-Length','0') or 0)>10_000_000:raise ValueError('Mənbənin cavabı çox böyükdür')
   data=resp.read(10_000_001)
   if len(data)>10_000_000:raise ValueError('Mənbənin cavabı çox böyükdür')
   output=json.loads(data)
 except Exception as ex:
  with CACHE_LOCK:
   CACHE[url]=(now+8,ex) # transient outages shouldn't disable whole competitions
   if isinstance(ex,urllib.error.HTTPError) and ex.code in (429,503):
    retry=ex.headers.get('Retry-After','')
    HOST_COOLDOWN[host]=now+(min(300,max(25,int(retry))) if str(retry).isdigit() else 45)
  raise
 with CACHE_LOCK:CACHE[url]=(now+ttl,output)
 return output

# Last successful snapshots are labeled as stale whenever an upstream cannot be reached.
# They are NEVER advertised as current live scores.
def snapshot_key(kind,league,date=''):
 return SCORE_CACHE / (kind+'_'+re.sub('[^a-z0-9_-]','_',league)+'_'+re.sub('[^0-9]','',date)+'.json')

def snapshot_save(kind,league,date,payload):
 try:
  fn=snapshot_key(kind,league,date)
  saved={'created':int(time.time()),'payload':payload}
  temp=fn.with_suffix('.tmp')
  temp.write_text(json.dumps(saved,ensure_ascii=False),encoding='utf8')
  os.replace(temp,fn)
 except (OSError,TypeError,ValueError):pass

def snapshot_load(kind,league,date):
 try:
  entry=json.loads(snapshot_key(kind,league,date).read_text(encoding='utf8'))
  age=int(time.time())-entry['created']
  if age>14*86400 or age<0:return None
  result=entry['payload']
  return {**result,'stale':True,'available':True,'asOf':entry['created'],
   'message':'Mənbə indi əlçatan deyil. Son saxlanmış nəticələr göstərilir; CANLI DEYİL.',
   'source':result.get('source','Keş')+' · əvvəlki yoxlama'}
 except (OSError,TypeError,ValueError,KeyError):return None

def source_call(name,url,ttl):
 try:
  v=get_json(url,ttl)
  SOURCE_STATUS[name]={'ok':True,'checked':int(time.time()),'detail':'Bağlantı uğurlu'}
  return v
 except Exception as ex:
  SOURCE_STATUS[name]={'ok':False,'checked':int(time.time()),'detail':type(ex).__name__+': '+str(ex)[:140]}
  raise


def wd_query(action,**params):
 params={'action':action,'format':'json',**params}
 return get_json('https://www.wikidata.org/w/api.php?'+urllib.parse.urlencode(params),600)

def wd_entities(ids):
 ids=[x for x in dict.fromkeys(ids) if QID.fullmatch(str(x))][:50]
 if not ids:return {}
 return wd_query('wbgetentities',ids='|'.join(ids),props='labels|descriptions|claims',languages='az|tr|en',languagefallback='1').get('entities',{})

def wd_label(e):
 return next((e.get('labels',{}).get(l,{}).get('value') for l in ['az','tr','en'] if e.get('labels',{}).get(l,{}).get('value')),e.get('id',''))

def wd_desc(e):
 return next((e.get('descriptions',{}).get(l,{}).get('value') for l in ['az','tr','en'] if e.get('descriptions',{}).get(l,{}).get('value')),'')

def claims(e,prop):
 return [s for s in e.get('claims',{}).get(prop,[]) if s.get('rank')!='deprecated' and s.get('mainsnak',{}).get('snaktype')=='value']

def wd_val(s):
 v=s.get('mainsnak',{}).get('datavalue',{}).get('value') if s else None
 return v.get('id',v.get('text',v.get('time',v.get('amount',v)))) if isinstance(v,dict) else v

def qualifiers(s,prop):
 v=s.get('qualifiers',{}).get(prop,[])
 raw=v[0].get('datavalue',{}).get('value') if v else None
 return raw.get('id',raw.get('time',raw.get('amount',raw))) if isinstance(raw,dict) else raw

def year(v):
 m=re.search(r'([12]\d{3})',str(v)) if v else None
 return int(m.group(1)) if m else None

def entity_media_filename(e,kind):
 # Do not display a stadium photo as a footballer portrait, or a person's photo as a club crest.
 # Even a QID can be passed with the wrong client kind; reject obvious type conflicts.
 inferred=wd_kind(e)
 if kind=='teams' and inferred in ('players','coaches'):return None
 if kind in ('players','coaches') and (inferred=='teams' or (claims(e,'P154') and not claims(e,'P106') and not claims(e,'P54'))):return None
 prop='P154' if kind=='teams' else 'P18'
 return next((wd_val(c) for c in claims(e,prop) if isinstance(wd_val(c),str) and 0<len(wd_val(c))<230),None)

def photo_url(e,known_kind=None):
 kind=known_kind or wd_kind(e)
 raw=entity_media_filename(e,kind)
 return 'https://commons.wikimedia.org/wiki/Special:FilePath/'+urllib.parse.quote(raw,safe='')+'?width=280' if raw else ''

def wd_kind(e):
 desc=wd_desc(e).lower(); occupations=[wd_val(x) for x in claims(e,'P106')]; instances=[wd_val(x) for x in claims(e,'P31')]
 if 'Q476028' in instances or 'football club' in desc or 'futbol klubu' in desc or 'soccer club' in desc:return 'teams'
 if 'Q628099' in occupations or 'football coach' in desc or 'football manager' in desc or 'məşqçi' in desc:return 'coaches'
 if 'Q937857' in occupations or 'football player' in desc or 'footballer' in desc or 'futbolçu' in desc or claims(e,'P54'):return 'players'
 return 'other'

def wd_search(q,kind):
 found=wd_query('wbsearchentities',search=q,language='en',uselang='az',limit='30').get('search',[])
 ids=[x.get('id','') for x in found if QID.fullmatch(x.get('id',''))]
 entities=wd_entities(ids)
 out=[]
 for id in ids:
  e=entities.get(id)
  if not e:continue
  typ=wd_kind(e)
  if typ=='other' or (kind!='all' and kind!=typ):continue
  out.append({'id':id,'name':wd_label(e),'kind':typ,'country':'','description':wd_desc(e),'image':photo_url(e,typ),'source':'Wikidata','verified':True})
 return out

def wd_profile(qid,known_kind=None):
 raw=wd_entities([qid]); e=raw.get(qid)
 if not e or e.get('missing') is not None:return None
 related=[]
 for prop in ['P54','P6087','P108','P413','P166','P27','P17']:
  related.extend([wd_val(x) for x in claims(e,prop) if QID.fullmatch(str(wd_val(x)))])
 lookup={k:wd_label(v) for k,v in wd_entities(related).items()}
 clubs=[]
 for c in claims(e,'P54'):
  key=wd_val(c)
  if not QID.fullmatch(str(key)):continue
  apps=qualifiers(c,'P1350');goals=qualifiers(c,'P1351')
  clubs.append({'id':key,'name':lookup.get(key,key),'from':year(qualifiers(c,'P580')),'to':year(qualifiers(c,'P582')),'apps':int(apps.lstrip('+')) if isinstance(apps,str) and apps.lstrip('+').isdigit() else None,'goals':int(goals.lstrip('+')) if isinstance(goals,str) and goals.lstrip('+').isdigit() else None})
 coached=[]
 for prop in ['P6087']:
  for c in claims(e,prop):
   key=wd_val(c)
   if QID.fullmatch(str(key)):coached.append({'id':key,'name':lookup.get(key,key),'from':year(qualifiers(c,'P580')),'to':year(qualifiers(c,'P582'))})
 positions=[lookup.get(wd_val(c),wd_val(c)) for c in claims(e,'P413')]
 countries=[lookup.get(wd_val(c),wd_val(c)) for c in claims(e,'P27')]
 awards=[lookup.get(wd_val(c),wd_val(c)) for c in claims(e,'P166')]
 # Preserve Wikidata date precision; a year-only death must never become Jan 1.
 def date_claim(prop):
  statement=(claims(e,prop) or [None])[0]
  raw=statement.get('mainsnak',{}).get('datavalue',{}).get('value') if statement else None
  return wiki.wikidata_date(raw)
 death=date_claim('P570');birthdate=date_claim('P569')
 has_playing=bool(clubs or claims(e,'P54'))
 has_coaching=bool(coached or claims(e,'P6087'))
 roles=(["players"] if has_playing else [])+(["coaches"] if has_coaching else [])
 return {'id':qid,'name':wd_label(e),'kind':known_kind or wd_kind(e),'description':wd_desc(e),'image':photo_url(e,known_kind),'country':', '.join(countries),'position':', '.join(positions),'clubs':clubs,'coached':coached,'awards':awards,'birth':birthdate,'death':death,'lifeStatus':'deceased' if death else 'unknown','careerStatus':'unverified','roles':roles,'source':'Wikidata','url':'https://www.wikidata.org/wiki/'+qid,'verified':True}

def parse_espn(data,league):
 out=[]
 for e in data.get('events',[]):
  c=(e.get('competitions') or [{}])[0]; comps=c.get('competitors',[])
  home=next((x for x in comps if x.get('homeAway')=='home'),None);away=next((x for x in comps if x.get('homeAway')=='away'),None)
  if not home or not away:continue
  st=e.get('status',{}).get('type',{});status={'pre':'scheduled','in':'live','post':'final'}.get(st.get('state'),'scheduled')
  def team(x):
   t=x.get('team',{});return {'id':str(t.get('id','')),'name':t.get('displayName') or t.get('name') or '—','image':t.get('logo') or (t.get('logos') or [{}])[0].get('href','')}
  def score(x):
   raw=x.get('score');return int(raw) if raw is not None and str(raw).isdigit() else None
  out.append({'id':'espn:'+league+':'+str(e.get('id')),'eventId':str(e.get('id')),'league':league,'home':team(home),'away':team(away),'homeScore':None if status=='scheduled' else score(home),'awayScore':None if status=='scheduled' else score(away),'state':status,'minute':e.get('status',{}).get('displayClock') or st.get('shortDetail',''),'date':e.get('date',''),'source':'ESPN (qeyri-rəsmi)'})
 return out

def espn_scores(league,date):
 url=f'https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard?dates={date.replace("-","")}&limit=150'
 return parse_espn(get_json(url,ttl=45),league)

def openliga_matches(date):
 season=int(date[:4])-(int(date[5:7])<7)
 rows=get_json(f'https://api.openligadb.de/getmatchdata/bl1/{season}',ttl=120)
 out=[]
 for e in rows:
  # OpenLigaDB reports UTC kickoff; align the requested match day to Baku time.
  when=e.get('matchDateTimeUTC') or e.get('matchDateTime') or ''
  try:
   kick=_dt.datetime.fromisoformat(when.replace('Z','+00:00'))
   # Provider's matchDateTime without UTC suffix is local German time, not UTC.
   if kick.tzinfo is None:
    from zoneinfo import ZoneInfo
    kick=kick.replace(tzinfo=ZoneInfo('Europe/Berlin'))
   from zoneinfo import ZoneInfo
   if kick.astimezone(ZoneInfo('Asia/Baku')).date().isoformat()!=date:continue
  except (ValueError,TypeError):continue
  rs=e.get('matchResults') or []
  final=next((x for x in rs if x.get('resultTypeID')==2),rs[-1] if rs else {})
  finished=bool(e.get('matchIsFinished'))
  elapsed=(_dt.datetime.now(_dt.timezone.utc)-kick.astimezone(_dt.timezone.utc)).total_seconds()
  has_score=bool(final and final.get('pointsTeam1') is not None and final.get('pointsTeam2') is not None)
  is_live=not finished and has_score and 0<=elapsed<=5*3600
  state='final' if finished else 'live' if is_live else 'scheduled'
  out.append({'id':'open:'+str(e.get('matchID')),'league':'ger.1','home':{'id':str(e.get('team1',{}).get('teamId','')),'name':e.get('team1',{}).get('teamName',''),'image':e.get('team1',{}).get('teamIconUrl','')},'away':{'id':str(e.get('team2',{}).get('teamId','')),'name':e.get('team2',{}).get('teamName',''),'image':e.get('team2',{}).get('teamIconUrl','')},'homeScore':final.get('pointsTeam1') if final and state!='scheduled' else None,'awayScore':final.get('pointsTeam2') if final and state!='scheduled' else None,'state':state,'minute':'','date':kick.astimezone(_dt.timezone.utc).isoformat(),'source':'OpenLigaDB','eventId':str(e.get('matchID'))})
 return out

def espn_standings(league):
 """Keep ESPN's real group/goal/form fields rather than making up table data."""
 j=source_call('ESPN',f'https://site.api.espn.com/apis/v2/sports/soccer/{league}/standings',900)
 def num(v):
  try:
   if v is None or v=='':return None
   return int(float(v))
  except (TypeError,ValueError,OverflowError):return None
 def normalize_entries(entries,group=''):
  result=[]
  for index,r in enumerate(entries if isinstance(entries,list) else []):
   t=r.get('team') or {};stats=r.get('stats') or []
   def raw(*names):
    found=next((v for v in stats if v.get('name') in names or v.get('abbreviation') in names),None)
    return (found.get('value') if found.get('value') is not None else found.get('displayValue')) if found else None
   logos=t.get('logos') or []
   gf=num(raw('pointsFor','goalsFor','goalsScored','GF'))
   ga=num(raw('pointsAgainst','goalsAgainst','goalsConceded','GA'))
   gd=num(raw('pointDifferential','goalDifference','GD'))
   # Form is only displayed when explicitly reported as W/D/L sequence.
   form=str(raw('lastFive','form','last5','lastFiveGames') or '').upper().replace(' ','')
   if not form or len(form)>10 or any(ch not in 'WDL-' for ch in form):form=''
   row={'name':t.get('displayName') or t.get('name') or '',
        'image':logos[0].get('href','') if logos else t.get('logo',''),
        'played':num(raw('gamesPlayed','GP')),'win':num(raw('wins','W')),
        'draw':num(raw('ties','D')),'loss':num(raw('losses','L')),
        'points':num(raw('points','PTS')),'rank':num(raw('rank','RK')) or index+1,
        'gf':gf,'ga':ga,'gd':gd,'form':form,'group':str(group or '')[:80]}
   if row['name']:result.append(row)
  return result
 out=normalize_entries((j.get('standings') or {}).get('entries'))
 def walk(nodes,depth=0):
  if depth>4 or not isinstance(nodes,list):return []
  found=[]
  for g in nodes:
   if not isinstance(g,dict):continue
   name=g.get('name') or g.get('abbreviation') or g.get('shortName') or ''
   found.extend(normalize_entries((g.get('standings') or {}).get('entries'),name))
   found.extend(walk(g.get('children'),depth+1))
  return found
 out.extend(walk(j.get('children')))
 # Duplicate teams may appear at parent and group level; prefer explicit group.
 merged={}
 for row in out:
  key=(row['group'],row['name'])
  merged[key]=row
 if any(row.get('group') for row in merged.values()):
  # Avoid parent aggregate duplicating group members.
  grouped={row['name'] for row in merged.values() if row['group']}
  merged={k:v for k,v in merged.items() if v['group'] or v['name'] not in grouped}
 return list(merged.values())

def openliga_table():
 season=time.gmtime().tm_year-(time.gmtime().tm_mon<7)
 rows=get_json(f'https://api.openligadb.de/getmatchdata/bl1/{season}',ttl=900)
 teams={}
 for m in rows:
  if not m.get('matchIsFinished'):continue
  results=m.get('matchResults') or []
  final=next((x for x in results if x.get('resultTypeID')==2),results[-1] if results else None)
  if final is None:continue
  a=m.get('team1',{}).get('teamName');b=m.get('team2',{}).get('teamName');x=final.get('pointsTeam1');y=final.get('pointsTeam2')
  if not (a and b and isinstance(x,int) and isinstance(y,int)):continue
  for name,goals,against in [(a,x,y),(b,y,x)]:
   row=teams.setdefault(name,{'name':name,'played':0,'win':0,'draw':0,'loss':0,'points':0,'gf':0,'ga':0,'image':''})
   row['played']+=1;row['gf']+=goals;row['ga']+=against
   if goals>against:row['win']+=1;row['points']+=3
   elif goals==against:row['draw']+=1;row['points']+=1
   else:row['loss']+=1
 return [dict(row,rank=i+1) for i,row in enumerate(sorted(teams.values(),key=lambda x:(-x['points'],-(x['gf']-x['ga']),-x['gf'],x['name'])))]

def live_from_sources(league,date):
 # ESPN is often the broadest source; alternative APIs are used on failure or empty result.
 errors=[]; empty_success=None
 candidates=[] if league=='aze.1' else [('ESPN',lambda:feeds.espn_games(source_call('ESPN',
  f'https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard?dates={date.replace("-","")}&limit=200',23),league),False)]
 if league in feeds.OPENLIGA:
  candidates.append(('OpenLigaDB',lambda:feeds.openliga_games(source_call('OpenLigaDB',feeds.openliga_matches_url(date,league),120),league,date),True))
 if league in feeds.SPORTSDB:
  candidates.append(('TheSportsDB',lambda:feeds.sportsdb_games(source_call('TheSportsDB',feeds.sportsdb_matches_url(date,league),180),league),True))
 # football-data.org: opt-in registered free token; delayed scores, never claimed live.
 if league in open_feeds.FOOTBALL_DATA_CODES and os.environ.get('FOOTBALL_DATA_TOKEN'):
  def delayed_fixtures():
   path=open_feeds.football_data_path(league,date)
   return open_feeds.parse_football_data_matches(open_feeds.fetch_football_data(path,os.environ['FOOTBALL_DATA_TOKEN']),league,date)
  candidates.append(('football-data.org (pulsuz, gecikmiş)',delayed_fixtures,True))
 # The public-domain JSON archive is historical only. Never fill current live scores with it.
 historical_url=open_feeds.openfootball_url(league,date)
 if historical_url:
  candidates.append(('OpenFootball CC0 (tarixi)',lambda:open_feeds.parse_openfootball(
   source_call('OpenFootball CC0',historical_url,21600),league,date),True))
 for name,fn,partial in candidates:
  try:
   rows=fn()
   if not isinstance(rows,list):raise ValueError('Uyğunsuz məlumat formatı')
   result={'items':rows,'available':True,'partial':partial,'source':name,
     'message':('Pulsuz plan məhdud sayda matç qaytara bilər.' if partial else '')}
   if rows:
    snapshot_save('matches',league,date,result)
    return result
   if empty_success is None:empty_success=result
  except Exception as ex:errors.append(name+': '+type(ex).__name__)
 if empty_success is not None:return empty_success
 prior=snapshot_load('matches',league,date)
 if prior:return prior
 return {'items':[],'available':False,'source':'Bağlantı alınmadı',
   'message':'Yoxlanan mənbələr: '+', '.join(errors)+'; serverdəki Mənbə diaqnostikasına baxın.'}


def table_from_sources(league):
 errors=[]; empty_success=None
 candidates=[] if league=='aze.1' else [('ESPN',lambda:espn_standings(league))]
 if league in feeds.OPENLIGA:
  date=_dt.date.today().isoformat()
  candidates.append(('OpenLigaDB',lambda:feeds.openliga_table(source_call('OpenLigaDB',feeds.openliga_table_url(league,date),900))))
 if league in feeds.SPORTSDB:
  candidates.append(('TheSportsDB',lambda:feeds.sportsdb_table(source_call('TheSportsDB',feeds.sportsdb_table_url(league),900))))
 if league in open_feeds.FOOTBALL_DATA_CODES and os.environ.get('FOOTBALL_DATA_TOKEN'):
  def delayed_table():
   path=open_feeds.football_data_path(league,table=True)
   return open_feeds.parse_football_data_table(open_feeds.fetch_football_data(path,os.environ['FOOTBALL_DATA_TOKEN']))
  candidates.append(('football-data.org (pulsuz, gecikmiş)',delayed_table))
 for name,fn in candidates:
  try:
   rows=fn()
   if not isinstance(rows,list):raise ValueError('Uyğunsuz cədvəl')
   result={'items':rows,'available':True,'source':name,'partial':name!='ESPN'}
   if rows:
    snapshot_save('table',league,'',result)
    return result
   if empty_success is None:empty_success=result
  except Exception as ex:errors.append(name+': '+type(ex).__name__)
 if empty_success is not None and league!='aze.1':return empty_success
 prior=snapshot_load('table',league,'')
 if prior:return prior
 return {'items':[],'available':False,'message':('Azərbaycan Premyer Liqasının cari cədvəli mənbədən alınmadı. Rəsmi PFL cədvəlinə baxın.' if league=='aze.1' else 'Cədvəl mənbələri əlçatan deyil: '+', '.join(errors))}


def media_by_qid(qid,kind='players',retry=False):
 # Every image must be tied to a verified Wikidata QID. No name-only guessing.
 if kind not in ('players','coaches','teams') or not QID.fullmatch(qid or ''):
  return {'url':'','source':'Təsdiqlənmiş kimlik yoxdur'}
 if not retry:
  known=extra_media.cache_load(qid,kind)
  if known and known.get('url'):return known
 if kind=='players' and not retry:
  try:
   media=json.loads((ROOT/'featured_media.js').read_text(encoding='utf8').split('=',1)[1].rstrip(';'))
   if qid in media:return {'url':media[qid],'source':'Wikimedia Commons · seçilmiş foto'}
  except (OSError,ValueError):pass
 e=wd_entities([qid]).get(qid,{})
 if not e:return {'url':'','source':'Wikidata kimliyi əlçatan deyil'}
 if kind in ('players','coaches') and (wd_kind(e)=='teams' or (claims(e,'P154') and not claims(e,'P106') and not claims(e,'P54'))):
  return {'url':'','source':'Profil növü Wikidata kimliyi ilə uyğun deyil'}
 if kind=='teams' and wd_kind(e) in ('players','coaches'):
  return {'url':'','source':'Profil növü Wikidata kimliyi ilə uyğun deyil'}
 filename=entity_media_filename(e,kind)
 # A failed image must fall through to a different verified source when retried.
 if filename and (not retry or kind=='teams'):
  return {'url':'https://commons.wikimedia.org/wiki/Special:FilePath/'+urllib.parse.quote(filename,safe='')+'?width=300',
          'source':'Wikidata / Wikimedia Commons','imagePage':extra_media.commons_file_page(filename),
          'verifiedQid':qid,'kind':kind}
 images,complete=extra_media.verified_page_images([qid],kind,get_json,refresh=retry)
 result=images.get(qid)
 if result:return result
 if filename and not retry:
  return {'url':'https://commons.wikimedia.org/wiki/Special:FilePath/'+urllib.parse.quote(filename,safe='')+'?width=300',
          'source':'Wikidata / Wikimedia Commons','imagePage':extra_media.commons_file_page(filename),
          'verifiedQid':qid,'kind':kind}
 return {'url':'','source':'Sərbəst təsdiqlənmiş media tapılmadı' if complete else 'Media mənbələri əlçatan deyil',
         'complete':complete}

def send_data(path,params):
  # Explicit CC0 archive endpoint: historical data is never labeled live.
  if path=='/api/history-leagues':
   return {'items':[{'id':key,'name':name} for key,(_,name) in historical_archive.LEAGUES.items()],
           'startYear':historical_archive.START_YEAR,
           'endYear':historical_archive.END_YEAR,
           'source':'OpenFootball CC0','live':False}
  if path=='/api/history-bundle':
   return historical_archive.bundle(
       params.get('league',['eng.1'])[0],
       params.get('season',['2025-26'])[0],
       get_json)
  if path=='/api/history':
   try:
    return historical_archive.view(
       params.get('league',['eng.1'])[0],params.get('season',['2025-26'])[0],
       get_json,params.get('limit',['60'])[0],params.get('offset',['0'])[0],
       params.get('team',[''])[0])
   except (TypeError,ValueError):
    return {'available':False,'items':[],'live':False,'message':'Tarixi axtarış parametrləri düzgün deyil.'}
 if path=='/api/season-stats':
  identifier=params.get('id',[''])[0][:120]
  if not (QID.fullmatch(identifier) or identifier in CATBYID or re.fullmatch(r'r[ctp][a-z0-9]{8,30}|reep_[a-z][a-f0-9]{8,30}',identifier)):
   return {'available':False,'items':[],'message':'Yanlış futbolçu kimliyi','source':'TheSportsDB V1 Free'}
  try:
   data=send_data('/api/profile',{'id':[identifier]})
   profile=data.get('profile') if isinstance(data,dict) else None
   if not profile:
    return {'available':False,'items':[],'message':'Təsdiqlənmiş futbolçu profili tapılmadı.','source':'TheSportsDB V1 Free'}
   return season_stats.lookup(profile,get_json)
  except Exception:
   return {'available':False,'items':[],'message':'Pulsuz mövsüm statistikası mənbəsinə qoşulmaq mümkün olmadı.','source':'TheSportsDB V1 Free'}
 if path=='/api/status':return {'ok':True,'backend':True,'version':'0.9.52-local','catalog':len(CATALOG),'world':world_db.counts(),'liveGuaranteed':False,'livePollingSeconds':25,'canInstall':True,'wikipedia':{'mode':'on_demand_verified_qid','verifiedSeedCount':len(wiki.SEED),'linkedQids':sum(x['linked'] for kind,x in world_db.qid_coverage().items() if kind in ('players','teams','coaches')),'teamProfiles':True,'shortExtracts':True}}
 if path=='/api/media-status':return {'source':'Verified Wikidata P18/P154 + free Wikipedia pageimages','cached':extra_media.cache_stats(),'linked':world_db.qid_coverage(),'allProfilesGuaranteed':False,'licensing':'Per-file Wikimedia Commons license applies'}
 if path=='/api/leagues':return {'items':[{'id':k,'name':v,'automatic':k in league_catalog.CORE_LEAGUES} for k,v in league_catalog.ALL_LEAGUES.items()],'count':len(league_catalog.ALL_LEAGUES),'note':'Kataloqda olmaq bu turnirin cari cədvəlinin mütləq işləməsi demək deyil.'}
 if path=='/api/sources':return {'sources':SOURCE_STATUS,
  'providers':['ESPN (qeyri-rəsmi)','OpenLigaDB (ODbL icma)','TheSportsDB V1 (pulsuz məhdud məlumat)','Wikipedia/Wikidata (mənbəli profil)','OpenFootball (CC0, tarixi matçlar)','football-data.org (qeydiyyatlı pulsuz, gecikmiş nəticələr)'],
  'configured':{'openFootball':True,'openLigaDB':True,'theSportsDBFree':True,'footballDataFreeToken':bool(os.environ.get('FOOTBALL_DATA_TOKEN'))},
  'notes':{'openFootball':'Tarixi nəticələr üçündür, canlı hesab deyil','footballDataFreeToken':'Yalnız serverdə FOOTBALL_DATA_TOKEN env varsa işləyir; pulsuz plan 10 sorğu/dəqiqə, gecikmiş nəticələr','theSportsDBFree':'Bütün futbolçuların asistləri mövcud deyil; mobil mağaza nəşri üçün ayrıca şərtlər'},
  'internetVerifiedHere':False}
 if path=='/api/photos':
  values=params.get('qids',[''])[0].split(',')[:20]
  kind=params.get('kind',['players'])[0]
  if kind not in ('players','coaches','teams'):return {'items':{},'details':{},'found':0,'complete':False}
  qids=list(dict.fromkeys(q for q in values if QID.fullmatch(q)))
  urls={};details_map={};wd_healthy=True
  curated={}
  if kind=='players':
   try:curated=json.loads((ROOT/'featured_media.js').read_text(encoding='utf8').split('=',1)[1].rstrip(';'))
   except (OSError,ValueError):pass
  for qid in qids:
   if qid in curated:
    urls[qid]=curated[qid]
    details_map[qid]={'url':curated[qid],'source':'Seçilmiş Wikimedia foto','verifiedQid':qid,'kind':kind}
  remaining=[qid for qid in qids if qid not in urls]
  blocked=set()
  if remaining:
   try:
    entities=wd_entities(remaining)
    for qid in remaining:
     e=entities.get(qid,{})
     if kind=='teams' and wd_kind(e) in ('players','coaches'):
      blocked.add(qid);continue
     if kind in ('players','coaches') and (wd_kind(e)=='teams' or (claims(e,'P154') and not claims(e,'P106') and not claims(e,'P54'))):
      blocked.add(qid);continue
     filename=entity_media_filename(e,kind)
     if filename:
      url='https://commons.wikimedia.org/wiki/Special:FilePath/'+urllib.parse.quote(filename,safe='')+'?width=240'
      urls[qid]=url
      details_map[qid]={'url':url,'source':'Wikidata / Wikimedia Commons',
                        'imagePage':extra_media.commons_file_page(filename),
                        'verifiedQid':qid,'kind':kind}
   except Exception:wd_healthy=False
  missing=[qid for qid in remaining if qid not in urls and qid not in blocked]
  fallback_complete=True
  if missing:
   added,fallback_complete=extra_media.verified_page_images(missing,kind,get_json)
   for qid,data in added.items():
    urls[qid]=data['url'];details_map[qid]=data
  return {'items':urls,'details':details_map,'requested':len(qids),'found':len(urls),
          'complete':wd_healthy and fallback_complete,
          'source':'Wikidata + QID-təsdiqli Wikipedia (sərbəst pageimages)'}
 if path=='/api/world/countries':return {'items':world_db.countries(),'installed':bool(world_db.counts())}
 if path=='/api/install-status':
  with INSTALL_LOCK: state=INSTALL.copy()
  state['world']=world_db.counts()
  state['files']={'entities':(ROOT/'entities.csv.gz').exists(),'overlay':(ROOT/'overlay_links.csv.gz').exists()}
  return state
 if path=='/api/search':
  q=params.get('q',[''])[0].strip()[:80];kind=params.get('kind',['all'])[0]
  country=params.get('country',[''])[0].strip()[:100]
  try:offset=max(0,min(3_500_000,int(params.get('offset',['0'])[0])))
  except:offset=0
  if kind not in ['all','players','teams','coaches']:return {'items':[],'error':'Yanlış filtr'}
  local=local_search(q,kind,limit=100) if q else [x for x in CATALOG if kind=='all' or x['kind']==kind]
  world,ready=world_db.search(q,kind,limit=75,offset=offset,country=country)
  if ready:
   # Always return real register rows first, never count the catalogue as part of the archive.
   curated=(local if q and offset==0 and not country else [])
   by_name={}
   for row in world:
    if row.get('qid') and row.get('country'):
     by_name.setdefault((world_db.normal(row['name']),world_db.normal(row['country'])),set()).add(row['qid'])
   verified=[]
   for row in curated:
    mapped=people.VERIFIED_LEGACY_QIDS.get(row['id'])
    candidates=by_name.get((world_db.normal(row['name']),world_db.normal(row.get('country'))),set())
    if not mapped and len(candidates)==1:mapped=next(iter(candidates))
    verified.append({**row,'qid':mapped} if mapped else row)
   # Suppress only explicitly reviewed *unlinked* catalogue homonyms in
   # the displayed search page. Never rewrite or assign a QID to them.
   # The original register records remain accessible by their own IDs.
   deduplicated=people.suppress_reviewed_display_duplicates(verified + world)
   out=people.unify(deduplicated)
   return {'items':out,'online':False,'source':'Reep CC0 yerli dünya arxivi','worldInstalled':True,'nextOffset':offset+75 if len(world)==75 else None,'registryCount':world_db.counts()}
  if not q:
   page=local[offset:offset+75]
   return {'items':people.unify(page),'online':False,'source':'Başlanğıc kataloq','worldInstalled':False,'nextOffset':offset+75 if offset+75<len(local) else None,'count':len(local)}
  if offset>0:return {'items':[],'worldInstalled':False,'nextOffset':None}
  try:
   remote=wd_search(q,kind)
   merged=people.unify(local+remote)
   return {'items':merged[:100],'online':True,'source':'Wikidata + başlanğıc kataloq','worldInstalled':False}
  except Exception:
   return {'items':people.unify(local[:75]),'online':False,'source':'Yerli kataloq','worldInstalled':False,'message':'Xarici server cavab vermədi; yerli real adlar göstərilir.'}
 if path=='/api/profile':
  identifier=params.get('id',[''])[0]
  local=CATBYID.get(identifier)
  alias_qid=people.VERIFIED_LEGACY_QIDS.get(identifier,'') or (world_db.unique_verified_identity(local.get('name',''),local.get('country','')) if local and local.get('kind') in ('players','coaches') else '')
  profile_identifier=world_db.preferred_person_id(alias_qid or (identifier if QID.fullmatch(identifier) else '')) or identifier
  world_profile=world_db.profile(profile_identifier)
  profile=world_profile or None
  if profile:
   qid=profile.get('wikidataId','')
   if qid and qid not in wiki.SEED:
    try:
     wd=wd_profile(qid,profile.get('kind'))
     if wd:
      profile.update({'image':wd.get('image',''),'position':wd.get('position',''),'clubs':wd.get('clubs',[]),'coached':wd.get('coached',[]),'awards':wd.get('awards',[]),'birth':wd.get('birth',''),'death':wd.get('death',''),'lifeStatus':wd.get('lifeStatus','unknown'),'roles':list(dict.fromkeys(profile.get('roles',[])+wd.get('roles',[])))})
    except Exception:pass
  elif QID.fullmatch(identifier):
   try:profile=wd_profile(identifier)
   except Exception:profile=None
   if profile is None and identifier in wiki.SEED:
    snapshot=wiki.SEED[identifier]
    profile={'id':identifier,'name':snapshot.get('name',identifier),'kind':snapshot.get('wikiKind','players'),'source':'Wikipedia · təsdiqlənmiş tarixi görüntü','wikidataId':identifier}
  if profile is None and local:profile=dict(local)
  if profile is None:return {'profile':None,'online':False,'message':'Bu profilə dair məlumat tapılmadı.'}
  qid=profile.get('wikidataId') or profile.get('qid') or (identifier if QID.fullmatch(identifier) else '')
  if qid and profile.get('kind') in ('players','coaches','teams'):
   # Always try on-demand Wikipedia first; curated snapshots are offline fallback.
   info=wiki.enrich(qid,get_json,kind=profile.get('kind')) or wiki.SEED.get(qid)
  else:
   info=wiki.seed_by_profile(profile)
  if info:profile=wiki.with_wikipedia(profile,info)
  elif local and not profile.get('clubs'):profile['localHistoricalClubs']=local.get('clubs',[])
  # Only identity-verified club profiles may be linked to curated career rows.
  # These historical links are not a claim that these people are the current roster.
  if profile.get('kind')=='teams' and QID.fullmatch(qid or ''):
   profile['historicalConnections']=club_history.historical_links(
    profile.get('name',''), wiki.SEED, qid,
    aliases=[profile.get('fullName',''),profile.get('shortName','')])

  # The same person can have multiple historical football and coaching rows.
  # They are roles of one QID, not independent people to show as duplicates.
  profile=people.decorate(profile)
  if alias_qid and not profile.get('wikidataId'):profile['wikidataId']=alias_qid
  if profile.get('qid') or profile.get('wikidataId'):
   profile['otherRoles']=[]
  if profile.get('clubs') and profile.get('coached'):
   profile['roles']=list(dict.fromkeys(people.roles_of(profile)+['players','coaches']))
  # Opt in recently accessed, verified identities to a bounded background refresh.
  # No scrape of all 506207 records; death/club facts remain source-attributed.
  if QID.fullmatch(qid or '') and profile.get('kind') in ('players','coaches','teams'):
   meta=profile_auto_updates.watch(qid,profile['kind'])
   if meta:profile['updateStatus']=meta
  return {'profile':profile,'online':bool(profile.get('image')),'source':profile.get('source','Reep CC0')}
 if path=='/api/wikipedia-refresh':
  identifier=params.get('id',[''])[0]
  profile=world_db.profile(identifier) or CATBYID.get(identifier,{})
  qid=profile.get('wikidataId') or profile.get('qid') or (identifier if QID.fullmatch(identifier) else '')
  if not QID.fullmatch(qid or '') or profile.get('kind') not in ('players','coaches','teams'):return {'available':False,'message':'Bu profilin təsdiqlənmiş Wikipedia bağlantısı yoxdur.'}
  data=wiki.enrich(qid,get_json,refresh=True,kind=profile.get('kind'))
  updated=bool(data and not data.get('verifiedSnapshot',False))
  return {'available':bool(data),'updated':updated,'data':data or {},'message':'Wikipedia məlumatı yeniləndi' if updated else 'Yalnız saxlanmış məlumat var; canlı Wikipedia yeniləməsi təsdiqlənmədi.'}
 if path=='/api/live':
  league=params.get('league',['eng.1'])[0];date=params.get('date',[''])[0]
  if (league not in LEAGUES and league!='all') or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',date):return {'items':[],'available':False,'message':'Liqa və ya tarix düzgün deyil'}
  try:_dt.date.fromisoformat(date)
  except ValueError:return {'items':[],'available':False,'message':'Tarix mövcud deyil'}
  return live_center.view(league,date,live_from_sources)
 if path=='/api/standings':
  league=params.get('league',['eng.1'])[0]
  if league not in LEAGUES:return {'items':[],'available':False,'message':'Liqa dəstəklənmir'}
  return table_from_sources(league)
 if path=='/api/roster':
  league=params.get('league',[''])[0];id=params.get('id',[''])[0]
  if league not in LEAGUES or not id.isdigit():return {'items':[],'available':False}
  try:
   j=get_json(f'https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/teams/{id}/roster',300)
   result=[];seen=set()
   def collect(items):
    if isinstance(items,list):
     for item in items:collect(item)
     return
    if not isinstance(items,dict):return
    # ESPN may return grouped position lists, or a flat athlete list.
    athlete=items.get('athlete') if isinstance(items.get('athlete'),dict) else items
    name=athlete.get('displayName') or athlete.get('fullName')
    if name:
     athlete_id=str(athlete.get('id') or '')
     key=athlete_id or name.casefold()
     if key not in seen:
      seen.add(key)
      photo=athlete.get('headshot') or ''
      position=athlete.get('position') or {}
      result.append({'id':athlete_id,'name':name,
                     'image':photo.get('href','') if isinstance(photo,dict) else photo,
                     'position':position.get('displayName','') if isinstance(position,dict) else str(position),
                     'number':athlete.get('jersey','')})
    for key in ('items','athletes'):
     if isinstance(items.get(key),list):collect(items[key])
   collect(j.get('athletes',[]) if isinstance(j,dict) else [])
   return {'items':result,'available':bool(result),'source':'ESPN (qeyri-rəsmi)',
           'message':'' if result else 'ESPN bu klub üçün təsdiqlənmiş cari heyət qaytarmadı.'}
  except Exception:return {'items':[],'available':False,'message':'Cari heyət mənbəyi əlçatan deyil.'}
 if path=='/api/photo':
  qid=params.get('qid',[''])[0].strip()
  kind=params.get('kind',['players'])[0]
  if kind not in ('players','teams','coaches'):return {'url':'','source':'Profil növü düzgün deyil'}
  if not QID.fullmatch(qid):return {'url':'','source':'Kimlik bağlantısı yoxdur'}
  try:return media_by_qid(qid,kind,retry=params.get('retry',['0'])[0]=='1')
  except Exception:return {'url':'','source':'Şəkil mənbəsinə çıxış yoxdur'}
 if path=='/api/match-detail':
  # Only three fixed upstream hosts are reachable. No arbitrary URL or hostname input.
  provider=params.get('provider',[''])[0]
  match_id=params.get('id',[''])[0]
  league=params.get('league',[''])[0]
  if not re.fullmatch(r'[1-9][0-9]{0,11}', match_id) or provider not in ('espn','sportsdb','open'):
   return {'available':False,'events':[],'statistics':[],'message':'Matç identifikatoru düzgün deyil.'}
  if provider=='espn' and league not in LEAGUES:
   return {'available':False,'events':[],'statistics':[],'message':'Liqa düzgün deyil.'}
  if provider=='espn':
   try:
    j=source_call('ESPN',f'https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/summary?event={match_id}',180)
    return details.espn_details(j)
   except Exception:
    return details.empty_details('ESPN (qeyri-rəsmi)','ESPN matç məlumatına hazırda çıxış yoxdur.')
  if provider=='open':
   try:
    j=source_call('OpenLigaDB','https://api.openligadb.de/getmatchdata/'+match_id,180)
    return details.openliga_details(j)
   except Exception:
    return details.empty_details('OpenLigaDB','Bu matçın qol hadisələri əlçatan deyil.')
  # TheSportsDB v1 free key is public; 3 separate requests may individually be empty/limited.
  path_base='https://www.thesportsdb.com/api/v1/json/123/'
  found={}; missing=[]
  for key,route in [('lineup','lookuplineup.php'),('stats','lookupeventstats.php'),('timeline','lookuptimeline.php')]:
   try:
    found[key]=source_call('TheSportsDB',path_base+route+'?id='+match_id,300)
   except Exception:
    found[key]={};missing.append(key)
  result=details.sportsdb_details(found['lineup'],found['stats'],found['timeline'])
  if missing:
   result['partial']=True
   result['message']=(result['message']+' ' if result['message'] else '')+'Mənbənin bəzi hissələri əlçatan deyil: '+', '.join(missing)
  return result
 if path=='/api/summary':
  league=params.get('league',[''])[0];id=params.get('id',[''])[0]
  if league not in LEAGUES or not id.isdigit():return {'events':[],'available':False}
  try:
   j=get_json(f'https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/summary?event={id}',120)
   plays=j.get('scoringPlays') or j.get('plays') or j.get('details') or []
   return {'events':[{'text':p.get('text') or p.get('description') or p.get('type',{}).get('text',''),'clock':p.get('clock',{}).get('displayValue','')} for p in plays[:70] if isinstance(p,dict)],'available':True}
  except Exception:return {'events':[],'available':False}
 return None

def set_install(**kw):
 with INSTALL_LOCK:INSTALL.update(kw)

def run_install():
 import import_world
 try:
  set_install(state='downloading',message='Reep arxivi endirilir; bu proqram pəncərəsini açıq saxla',done=False,error='')
  archive=ROOT/'entities.csv.gz';overlay=ROOT/'overlay_links.csv.gz'
  if not archive.exists():import_world.download([import_world.PINNED,import_world.MIRROR],archive,import_world.SHA256)
  if not overlay.exists():
   try:import_world.download([import_world.OVERLAY_URL],overlay,import_world.OVERLAY_SHA)
   except Exception:pass
  set_install(state='indexing',message='Futbolçu, klub və məşqçilər SQLite bazasına idxal edilir')
  counts=import_world.install(archive,overlay if overlay.exists() else None)
  set_install(state='ready',message='Dünya arxivi quraşdırıldı: '+str(sum(counts.values()))+' qeyd',done=True,error='')
 except Exception as ex:
  set_install(state='error',message='Yükləmə və ya idxal alınmadı',done=True,error=str(ex)[:240])

def start_install():
 with INSTALL_LOCK:
  if INSTALL['state'] in ('downloading','indexing'):return False
  INSTALL.update({'state':'downloading','message':'Başladılır','bytes':0,'done':False,'error':''})
 threading.Thread(target=run_install,name='world-database-import',daemon=True).start()
 return True

class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
 def log_message(self,fmt,*args):pass
 def do_POST(self):
  # Browser forms from unrelated sites must not start a large database installation.
  origin=self.headers.get('Origin','')
  if origin:
   parsed_origin=urllib.parse.urlsplit(origin)
   own_host=self.headers.get('Host','')
   if parsed_origin.scheme!='http' or parsed_origin.netloc!=own_host or parsed_origin.hostname not in ('127.0.0.1','localhost'):
    return self.json_response(403,{'error':'Yalnız yerli proqramın sorğularına icazə verilir'})
  import import_world
  parsed=urllib.parse.urlsplit(self.path)
  if parsed.path=='/api/install-start':
   started=start_install();return self.json_response(200,{'started':started,'state':INSTALL['state']})
  if parsed.path!='/api/install-upload':return self.json_response(404,{'error':'Not found'})
  kind=urllib.parse.parse_qs(parsed.query).get('kind',[''])[0]
  if kind not in ('entities','overlay'):return self.json_response(400,{'error':'Yalnız entities və overlay faylları qəbul olunur'})
  with INSTALL_LOCK:
   if INSTALL['state'] in ('downloading','indexing'):return self.json_response(409,{'error':'İdxal davam edir'})
  try:n=int(self.headers.get('Content-Length','0'))
  except:n=0
  if not 20<n<160*1024*1024:return self.json_response(413,{'error':'Fayl ölçüsü düzgün deyil; ən çox 160 MB'})
  target=ROOT/('entities.csv.gz' if kind=='entities' else 'overlay_links.csv.gz');temp=target.with_suffix('.uploading')
  expected=import_world.SHA256 if kind=='entities' else import_world.OVERLAY_SHA
  try:
   digest=hashlib.sha256();remaining=n
   with temp.open('wb') as out:
    while remaining>0:
     chunk=self.rfile.read(min(256*1024,remaining))
     if not chunk:raise ValueError('Yarımçıq fayl')
     out.write(chunk);digest.update(chunk);remaining-=len(chunk)
   if digest.hexdigest().lower()!=expected.lower():raise ValueError('SHA-256 uyğun deyil. Yalnız 2026-10-25.1 rəsmi buraxılışı qəbul edilir.')
   os.replace(temp,target)
   return self.json_response(200,{'ok':True,'type':kind,'message':'Fayl doğrulandı; idxalı başlat düyməsini bas'})
  except Exception as ex:
   temp.unlink(missing_ok=True);return self.json_response(422,{'error':str(ex)[:240]})
 def json_response(self,code,payload):
  raw=json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode('utf8')
  self.send_response(code);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
 def do_GET(self):
  parsed=urllib.parse.urlsplit(self.path)
  if parsed.path.startswith('/api/'):
   params=urllib.parse.parse_qs(parsed.query)
   try:
    payload=send_data(parsed.path,params)
    code=200 if payload is not None else 404
    if payload is None:payload={'error':'Not found'}
   except Exception: code=503;payload={'error':'Məlumat alına bilmədi','available':False}
   raw=json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode('utf-8')
   self.send_response(code);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
   return
  # Serve ONLY frontend assets. SQLite, source code, local logs and uploads never leave this process.
  public={'/index.html','/app.js','/catalog.js','/featured_media.js','/coach_tactics.js','/styles.css','/assets/icon.svg'}
  requested=urllib.parse.unquote(parsed.path)
  if requested in ('','/'):requested='/index.html'
  if requested not in public:
   self.send_error(404)
   return
  self.path=requested
  super().do_GET()

def main():
 ap=argparse.ArgumentParser(description='MATCHLAB AZ — HTML + local server (no VBS/PYW/CMD launcher)')
 ap.add_argument('--port',type=int,default=8765,help='Default 8765; 0 chooses a free port')
 ap.add_argument('--no-browser',action='store_true',help='Do not open browser automatically')
 ns=ap.parse_args()
 must_have=['index.html','app.js','styles.css','world_football.sqlite']
 missing=[name for name in must_have if not (ROOT/name).is_file()]
 if missing:
  print('XƏTA: Bu fayllar yoxdur: '+', '.join(missing))
  print('ZIP arxivini tam çıxart və server.py faylını çıxarılan qovluqdan aç.')
  return 2
 try:
  server=ThreadingHTTPServer(('127.0.0.1',ns.port),Handler)
 except OSError as exc:
  if ns.port==8765:
   print('8765 portu məşğuldur, avtomatik başqa boş port seçilir.',flush=True)
   server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
  else:
   print('Serveri başlatmaq mümkün olmadı: '+str(exc),flush=True)
   return 1
 actual_port=server.server_address[1]
 url=f'http://127.0.0.1:{actual_port}/'
 print('MATCHLAB AZ — HTML + SERVER',flush=True)
 print('Brauzer ünvanı: '+url,flush=True)
 print('Server işləyərkən bu Python pəncərəsini bağlama. Dayandırmaq üçün Ctrl+C.',flush=True)
 if not ns.no_browser:
  threading.Timer(0.6,lambda:webbrowser.open(url)).start()
 try:server.serve_forever(poll_interval=0.2)
 except KeyboardInterrupt:pass
 finally:server.server_close()
 return 0
if __name__=='__main__':raise SystemExit(main())
