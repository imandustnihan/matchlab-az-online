"""Source-verified club history extraction: honours, roster snapshots, imagery and links.

Only parse Wikipedia page *after* its Wikidata identity was matched by the caller.
This module never claims a Wikipedia snapshot is an up-to-the-minute roster.
A missing statistic is missing, not zero. No club title totals are inferred.
"""
import datetime as dt
import html
import re
import unicodedata
import urllib.parse
from pathlib import Path

_HEADING = re.compile(r'(?m)^\s*(={2,6})\s*([^\n=]+?)\s*\1\s*$')
_HONOURS = re.compile(r'^(honou?rs|titles|trophies|achievements|palmar[eè]s|t[ií]tulos|erfolge|başarılar|kupalar|trofeylər|nailiyyətlər)$', re.I)
_SQUAD = re.compile(r'^(current squad|first[- ]team squad|first[- ]team players|senior squad|playing squad|squad|plantilla actual|primer equipo|kad(r|ro)|heyət|əsas heyət)$', re.I)


def _norm(text):
    text = str(text or '').casefold().replace('ə','e').replace('ı','i')
    return ''.join(c for c in unicodedata.normalize('NFKD',text) if not unicodedata.combining(c))


def _text(text):
    """Strip basic wiki markup safely; skip templates rather than inventing content."""
    text=str(text or '')
    text=re.sub(r'<!--.*?-->','',text,flags=re.S)
    text=re.sub(r'<ref\b[^>]*>.*?</ref\s*>|<ref\b[^>]*/>', '',text,flags=re.S|re.I)
    text=re.sub(r'<[^>]*>','',text)
    text=re.sub(r'\[\[(?:[^\]|]+\|)?([^\]]+)\]\]',r'\1',text)
    text=re.sub(r'\{\{[^{}]*\}\}','',text)
    text=re.sub(r"'{2,5}",'',text)
    return html.unescape(re.sub(r'\s+',' ',text)).strip(' \t:;*|')[:220]


def section(wikitext, heading_pattern):
    """Return text bounded by next header at the same or higher level."""
    if not isinstance(wikitext,str):return ''
    matches=list(_HEADING.finditer(wikitext))
    for i,m in enumerate(matches):
        name=_text(m.group(2))
        if heading_pattern.fullmatch(_norm(name)):
            level=len(m.group(1))
            end=next((n.start() for n in matches[i+1:] if len(n.group(1))<=level),len(wikitext))
            return wikitext[m.end():min(end,m.end()+90_000)]
    return ''


def _table_honours(section_text):
    """Parse Type/Competition/Titles/Seasons wiki tables when counts are explicit.

    Most major football-club articles use tabular honours, not bullet lists.
    This deliberately ignores totals that cannot be attributed to a single cup.
    """
    out=[];group=''
    for chunk in re.split(r'(?m)^\s*\|-.*$',section_text)[1:]:
        if chunk.strip().startswith('!') or chunk.strip().startswith('\n!'):
            continue
        cells=[]
        for line in chunk.splitlines():
            line=line.strip()
            if line.startswith('|}'):
                break
            if not line.startswith('|') or line.startswith('|-'):
                continue
            val=line[1:].strip()
            # Handle '| rowspan="5" | Domestic' and similar MediaWiki cell attrs.
            if re.match(r'(?i)^(?:rowspan|colspan|style|scope|class)\s*=',val):
                val=val.split('|',1)[-1].strip() if '|' in val else ''
            for item in re.split(r'\s*\|\|\s*',val):
                item=_text(item)
                if item:cells.append(item)
        if len(cells)<2:continue
        categories={'domestic','continental','intercontinental','international','worldwide','regional','national','other'}
        if _norm(cells[0]).strip() in categories and len(cells)>=3:
            group=cells[0]
            title,count=cells[1],cells[2]
        else:
            title,count=cells[0],cells[1]
        count_str=re.sub(r'(?i)\s*\[[a-z]+\]\s*$','',count).strip()
        # Some Wikipedia cells carry footnote superscripts after the numeral.
        match=re.match(r'^(\d{1,3})(?:\D.*)?$',count_str)
        if not match:continue
        number=int(match.group(1))
        if number<1 or number>150 or not 4<=len(title)<=105:continue
        if _norm(title).strip() in categories or 'runner' in _norm(title):continue
        out.append({'name':title,'count':number,'category':group or 'Kuboklar','source':'Wikipedia · Honours (cədvəl)'})
        if len(out)>=50:break
    return out


