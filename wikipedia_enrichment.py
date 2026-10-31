"""Wikipedia/Wikidata football biography enrichment with a disk cache.

No bulk scraping at startup. Only follow Wikidata-verified sitelinks: never
associate an arbitrary name with a similarly named person. Stats extracted
from the football biography infobox are SENIOR DOMESTIC LEAGUE apps/goals, not
all-competition totals. Missing values stay null (never zero).
"""
import datetime as dt
import json
import re
import sqlite3
import threading
import unicodedata
import urllib.parse
from pathlib import Path

BASE=Path(__file__).resolve().parent
CACHE_DB=BASE/'wikipedia_profiles.sqlite'
SEED=json.loads((BASE/'verified_profiles.json').read_text(encoding='utf-8')) if (BASE/'verified_profiles.json').exists() else {}
VALID_QID=re.compile(r'^Q[1-9][0-9]{0,11}$')
WRITE_LOCK=threading.Lock()
_CACHE_SETUP=False


def clean_text(text):
    """Remove common Wikipedia markup without relying on a full wiki parser."""
    text=str(text or '')
    text=re.sub(r'<!--.*?-->','',text,flags=re.S)
    text=re.sub(r'<ref\b[^>]*>.*?</ref\s*>|<ref\b[^>]*/>', '',text,flags=re.S|re.I)
    text=re.sub(r'<[^>]+>','',text)
    text=re.sub(r'\{\{(?:nowrap|small|flagicon|flag|flagcountry|nobold)\|([^{}|]*)\}\}',r'\1',text,flags=re.I)
    text=re.sub(r'\[\[(?:[^\]|]*\|)?([^\]|]+)\]\]',r'\1',text)
    text=re.sub(r'\[(?:https?://\S+)(?:\s+([^\]]*))?\]',lambda m:m.group(1) or '',text)
    text=re.sub(r"'{2,}", '',text)
    text=re.sub(r'\{\{[^{}]*\}\}', '',text)
    text=re.sub(r'\s+', ' ',text).strip(' \n\t|')
    return text[:250]


def extract_infobox(wikitext):
    """Extract the first {{Infobox football biography}} or equivalent, balanced."""
    if not isinstance(wikitext,str):return ''
    match=re.search(r'\{\{\s*Infobox\s+(?:football\s+(?:biography|player|manager)|soccer\s+(?:player|biography))\b',wikitext,re.I)
    if not match:return ''
    start=match.start();stack=0;i=start
    while i<len(wikitext) and i<start+240_000:
        chunk=wikitext[i:i+2]
        if chunk=='{{':stack+=1;i+=2;continue
        if chunk=='}}':
            stack-=1;i+=2
            if stack==0:return wikitext[start:i]
            continue
        i+=1
    return ''


def split_params(template):
    """Split template fields on top-level | only, allowing nested templates."""
    template=template[2:-2] if template.startswith('{{') and template.endswith('}}') else template
    depth=0;links=0;parts=[];start=0;i=0
    while i<len(template):
        c=template[i:i+2]
        if c=='{{':depth+=1;i+=2;continue
        if c=='}}':depth=max(depth-1,0);i+=2;continue
        if c=='[[':links+=1;i+=2;continue
        if c==']]':links=max(links-1,0);i+=2;continue
        if template[i]=='|' and depth==0 and links==0:
            parts.append(template[start:i]);start=i+1
        i+=1
    parts.append(template[start:])
    fields={}
    for part in parts[1:]:
        if '=' not in part:continue
        k,v=part.split('=',1)
        k=k.strip().lower().replace('_','').replace('-','')
        if k and len(k)<85:fields[k]=v.strip()
    return fields


def numeric(raw):
    if raw is None:return None
    val=clean_text(raw).replace(',','').replace(' ','')
    if not re.fullmatch(r'\d{1,6}',val):return None
    n=int(val)
    return n if n<=99999 else None


def first_year(raw):
    match=re.search(r'\b(?:18|19|20)\d{2}\b',clean_text(raw))
    return int(match.group()) if match else None


def years(raw):
    val=clean_text(raw)
    nums=[int(x) for x in re.findall(r'\b(?:18|19|20)\d{2}\b',val)]
    if not nums:return None,None
    start=nums[0]
    # dash-ended intervals (e.g. 2023–) mean an ongoing season, not a missing historic year
    end=nums[-1] if len(nums)>1 else (None if re.search(r'[–—-]\s*$',val) else start)
    return start,end


