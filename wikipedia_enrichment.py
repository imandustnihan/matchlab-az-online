"""Wikipedia/Wikidata verified football biography and club enrichment with a disk cache.

No bulk scraping at startup. Only follow Wikidata-verified sitelinks: never
associate an arbitrary name with a similarly named person. Stats extracted
from the football biography infobox are SENIOR DOMESTIC LEAGUE apps/goals, not
all-competition totals. Missing values stay null (never zero). No mass scraping.
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
    text=re.sub(r'<br\s*/?>','; ',text,flags=re.I)
    text=re.sub(r'\{\{\s*(?:hlist|ubl|ubt|unbulleted list|flatlist)\s*\|([^{}]*)\}\}',lambda m:'; '.join(x for x in (clean_text(v) for v in m.group(1).split('|')) if x),text,flags=re.I)
    text=re.sub(r'\{\{\s*plainlist\s*\|','',text,flags=re.I)
    text=text.replace('{{endplainlist}}','').replace('{{Endplainlist}}','')
    text=text.replace('*','; ')
    text=re.sub(r'<ref\b[^>]*>.*?</ref\s*>|<ref\b[^>]*/>', '',text,flags=re.S|re.I)
    text=re.sub(r'<[^>]+>','',text)
    text=re.sub(r'\{\{(?:nowrap|small|flagicon|flag|flagcountry|nobold)\|([^{}|]*)\}\}',r'\1',text,flags=re.I)
    text=re.sub(r'\[\[(?:[^\]|]*\|)?([^\]|]+)\]\]',r'\1',text)
    text=re.sub(r'\[(?:https?://\S+)(?:\s+([^\]]*))?\]',lambda m:m.group(1) or '',text)
    text=re.sub(r"'{2,}", '',text)
    text=re.sub(r'\{\{[^{}]*\}\}', '',text)
    text=re.sub(r'\s*;\s*','; ',text)
    text=re.sub(r'\s+', ' ',text).strip(' \n\t|;')
    return text[:250]


def split_values(raw,limit=12):
    text=clean_text(raw)
    if not text:return []
    text=text.replace(' / ','; ').replace(' • ','; ').replace(' · ','; ')
    parts=[x.strip(' ,') for x in re.split(r';|\u2022|\u00b7|\s{2,}|(?<!\d),(?!\d)',text) if x.strip(' ,')]
    out=[]
    for part in parts:
        if part not in out:
            out.append(part)
        if len(out)>=limit:break
    return out

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


def extract_club_infobox(wikitext):
    """Only football club templates, never unrelated encyclopedic templates."""
    if not isinstance(wikitext,str):return ''
    match=re.search(r'\{\{\s*Infobox\s+(?:football\s+(?:club|team)|soccer\s+club)\b',wikitext,re.I)
    if not match:return ''
    start=match.start();depth=0;i=start
    while i<len(wikitext) and i<start+180_000:
        token=wikitext[i:i+2]
        if token=='{{':depth+=1;i+=2;continue
        if token=='}}':
            depth-=1;i+=2
            if depth==0:return wikitext[start:i]
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
    indexes=sorted({int(m.group(1)) for key in f if (m:=re.fullmatch(r'(?:years|clubs|caps|goals|assists)(\d+)',key))})
    for n in indexes[:90]:
        team=clean_text(f.get(f'clubs{n}',''))
        if not team:continue
        y0,y1=years(f.get(f'years{n}',''))
        player_rows.append({'name':team,'from':y0,'to':y1,'apps':numeric(f.get(f'caps{n}')),'goals':numeric(f.get(f'goals{n}')),'assists':numeric(f.get(f'assists{n}')),'statScope':'domestic_league'})
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
    for field,key in (('fullName','fullname'),('birthPlace','birthplace'),('height','height')):
        if (value:=clean_text(f.get(key,''))):out[field]=value
    # These template values are biographical context, not verified career statistics.
    return out


def parse_club_infobox(source):
    """Conservative Wikipedia club facts; no invented current roster."""
    box=extract_club_infobox(source)
    if not box:return {}
    f=split_params(box)
    out={}
    founded=f.get('founded','')
    date=re.search(r'\{\{\s*(?:start\s*date(?:\s*and\s*age)?|birth\s*date(?:\s*and\s*age)?)\s*\|\s*(\d{4})',founded,re.I)
    if not date:date=re.search(r'\b(?:18|19|20)\d{2}\b',clean_text(founded))
    if date:
        yr=date.group(1) if date.lastindex else date.group(0)
        if 1800<=int(yr)<=dt.date.today().year:out['foundedYear']=int(yr)
    field_map=(
        ('fullName',('fullname','clubname','fullclubname')),
        ('shortName',('shortname','nicknameabbrev')),
        ('stadium',('ground','stadium','arena','homeground')),
        ('city',('city','location','headquarters','basedin')),
        ('country',('country',)),
        ('manager',('manager','headcoach','coach')),
        ('league',('league','competition')),
        ('chairman',('chairman','chairperson','president')),
        ('owner',('owner','owners')),
        ('colors',('colours','colors','colour','color')),
    )
    for target,fields in field_map:
        for field in fields:
            value=clean_text(f.get(field,''))
            if value and len(value)<=180:
                out[target]=value
                break
    nick_raw=''
    for field in ('nickname','nicknames','nickname(s)'):
        nick_raw=f.get(field,'')
        if nick_raw:break
    nicknames=split_values(nick_raw,limit=10)
    if nicknames:
        out['nicknames']=nicknames
        out['nickname']=' · '.join(nicknames[:6])
    raw=f.get('capacity') or f.get('groundcapacity') or ''
    m=re.search(r'(?<!\d)(\d{1,3}(?:[,. ]\d{3})+|\d{4,6})(?!\d)',clean_text(raw))
    if m:
        n=int(re.sub(r'[^\d]','',m.group(1)))
        if 1000<=n<=300000:out['stadiumCapacity']=n
    return out

def article_details(lang,title,qid,get_json):
    """Get a short intro only if pageprops.wikibase_item matches the profile QID."""
    params={'action':'query','format':'json','formatversion':2,'prop':'pageprops|extracts|pageimages',
            'titles':title,'redirects':1,'exintro':1,'explaintext':1,'exchars':800,'piprop':'thumbnail',
            'pithumbsize':360,'pilicense':'free','ppprop':'wikibase_item|disambiguation'}
    url='https://'+lang+'.wikipedia.org/w/api.php?'+urllib.parse.urlencode(params)
    pages=get_json(url,86400).get('query',{}).get('pages',[])
    if not pages or len(pages)!=1:return {}
    page=pages[0];props=page.get('pageprops') or {}
    if page.get('ns')!=0 or 'missing' in page or props.get('wikibase_item')!=qid or 'disambiguation' in props:return {}
    excerpt=re.sub(r'\s+',' ',re.sub(r'[\x00-\x1f\x7f]+',' ',str(page.get('extract') or ''))).strip()[:800]
    thumb=(page.get('thumbnail') or {}).get('source','')
    if not thumb.startswith('https://upload.wikimedia.org/'):thumb=''
    return {'wikiSummary':excerpt,'wikiThumbnail':thumb,'articleVerified':True}


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
    # The cache is an optimization, never an authority: a corrupt/locked SQLite
    # row must not prevent an otherwise valid player or club profile loading.
    try:
        _init()
        with sqlite3.connect(CACHE_DB,timeout=5) as con:
            row=con.execute('SELECT fetched_utc,payload,success FROM enriched WHERE qid=?',(qid,)).fetchone()
        if not row:return None
        when=dt.datetime.fromisoformat(row[0])
        age=dt.datetime.now(dt.timezone.utc)-when.replace(tzinfo=dt.timezone.utc)
        if age>dt.timedelta(days=refresh_days if row[2] else 1):return None
        return json.loads(row[1])
    except (sqlite3.Error, OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None


def store(qid,payload,success):
    if not VALID_QID.fullmatch(qid or ''):return
    _init()
    with sqlite3.connect(CACHE_DB,timeout=10) as con:
        con.execute('INSERT OR REPLACE INTO enriched VALUES(?,?,?,?)',(qid,dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds'),json.dumps(payload,ensure_ascii=False),int(success)))


def wiki_title(wikidata_entity):
    links=wikidata_entity.get('sitelinks',{})
    for site in ('enwiki','trwiki','azwiki','eswiki','dewiki','frwiki','itwiki','ptwiki','ruwiki','nlwiki','plwiki'):
        page=links.get(site,{}).get('title')
        if page and not any(part in page.lower() for part in ('list of ','category:','template:')):
            return site[:2],page
    return None,None


def verified_language_links(wikidata_entity):
    result={}
    for lang in ('az','tr','en','es','de','fr','it','pt','ru','nl','pl'):
        title=(wikidata_entity.get('sitelinks') or {}).get(lang+'wiki',{}).get('title','')
        if isinstance(title,str) and title and not any(x in title.casefold() for x in ('category:','template:','list of ')):
            result[lang]='https://'+lang+'.wikipedia.org/wiki/'+urllib.parse.quote(title.replace(' ','_'),safe='()_')
    return result


def entity_value(entity,prop):
    for s in entity.get('claims',{}).get(prop,[]):
        if s.get('rank')=='deprecated':continue
        raw=s.get('mainsnak',{}).get('datavalue',{}).get('value')
        if raw is not None:return raw
    return None


def entity_values(entity,prop):
    out=[]
    for s in entity.get('claims',{}).get(prop,[]):
        if s.get('rank')=='deprecated':
            continue
        raw=s.get('mainsnak',{}).get('datavalue',{}).get('value')
        if raw is not None:
            out.append(raw)
    return out


def entity_labels(ids,get_json):
    ids=[x for x in dict.fromkeys(ids) if VALID_QID.fullmatch(str(x))]
    if not ids:return {}
    url='https://www.wikidata.org/w/api.php?'+urllib.parse.urlencode({'action':'wbgetentities','format':'json','ids':'|'.join(ids),'props':'labels','languages':'az|tr|en','languagefallback':'1'})
    payload=get_json(url,86400).get('entities',{})
    out={}
    for qid,entity in payload.items():
        label=''
        for lang in ('az','tr','en'):
            value=((entity.get('labels') or {}).get(lang) or {}).get('value')
            if value:
                label=value
                break
        out[qid]=label or qid
    return out


def first_labeled(entity,prop,labels):
    for raw in entity_values(entity,prop):
        if isinstance(raw,dict) and raw.get('id') in labels:
            return labels[raw['id']]
        if isinstance(raw,dict) and raw.get('id'):
            return raw['id']
        if isinstance(raw,str) and raw.strip():
            return raw.strip()
    return ''

def wikidata_date(value):
    """Respect Wikidata precision: year/month-only dates are NOT January 1.

    Wikidata time values represent unknown components using 01 internally;
    precision 9 means only the year is known, 10 the month, and 11 the day.
    """
    if not isinstance(value,dict):return ''
    raw=str(value.get('time') or '')
    match=re.match(r'^\+?(\d{4})-(\d{2})-(\d{2})T',raw)
    if not match:return ''
    yyyy,mm,dd=match.groups()
    try:precision=int(value.get('precision',11))
    except (ValueError,TypeError):return ''
    if precision<9:return ''
    if not 1<=int(mm)<=12:return ''
    if precision==9:return yyyy
    if precision==10:return f'{yyyy}-{mm}'
    try:dt.date(int(yyyy),int(mm),int(dd))
    except ValueError:return ''
    return f'{yyyy}-{mm}-{dd}'



def verified_wikidata_team_history(entity, get_json):
    """Conservative P54 team affiliations with qualifiers; no fabricated senior stats.

    Wikidata P54 may include national/youth teams, and an absent end date does
    not establish a current affiliation. Such rows are labelled as affiliations,
    not senior league statistics, and carry no invented caps/goals/assists.
    """
    statements=(entity.get('claims') or {}).get('P54') or []
    raw=[]
    for statement in statements[:90]:
        if not isinstance(statement,dict) or statement.get('rank')=='deprecated':continue
        team=((statement.get('mainsnak') or {}).get('datavalue') or {}).get('value') or {}
        qid=team.get('id') if isinstance(team,dict) else None
        if not qid or not VALID_QID.fullmatch(str(qid)):continue
        qualifiers=statement.get('qualifiers') or {}
        sport_ids=[((x.get('datavalue') or {}).get('value') or {}).get('id')
                   for x in qualifiers.get('P641',[]) if isinstance(x,dict) and isinstance((x.get('datavalue') or {}).get('value'),dict)]
        if sport_ids and 'Q2736' not in sport_ids:continue
        def qualifying_year(prop):
            for claim in qualifiers.get(prop,[])[:5]:
                if not isinstance(claim,dict):continue
                raw_time=(claim.get('datavalue') or {}).get('value')
                date=wikidata_date(raw_time)
                if date:return int(date[:4])
                # Year-precision qualifiers can encode unknown month/day as 00.
                # Parse only the year, never make up a month or day.
                if isinstance(raw_time,dict):
                    match=re.match(r'^\+?(\d{4})-',str(raw_time.get('time') or ''))
                    try:precision=int(raw_time.get('precision',0))
                    except (ValueError,TypeError):precision=0
                    if match and precision>=9:
                        return int(match.group(1))
            return None
        start,end=qualifying_year('P580'),qualifying_year('P582')
        if start and end and start>end:continue
        raw.append((qid,start,end))
    if not raw:return []
    ids=list(dict.fromkeys(team for team,_,_ in raw))[:80]
    # No guessed labels: a networking failure must not turn QIDs into club names.
    labels={}
    # Wikidata wbgetentities supports bounded ID batches; preserve successful
    # chunks if one API request fails instead of dropping the whole history.
    for i in range(0,len(ids),40):
        try:labels.update(entity_labels(ids[i:i+40],get_json))
        except (OSError,ValueError,KeyError,TypeError):continue
    rows=[]
    for qid,start,end in raw:
        name=labels.get(qid,'')
        if not name or name==qid:continue
        row={'name':name,'statScope':'unspecified_membership','source':'Wikidata P54'}
        if start is not None:row['from']=start
        if end is not None:row['to']=end
        rows.append(row)
        if len(rows)>=60:break
    return rows


def remote_enrich(qid,get_json,kind='players'):
    """Pass a request adapter get_json(url,ttl). Failures are handled upstream."""
    url='https://www.wikidata.org/w/api.php?'+urllib.parse.urlencode({'action':'wbgetentities','format':'json','ids':qid,'props':'sitelinks|claims|labels','languages':'az|en|tr'})
    e=get_json(url,86400).get('entities',{}).get(qid,{})
    if not e or e.get('missing') is not None:return None
    lang,title=wiki_title(e)
    if not title:
        # Many QID-linked people have no Wikipedia article at all. A trusted
        # Wikidata entity can still offer P54 team memberships; distinguish
        # this from an encyclopedia career table and from league statistics.
        if kind not in ('players','coaches'):return None
        affiliations=verified_wikidata_team_history(e,get_json)
        if not affiliations:return None
        return {'clubs':affiliations,'coached':[],'wikiKind':kind,'wikiMatch':False,
                'verifiedSnapshot':False,'careerSource':'Wikidata P54 · mənbəli komanda üzvlüyü',
                'careerUrl':'https://www.wikidata.org/wiki/'+qid,
                'statsScope':'unspecified_membership',
                'statNotice':'Wikipedia məqaləsi yoxdur; Wikidata komanda üzvlüyü göstərilir. Bunlar təsdiqlənmiş senior liqa matçları və ya qol/asist statistikası deyil.'}
    page_url='https://'+lang+'.wikipedia.org/wiki/'+urllib.parse.quote(title.replace(' ','_'),safe='()_')
    details={}
    try:details=article_details(lang,title,qid,get_json)
    except Exception:pass
    # Never parse a Wikipedia infobox unless the actual page's Wikidata QID
    # matches the football identity. A sitelink alone is not confirmation of
    # the current page after redirects or page replacements.
    verified=bool(details.get('articleVerified'))
    if not verified:details={}
    wikitext=''
    if verified:
        rest='https://'+lang+'.wikipedia.org/w/rest.php/v1/page/'+urllib.parse.quote(title.replace(' ','_'),safe='()_')
        try:wikitext=get_json(rest,86400).get('source','')
        except Exception:wikitext=''
        if not wikitext:
            api='https://'+lang+'.wikipedia.org/w/api.php?'+urllib.parse.urlencode({'action':'query','prop':'revisions','titles':title,'rvprop':'content','rvslots':'main','formatversion':2,'format':'json'})
            try:
                response=get_json(api,86400)
                pages=response.get('query',{}).get('pages',[])
                if pages:
                    slot=(pages[0].get('revisions') or [{}])[0].get('slots',{}).get('main',{})
                    wikitext=slot.get('content') or slot.get('*') or ''
            except Exception:pass
    data=(parse_club_infobox(wikitext) if kind=='teams' else parse_football_infobox(wikitext)) if verified else {}
    data.update({k:v for k,v in details.items() if k not in ('wikiThumbnail','articleVerified') and v})
    history_fallback=False
    if kind in ('players','coaches') and not data.get('clubs'):
        # Wikipedia article verified, but no machine-readable football career
        # infobox: use QID-linked Wikidata team memberships as a labelled fallback.
        affiliations=verified_wikidata_team_history(e,get_json)
        if affiliations:
            data['clubs']=affiliations
            history_fallback=True
    if kind=='teams':
        from club_history import parse_honours, parse_squad, colors_from_text, stadium_media
        if verified:
            honours=parse_honours(wikitext)
            squad=parse_squad(wikitext)
            if honours:data['honours']=honours
            if squad:
                data['squadSnapshot']=squad
                data['squadSource']='Wikipedia ('+lang+') · Current squad (tarixə bağlı görüntü)'
                data['squadChecked']=dt.datetime.now(dt.timezone.utc).date().isoformat()
            # Capture hex values only when declared in the matched infobox.
            color_match=re.search(r'(?im)^\s*\|\s*(?:colors|colours|colour|color)\s*=\s*([^\n]+)',wikitext)
            if color_match:
                swatches=colors_from_text(color_match.group(1))
                if swatches:data['colorHexes']=swatches
        # Stadium P115 -> P18 is a stadium photograph, never a club crest.
        try:
            stadium=stadium_media(e,get_json)
            if stadium:data.update(stadium)
        except Exception:
            pass
        data['clubDataVersion']=2
    if kind=='teams':
        founded=entity_value(e,'P571')
        if not data.get('foundedYear') and isinstance(founded,dict) and founded.get('time'):
            match=re.search(r'(?:18|19|20)\d{2}',founded['time'])
            if match:data['foundedYear']=int(match.group())
        related_ids=[]
        for prop in ('P17','P118','P115','P159','P286','P488','P127'):
            for raw in entity_values(e,prop):
                if isinstance(raw,dict) and VALID_QID.fullmatch(str(raw.get('id') or '')):
                    related_ids.append(raw['id'])
        labels=entity_labels(related_ids,get_json) if related_ids else {}
        if not data.get('country'):
            vals=[labels.get(x.get('id'),x.get('id')) for x in entity_values(e,'P17') if isinstance(x,dict) and x.get('id')]
            vals=[x for x in vals if x]
            if vals:data['country']=', '.join(dict.fromkeys(vals))
        if not data.get('league'):
            value=first_labeled(e,'P118',labels)
            if value:data['league']=value
        if not data.get('stadium'):
            value=first_labeled(e,'P115',labels)
            if value:data['stadium']=value
        if not data.get('city'):
            value=first_labeled(e,'P159',labels)
            if value:data['city']=value
        if not data.get('manager'):
            value=first_labeled(e,'P286',labels)
            if value:data['manager']=value
        if not data.get('chairman'):
            value=first_labeled(e,'P488',labels)
            if value:data['chairman']=value
        if not data.get('owner'):
            owners=[labels.get(x.get('id'),x.get('id')) for x in entity_values(e,'P127') if isinstance(x,dict) and x.get('id')]
            owners=[x for x in owners if x]
            if owners:data['owner']=', '.join(list(dict.fromkeys(owners))[:3])
        site=entity_value(e,'P856')
        if not data.get('website') and isinstance(site,str) and site.startswith('http'):
            data['website']=site
    birth=entity_value(e,'P569');death=entity_value(e,'P570')
    if kind!='teams':
        if (value:=wikidata_date(birth)):data['birth']=value
        if (value:=wikidata_date(death)):data['death']=value
    photo=entity_value(e,'P154' if kind=='teams' else 'P18')
    # P154 is a club crest, NEVER a fallback portrait for footballers/coaches.
    if isinstance(photo,str) and len(photo)<240:
        data['image']='https://commons.wikimedia.org/wiki/Special:FilePath/'+urllib.parse.quote(photo,safe='')+'?width=360'
        data['imagePage']='https://commons.wikimedia.org/wiki/File:'+urllib.parse.quote(photo.replace(' ','_'),safe='()_')
    elif kind!='teams' and details.get('wikiThumbnail'):
        data['image']=details['wikiThumbnail']
        data['imagePage']=page_url
    has_career=bool(data.get('clubs') or data.get('coached'))
    data['careerSource']=('Wikipedia ('+lang+') · '+('klub məlumatları' if kind=='teams' else 'karyera cədvəli')) if verified and has_career else ('Wikipedia ('+lang+') · xülasə; klub tarixi: Wikidata' if verified else 'Wikidata · təsdiqlənmiş struktur faktları')
    if history_fallback:
        data['careerSource']='Wikidata P54 · təsdiqlənmiş komanda üzvlüyü (senior liqa statistikası deyil)'
    data['careerUrl']=page_url if verified else 'https://www.wikidata.org/wiki/'+qid
    data['wikiUrl']=page_url
    data['wikiLanguage']=lang
    data['wikiPageLinks']=verified_language_links(e)
    data['wikiLicense']='CC BY-SA 4.0 (məqalə mətni); media ayrıca lisenziyalıdır'
    data['wikiLicenseUrl']='https://creativecommons.org/licenses/by-sa/4.0/'
    data['wikiKind']=kind
    data['statsChecked']=dt.datetime.now(dt.timezone.utc).date().isoformat()
    if kind!='teams':
        data['statsScope']='unspecified_membership' if history_fallback else 'domestic_league'
        data['statNotice']=('Komanda üzvlüyü Wikidata P54 məlumatıdır; klub, gənclər və milli komanda ola bilər. Matç, qol və assist statistikaları burada təsdiqlənmir.' if history_fallback else 'Matç və qollar əsasən daxili liqa üçündür; bütün yarışların cəmi deyil. Asist məlum deyilsə, 0 sayılmır.')
    data['wikiMatch']=verified
    data['verifiedSnapshot']=False
    return data

def enrich(qid,get_json,refresh=False,kind='players'):
    """Return cached or on-demand Wikipedia data; offline seed for curated stars."""
    if not VALID_QID.fullmatch(qid or ''):return None
    if not refresh:
        found=cached(qid)
        if found is not None and found.get('wikiKind')==kind and (kind!='teams' or found.get('clubDataVersion')==2):
            if qid in SEED and isinstance(found,dict):
                seeded=SEED[qid]
                return {**seeded,**{k:v for k,v in found.items() if v not in ('',None) and v != []}}
            return found or SEED.get(qid)
    try:
        info=remote_enrich(qid,get_json,kind=kind)
        if info:
            # Disk cache failure cannot discard valid, freshly fetched source data.
            try:store(qid,info,bool(info.get('wikiMatch'))) # Retry unverified pages after 1 day
            except (sqlite3.Error,OSError,ValueError):pass
            # Wikidata-verified article facts take precedence. Curated snapshots fill
            # *missing sections*, not overwrite a verified live career table.
            if qid in SEED:
                seeded=SEED[qid]
                merged={**seeded,**{k:v for k,v in info.items() if v not in ('',None) and v != []}}
                for field in ('clubs','coached','nationalTeams','national','awards','fullName','birthPlace','height','position','birth','image','imagePage'):
                    if not info.get(field) and seeded.get(field):merged[field]=seeded[field]
                return merged
            return info
        try:store(qid,{},False)
        except (sqlite3.Error,OSError,ValueError):pass
    except Exception:
        # Cache miss rather than an empty authoritative profile if requests fail.
        pass
    return SEED.get(qid)


def with_wikipedia(profile,info):
    if not info:return profile
    p=dict(profile)
    for field in ('birth','death','image','position','fullName','birthPlace','height','country','foundedYear','stadium','stadiumCapacity',
                  'city','manager','league','nickname','nicknames','fullName','shortName','chairman','owner','website','colors','wikiSummary','wikiUrl','wikiLanguage',
                  'wikiPageLinks','wikiLicense','wikiLicenseUrl','wikiKind','imagePage'):
        if info.get(field):p[field]=info[field]
    for field in ('honours','squadSnapshot','colorHexes'):
        if info.get(field):p[field]=info[field]
    for field in ('squadSource','squadChecked','clubDataVersion','stadiumPhoto','stadiumPhotoPage','stadiumPhotoLicense','stadiumPhotoLicenseUrl','stadiumPhotoCredit','stadiumQid','stadiumImageName'):
        if info.get(field):p[field]=info[field]
    for field in ('clubs','coached','nationalTeams','awards'):
        if info.get(field):p[field]=info[field]
    for field in ('careerSource','careerUrl','statsChecked','statsAsOf','statsScope','statNotice','wikiMatch','verifiedSnapshot','national','otherSources'):
        if field in info:p[field]=info[field]
    if p.get('death'):p['lifeStatus']='deceased'
    if p.get('clubs') and p.get('coached'):
        p['roles']=list(dict.fromkeys((p.get('roles') or [])+['players','coaches']))
    if info.get('clubs') or info.get('coached') or p.get('kind')=='teams' or info.get('wikiSummary'):
        if info.get('wikiMatch'):
            p['source']=(p.get('source','').split(' + Wikipedia')[0] or 'Wikidata')+' + Wikipedia'
        p['statsAvailable']=any(c.get('apps') is not None or c.get('goals') is not None for c in info.get('clubs',[]))
    return p

def seed_by_profile(profile):
    qid=profile.get('wikidataId') or profile.get('qid') or (profile['id'] if VALID_QID.fullmatch(profile.get('id','')) else '')
    if qid and qid in SEED:return SEED[qid]
    # Seed catalogue IDs such as p:pel have been explicitly curated, unlike fuzzy matching.
    return SEED.get(profile.get('id'))