def parse_honours(wikitext):
    """Read only explicitly listed wins. Counts require an explicit source numeral."""
    raw=section(wikitext,_HONOURS)
    if not raw:return []
    entries=[];group='';seen=set()
    for line in raw.splitlines():
        heading=_HEADING.fullmatch(line.strip())
        if heading:
            group=_text(heading.group(2))[:70]
            continue
        if not re.match(r'^\s*\*{1,3}\s+',line):continue
        item=_text(re.sub(r'^\s*\*{1,3}\s+','',line)).strip()
        if not item or len(item)<4:continue
        if re.search(r'(?i)runner[s]?[- ]?up|finalists?|semi[- ]final|third place|second place|runners? up',item):continue
        if re.search(r'(?i)\b(reserve[s]?|youth|under[- ]?\d\d|academy|women)\b',group+' '+item):continue
        # Typical Wikipedia: "UEFA Champions League: Winners (15): years", "La Liga (36)".
        main=item.split(':')[0].strip()
        if re.search(r'(?i)\b(winners?|champions?|title[s]?)\b',main):
            # if competition is after a prefix like "Winners", keep context only if explicit.
            main=re.sub(r'(?i)\s*[-–:]?\s*(?:winners?|champions?)\s*$', '',main).strip()
        number=re.search(r'(?i)\b(?:winners?|champions?|titles?)\s*\(\s*(\d{1,3})\s*\)',item)
        if not number:number=re.search(r'\(\s*(\d{1,3})\s*\)\s*(?::|$)',main)
        if not number:number=re.search(r'(?i)^(.*?):\s*(\d{1,3})\b',item)
        count=int(number.group(number.lastindex)) if number and 0<int(number.group(number.lastindex))<=150 else None
        name=re.sub(r'\s*\(\s*\d{1,3}\s*\)\s*$','',main)
        name=re.sub(r'(?i)\s*[—–-]?\s*(?:winners?|champions?)\s*$','',name)
        name=name.strip(' :—–-')
        if not 4<=len(name)<=105:continue
        if re.fullmatch(r'(?i)domestic|international|continental|regional|national|other|friendly|major|minor|worldwide',name):continue
        # A trophy's source may have count but no competition: do not invent.
        if name.casefold() in ('winners','champions','runners-up'):continue
        key=_norm(name)
        if key in seen:continue
        seen.add(key)
        entries.append({'name':name,'count':count,'category':group or 'Kuboklar','source':'Wikipedia · Honours'})
        if len(entries)>=45:break
    for h in _table_honours(raw):
        key=_norm(h['name'])
        if key not in seen:
            seen.add(key)
            entries.append(h)
    return entries[:50]


def _templates(raw,names=('fs player','football squad player','football squad member')):
    """Yield balanced templates with a recognized opening name."""
    pattern=re.compile(r'\{\{\s*('+('|'.join(re.escape(n).replace('\\ ','\\s+') for n in names))+r')\b',re.I)
    for match in pattern.finditer(raw):
        pos=match.start();depth=0;i=pos
        while i<len(raw) and i<pos+5000:
            token=raw[i:i+2]
            if token=='{{':depth+=1;i+=2;continue
            if token=='}}':
                depth-=1;i+=2
                if depth==0:
                    yield raw[pos:i];break
                continue
            i+=1


def parse_squad(wikitext):
    """Wikipedia squad snapshot, never a certified live squad."""
    raw=section(wikitext,_SQUAD)
    if not raw:return []
    from wikipedia_enrichment import split_params
    players=[];names=set()
    for item in _templates(raw):
        params=split_params(item)
        name=_text(params.get('name') or params.get('player') or '')
        number=_text(params.get('no') or params.get('number') or '')
        role=_text(params.get('pos') or params.get('position') or '')
        if not 2<len(name)<85 or name.casefold() in ('tbd','vacant','n/a'):continue
        if not re.fullmatch(r'\d{1,2}',number):number=''
        if role and len(role)>12:role=''
        key=_norm(name)
        if key in names:continue
        names.add(key)
        players.append({'name':name,'number':number,'position':role,'source':'Wikipedia · Current squad'})
        if len(players)>=40:break
    return players