def wikipedia_date(raw):
    # Wikidata is preferred, because infobox dates often use templates.
    x=re.search(r'\{\{(?:birth date(?: and age)?|death date(?: and age)?)\s*\|\s*(\d{4})\s*\|\s*(\d{1,2})\s*\|\s*(\d{1,2})',raw or '',re.I)
    if x:
        try:return dt.date(*[int(i) for i in x.groups()]).isoformat()
        except ValueError:pass
    return ''


def parse_football_infobox(source):
    box=extract_infobox(source)
    if not box:return {}
    f=split_params(box)
    player_rows=[];coach_rows=[];national_rows=[]
    # Senior career indexed as years1/clubs1/caps1/goals1. No junior/youth rows.
    indexes=sorted({int(m.group(1)) for key in f if (m:=re.fullmatch(r'(?:years|clubs|caps|goals)(\d+)',key))})
    for n in indexes[:90]:
        team=clean_text(f.get(f'clubs{n}',''))
        if not team:continue
        y0,y1=years(f.get(f'years{n}',''))
        player_rows.append({'name':team,'from':y0,'to':y1,'apps':numeric(f.get(f'caps{n}')),'goals':numeric(f.get(f'goals{n}')),'assists':None,'statScope':'domestic_league'})
    manager_idx=sorted({int(m.group(1)) for key in f if (m:=re.fullmatch(r'(?:manageryears|managerclubs)(\d+)',key))})
    for n in manager_idx[:60]:
        team=clean_text(f.get(f'managerclubs{n}',''))
        if not team:continue
        y0,y1=years(f.get(f'manageryears{n}',''))
        coach_rows.append({'name':team,'from':y0,'to':y1})
    national_idx=sorted({int(m.group(1)) for key in f if (m:=re.fullmatch(r'(?:nationalyears|nationalteam|nationalcaps|nationalgoals)(\d+)',key))})
    for n in national_idx[:45]:
        team=clean_text(f.get(f'nationalteam{n}',''))
        if not team:continue
        y0,y1=years(f.get(f'nationalyears{n}',''))
        national_rows.append({'name':team,'from':y0,'to':y1,'apps':numeric(f.get(f'nationalcaps{n}')),'goals':numeric(f.get(f'nationalgoals{n}'))})
    out={'clubs':player_rows,'coached':coach_rows,'nationalTeams':national_rows}
    if (birth:=wikipedia_date(f.get('birthdate',''))):out['birth']=birth
    if (death:=wikipedia_date(f.get('deathdate',''))):out['death']=death
    if (position:=clean_text(f.get('position',''))):out['position']=position
    return out


def _init():
    global _CACHE_SETUP
    if _CACHE_SETUP:return
    with WRITE_LOCK:
        if _CACHE_SETUP:return
        with sqlite3.connect(CACHE_DB,timeout=10) as con:
            con.execute('PRAGMA journal_mode=WAL')
            con.execute('''CREATE TABLE IF NOT EXISTS enriched (qid TEXT PRIMARY KEY, fetched_utc TEXT NOT NULL, payload TEXT NOT NULL, success INTEGER NOT NULL)''')
        _CACHE_SETUP=True


def cached(qid,refresh_days=14):
    if not VALID_QID.fullmatch(qid or ''):return None
    _init()
    with sqlite3.connect(CACHE_DB,timeout=5) as con:
        row=con.execute('SELECT fetched_utc,payload,success FROM enriched WHERE qid=?',(qid,)).fetchone()
    if not row:return None
    when=dt.datetime.fromisoformat(row[0])
    age=dt.datetime.now(dt.timezone.utc)-when.replace(tzinfo=dt.timezone.utc)
    if age>dt.timedelta(days=refresh_days if row[2] else 1):return None
    return json.loads(row[1])


