"""MATCHLAB AZ verified Wikimedia media expansion (v0.9.17).

Second-stage lookup when Wikidata P18 (person) or P154 (club emblem) is empty.
Never identify by a similar-looking name: resolve the QID's own Wikipedia
sitelink and require the article's pageprops.wikibase_item to match the QID.
Use only MediaWiki pageimages marked free; a club's stadium photo is not a logo.
"""
import datetime as dt
import json
import re
import sqlite3
import threading
import urllib.parse
from contextlib import closing
from pathlib import Path

VALID_ID = re.compile(r'^Q[1-9]\d{0,11}$')
LANGUAGES = ('en', 'tr', 'az', 'de', 'es', 'fr', 'it', 'pt')
KINDS = frozenset(('players', 'coaches', 'teams'))
CACHE_FILE = Path(__file__).with_name('wikimedia_media_cache.sqlite')
DB_LOCK = threading.Lock()
# Deliberately strict. A club photograph, stadium and jersey are NOT crests.
NOT_PORTRAIT = re.compile(r'(?:^|[ _-])(logo|emblem|badge|crest|stadium|ground|jersey|shirt|flag|coat.of.arms|map|kit)(?:[ _.-]|$)', re.I)
CREST_WORD = re.compile(r'(^|[^a-z])(logo|logotipo|logotype|badge|crest|emblem|escudo|wappen|vereinswappen|insignia|brasao|brasão|coat.of.arms|shield|grb|znak)([^a-z]|$)', re.I)


def commons_file_page(filename):
    if not isinstance(filename,str) or not filename or len(filename)>245:return ''
    return 'https://commons.wikimedia.org/wiki/File:'+urllib.parse.quote(filename.removeprefix('File:').replace(' ', '_'),safe='()_')


def free_image_url(value):
    """Allow only real Wikimedia upload CDN files, not attacker-controlled hosts."""
    if not isinstance(value,str) or not value.startswith('https://upload.wikimedia.org/') or len(value)>1500:return ''
    parts=urllib.parse.urlsplit(value)
    if parts.hostname!='upload.wikimedia.org' or parts.username or parts.password:return ''
    if not parts.path.startswith('/wikipedia/'):return ''
    return value


def crest_like(filename):
    if not isinstance(filename,str):return False
    text=urllib.parse.unquote(filename.replace('_',' ')).casefold()
    # SVG illustrations often include flags or stadium plans. Require explicit logo words.
    return bool(CREST_WORD.search(text))


def _connect():
    con=sqlite3.connect(CACHE_FILE,timeout=2)
    con.execute('CREATE TABLE IF NOT EXISTS media (qid TEXT NOT NULL, kind TEXT NOT NULL, stamp TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(qid,kind))')
    return con


def cache_load(qid,kind):
    if not VALID_ID.fullmatch(qid or '') or kind not in KINDS:return None
    try:
        with DB_LOCK:
            with closing(_connect()) as con, con:
                record=con.execute('SELECT stamp,payload FROM media WHERE qid=? AND kind=?',(qid,kind)).fetchone()
        if not record:return None
        data=json.loads(record[1]); age=dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(record[0])
        # Recheck unavailable entries daily; confirmed media every 3 weeks.
        ttl=dt.timedelta(days=21 if data.get('url') else 1)
        return data if dt.timedelta(0)<=age<ttl else None
    except (sqlite3.Error, OSError, ValueError, TypeError):return None


def cache_write(qid,kind,value):
    if not VALID_ID.fullmatch(qid or '') or kind not in KINDS:return
    try:
        with DB_LOCK:
            with closing(_connect()) as con, con:
                con.execute('INSERT OR REPLACE INTO media VALUES(?,?,?,?)',(qid,kind,dt.datetime.now(dt.timezone.utc).isoformat(),json.dumps(value,ensure_ascii=False)))
    except (sqlite3.Error, OSError, ValueError, TypeError):pass


def cache_stats():
    try:
        with DB_LOCK:
            with closing(_connect()) as con, con:
                entries=con.execute('SELECT kind,payload FROM media').fetchall()
        result={kind:{'found':0,'unavailable':0} for kind in KINDS}
        for kind,payload in entries:
            if kind in result:
                try:result[kind]['found' if json.loads(payload).get('url') else 'unavailable']+=1
                except (ValueError,TypeError):pass
        return result
    except (sqlite3.Error, OSError):return {kind:{'found':0,'unavailable':0} for kind in KINDS}