def colors_from_text(raw):
    """Only a visual swatch when the source explicitly gives its hex color."""
    raw=str(raw or '')
    hexes=list(dict.fromkeys('#'+h.upper() for h in re.findall(r'(?<![0-9A-Fa-f])#([0-9A-Fa-f]{6})(?![0-9A-Fa-f])',raw)))
    return hexes[:5]


def stadium_media(club_entity, get_json, max_filename=200):
    """P115 -> stadium P18 -> Commons imageinfo and license, all linked by QIDs."""
    from wikipedia_enrichment import entity_value
    stadium=entity_value(club_entity,'P115')
    qid=stadium.get('id','') if isinstance(stadium,dict) else ''
    if not re.fullmatch(r'Q[1-9][0-9]{0,11}',qid):return {}
    url='https://www.wikidata.org/w/api.php?'+urllib.parse.urlencode({'action':'wbgetentities','format':'json','ids':qid,'props':'labels|claims','languages':'az|tr|en','languagefallback':'1'})
    payload=(get_json(url,86400).get('entities') or {}).get(qid,{})
    name=next((payload.get('labels',{}).get(lang,{}).get('value') for lang in ('az','tr','en') if payload.get('labels',{}).get(lang,{}).get('value')),'')
    photo=entity_value(payload,'P18')
    if not isinstance(photo,str) or not 1<len(photo)<max_filename:return {}
    file='File:'+photo.replace('_',' ')
    params={'action':'query','format':'json','formatversion':2,'prop':'imageinfo','iiprop':'url|extmetadata','iiurlwidth':720,'titles':file}
    media_url='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(params)
    pages=(get_json(media_url,86400).get('query') or {}).get('pages') or []
    if not pages or len(pages)!=1:return {}
    info=(pages[0].get('imageinfo') or [{}])[0]
    ext=info.get('extmetadata') or {}
    def val(key):return str((ext.get(key) or {}).get('value') or '')
    if val('NonFree').casefold()=='true':return {}
    license_name=_text(val('LicenseShortName'))
    license_url=val('LicenseUrl')
    # Reject unlicensed files rather than claiming they are free.
    if not license_name or not license_url.startswith('https://'):return {}
    if not re.search(r'(?i)\bcc[ -]?(?:by|zero|0)|creative commons|public domain|\bpd\b|\bgfdl\b',license_name):return {}
    image=info.get('thumburl') or info.get('url') or ''
    if not isinstance(image,str) or not image.startswith('https://upload.wikimedia.org/'):return {}
    page=info.get('descriptionurl') or 'https://commons.wikimedia.org/wiki/'+urllib.parse.quote(file.replace(' ','_'),safe=':_')
    if not page.startswith('https://commons.wikimedia.org/'):return {}
    return {'stadiumPhoto':image,'stadiumPhotoPage':page,'stadiumPhotoLicense':license_name,'stadiumPhotoLicenseUrl':license_url,'stadiumPhotoCredit':_text(val('Attribution') or val('Artist'))[:160],'stadiumQid':qid,'stadiumImageName':name}


def historical_links(club_name, seed, team_qid='', aliases=()):
    """Curated archival associations only. No name-based cross-person unification."""
    from wikipedia_enrichment import VALID_QID
    keys={_norm(x).strip() for x in (club_name,*aliases) if x}
    keys.discard('')
    if not keys:return {'players':[],'coaches':[]}
    out={'players':[],'coaches':[]};seen=set()
    for person_id,person in seed.items():
        if not VALID_QID.fullmatch(str(person_id)):continue
        if not isinstance(person,dict):continue
        name=person.get('name')
        if not name:continue
        for field,label in (('clubs','players'),('coached','coaches')):
            matches=[]
            for club in person.get(field,[]) or []:
                if not isinstance(club,dict):continue
                club_id=club.get('id','')
                target_name=_norm(club.get('name') or '').strip()
                if (team_qid and club_id==team_qid) or (target_name and target_name in keys):
                    matches.append(club)
            if matches and (person_id,label) not in seen:
                seen.add((person_id,label))
                out[label].append({'id':person_id,'name':name,'kind':label,'country':person.get('country',''),'career':matches[:8], 'source':'Seçilmiş təsdiqlənmiş tarixi karyera qeydləri'})
        if len(out['players'])>=25 and len(out['coaches'])>=15:break
    for field,cap in (('players',25),('coaches',15)):
        out[field]=out[field][:cap]
    return out