def store(qid,payload,success):
    if not VALID_QID.fullmatch(qid or ''):return
    _init()
    with sqlite3.connect(CACHE_DB,timeout=10) as con:
        con.execute('INSERT OR REPLACE INTO enriched VALUES(?,?,?,?)',(qid,dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds'),json.dumps(payload,ensure_ascii=False),int(success)))


def wiki_title(wikidata_entity):
    links=wikidata_entity.get('sitelinks',{})
    for site in ('enwiki','trwiki','azwiki'):
        page=links.get(site,{}).get('title')
        if page and not any(part in page.lower() for part in ('list of ','category:','template:')):
            return site[:2],page
    return None,None


def entity_value(entity,prop):
    for s in entity.get('claims',{}).get(prop,[]):
        if s.get('rank')=='deprecated':continue
        raw=s.get('mainsnak',{}).get('datavalue',{}).get('value')
        if raw is not None:return raw
    return None


def remote_enrich(qid,get_json):
    """Pass a request adapter get_json(url,ttl). Failures are handled upstream."""
    url='https://www.wikidata.org/w/api.php?'+urllib.parse.urlencode({'action':'wbgetentities','format':'json','ids':qid,'props':'sitelinks|claims|labels','languages':'az|en|tr'})
    e=get_json(url,86400).get('entities',{}).get(qid,{})
    if not e or e.get('missing') is not None:return None
    lang,title=wiki_title(e)
    if not title:return None
    page_url='https://'+lang+'.wikipedia.org/wiki/'+urllib.parse.quote(title.replace(' ','_'),safe='()_')
    rest='https://'+lang+'.wikipedia.org/w/rest.php/v1/page/'+urllib.parse.quote(title.replace(' ','_'),safe='()_')
    wikitext=get_json(rest,86400).get('source','')
    if not wikitext:
        # Stable wiki Action API fallback for older/unsupported page source formats.
        api='https://'+lang+'.wikipedia.org/w/api.php?'+urllib.parse.urlencode({'action':'query','prop':'revisions','titles':title,'rvprop':'content','rvslots':'main','formatversion':2,'format':'json'})
        response=get_json(api,86400)
        pages=response.get('query',{}).get('pages',[])
        if pages:
            slot=(pages[0].get('revisions') or [{}])[0].get('slots',{}).get('main',{})
            wikitext=slot.get('content') or slot.get('*') or ''
    data=parse_football_infobox(wikitext)
    if not data or not (data.get('clubs') or data.get('coached') or data.get('nationalTeams')):
        data={}
    birth=entity_value(e,'P569');death=entity_value(e,'P570')
    if isinstance(birth,dict) and birth.get('time'):data['birth']=birth['time'].lstrip('+')[:10]
    if isinstance(death,dict) and death.get('time'):data['death']=death['time'].lstrip('+')[:10]
    photo=entity_value(e,'P18')
    if not photo and entity_value(e,'P154'):photo=entity_value(e,'P154')
    if isinstance(photo,str) and len(photo)<240:
        data['image']='https://commons.wikimedia.org/wiki/Special:FilePath/'+urllib.parse.quote(photo,safe='')+'?width=360'
    data['careerSource']='Wikipedia ('+lang+') · senior liqa göstəriciləri'
    data['careerUrl']=page_url
    data['statsChecked']=dt.datetime.now(dt.timezone.utc).date().isoformat()
    data['statsScope']='domestic_league'
    data['statNotice']='Matç və qollar əsasən daxili liqa üçündür; bütün yarışların cəmi deyil. Asist məlum deyilsə, 0 sayılmır.'
    data['wikiMatch']=True
    data['verifiedSnapshot']=False
    return data


def enrich(qid,get_json,refresh=False):
    """Return cached or on-demand Wikipedia data; offline seed for curated stars."""
    if not VALID_QID.fullmatch(qid or ''):return None
    if not refresh:
        found=cached(qid)
        if found is not None:return found or SEED.get(qid)
    try:
        info=remote_enrich(qid,get_json)
        if info:
            store(qid,info,True)
            # Historical editorial snapshots remain fallback if remote infobox lacks useful detail.
            if not info.get('clubs') and not info.get('coached') and qid in SEED:
                return {**SEED[qid],**{k:v for k,v in info.items() if v and k not in ('clubs','coached')}}
            return info
        store(qid,{},False)
    except Exception:
        # Cache miss rather than an empty authoritative profile if requests fail.
        pass
    return SEED.get(qid)


def with_wikipedia(profile,info):
    if not info:return profile
    p=dict(profile)
    for field in ('birth','death','image','position'):
        if info.get(field):p[field]=info[field]
    for field in ('clubs','coached','nationalTeams'):
        if info.get(field):p[field]=info[field]
    for field in ('careerSource','careerUrl','statsChecked','statsAsOf','statsScope','statNotice','wikiMatch','verifiedSnapshot','national'):
        if field in info:p[field]=info[field]
    if p.get('death'):p['lifeStatus']='deceased'
    if info.get('clubs') or info.get('coached'):
        p['source']=(p.get('source','').split(' + Wikipedia')[0] or 'Wikidata')+' + Wikipedia'
        p['statsAvailable']=any(c.get('apps') is not None or c.get('goals') is not None for c in info.get('clubs',[]))
    return p


def seed_by_profile(profile):
    qid=profile.get('wikidataId') or profile.get('qid') or (profile['id'] if VALID_QID.fullmatch(profile.get('id','')) else '')
    if qid and qid in SEED:return SEED[qid]
    # Seed catalogue IDs such as p:pel have been explicitly curated, unlike fuzzy matching.
    return SEED.get(profile.get('id'))