def verified_page_images(qids,kind,get_json,refresh=False):
    """Find strictly QID-matched freely licensed Wikipedia pageimages in batches.

    Returns (found mapping, complete boolean). An upstream outage is not a
    definitive image miss; do not cache absence if the upstream is unreachable.
    """
    if kind not in KINDS:return {},False
    ids=list(dict.fromkeys(q for q in qids if VALID_ID.fullmatch(q or '')))[:20]
    if not ids:return {},True
    output={};unresolved=[]
    for qid in ids:
        cached=None if refresh else cache_load(qid,kind)
        if cached is None:unresolved.append(qid)
        elif cached.get('url'):output[qid]=cached
    if not unresolved:return output,True
    params={'action':'wbgetentities','format':'json','ids':'|'.join(unresolved),'props':'sitelinks',
            'sitefilter':'|'.join(lang+'wiki' for lang in LANGUAGES)}
    wd='https://www.wikidata.org/w/api.php?'+urllib.parse.urlencode(params)
    try:entities=get_json(wd,86400).get('entities',{})
    except Exception:return output,False
    # A sitelink alone is not proof: pageprops.wikibase_item must also match.
    targets={qid:(entities.get(qid,{}).get('sitelinks') or {}) for qid in unresolved}
    complete=True
    for lang in LANGUAGES:
        candidates={qid:sitelinks.get(lang+'wiki',{}).get('title') for qid,sitelinks in targets.items()
                    if qid not in output and isinstance(sitelinks.get(lang+'wiki',{}).get('title'),str)}
        candidates={k:v for k,v in candidates.items() if v and ':' not in v.split(' ',1)[0] and len(v)<180}
        if not candidates:continue
        wp='https://'+lang+'.wikipedia.org/w/api.php?'+urllib.parse.urlencode({
            'action':'query','format':'json','formatversion':2,'prop':'pageimages|pageprops',
            'titles':'|'.join(dict.fromkeys(candidates.values())),'redirects':1,
            'ppprop':'wikibase_item|disambiguation','piprop':'thumbnail|name',
            'pithumbsize':300,'pilicense':'free'})
        try:pages=get_json(wp,86400).get('query',{}).get('pages',[])
        except Exception:
            complete=False
            continue
        for page in pages:
            if not isinstance(page,dict) or page.get('ns')!=0 or 'missing' in page:continue
            props=page.get('pageprops') or {}
            qid=props.get('wikibase_item','')
            if qid not in candidates or 'disambiguation' in props:continue
            # A redirected page with a different identity must not be accepted.
            thumbnail=free_image_url((page.get('thumbnail') or {}).get('source',''))
            if not thumbnail:continue
            filename=page.get('pageimage') or props.get('page_image_free') or ''
            if kind=='teams' and not crest_like(filename):continue
            if kind in ('players','coaches') and NOT_PORTRAIT.search(str(filename)):continue
            file_host='https://commons.wikimedia.org' if '/wikipedia/commons/' in urllib.parse.urlsplit(thumbnail).path else 'https://'+lang+'.wikipedia.org'
            file_link=(file_host+'/wiki/File:'+urllib.parse.quote(str(filename).removeprefix('File:').replace(' ','_'),safe='()_')) if filename else 'https://'+lang+'.wikipedia.org/wiki/'+urllib.parse.quote(str(page.get('title','')).replace(' ','_'),safe='()_')
            value={'url':thumbnail,'source':'Wikipedia ('+lang+') · sərbəst pageimage',
                   'imagePage':file_link,
                   'licenseNote':'Şəklin lisenziyasını Wikimedia Commons mənbəsində yoxlayın',
                   'verifiedQid':qid,'kind':kind,'wikiLanguage':lang,'mediaType':'crest' if kind=='teams' else 'portrait'}
            output[qid]=value
    for qid in unresolved:
        if qid in output:cache_write(qid,kind,output[qid])
        elif complete:cache_write(qid,kind,{'url':'','source':'Təsdiqlənmiş sərbəst media tapılmadı','verifiedQid':qid,'kind':kind})
    return output,complete
