"""SQLite search index for Reep's public-domain football identity register.
Only identity facts are indexed; never invents stats, photos, rosters or fixture results.
"""
import json, re, sqlite3, unicodedata
from functools import lru_cache
from pathlib import Path

BASE=Path(__file__).resolve().parent
DB=BASE/'world_football.sqlite'
KINDS={'player':'players','team':'teams','coach':'coaches','competition':'competitions'}

def normal(text):
 text=str(text or '').casefold().replace('ə','e').replace('ı','i').replace('ß','ss').replace('ø','o').replace('ł','l')
 text=''.join(c for c in unicodedata.normalize('NFKD',text) if not unicodedata.combining(c))
 return ' '.join(re.findall(r'[^\W_]+',text,flags=re.UNICODE))

def connect():
 if not DB.is_file():return None
 try:
  con=sqlite3.connect(f'file:{DB.as_posix()}?mode=ro',uri=True,timeout=2)
  con.row_factory=sqlite3.Row
  con.execute('SELECT 1 FROM identities LIMIT 1')
  return con
 except sqlite3.Error:
  try:con.close()
  except Exception:pass
  return None

def counts():
 con=connect()
 if not con:return None
 try:
  items=dict(con.execute('SELECT kind, COUNT(*) FROM identities GROUP BY kind').fetchall())
  release=con.execute('SELECT value FROM metadata WHERE key=?',('release',)).fetchone()
  return {'counts':items,'total':sum(items.values()),'release':release[0] if release else 'unknown'}
 finally:con.close()

@lru_cache(maxsize=1)
def qid_coverage():
 """Exact counts of source-linked identities; never counts unnamed photo assets."""
 con=connect()
 if not con:return {}
 try:
  return {kind:{'total':total,'linked':linked} for kind,total,linked in con.execute(
   "SELECT kind, COUNT(*), SUM(CASE WHEN qid IS NOT NULL AND qid!='' THEN 1 ELSE 0 END) FROM identities GROUP BY kind")}
 except sqlite3.Error:return {}
 finally:con.close()

def result(row):
 return {'id':row['id'],'name':row['name'],'kind':row['kind'],'country':row['country'] or '', 'description':row['country'] or '', 'image':'','source':'Reep CC0 · dünya reyestri','verified':True,'qid':row['qid'] or ''}

def search(query,kind='all',limit=75,offset=0,country=''):
 con=connect()
 if not con:return [],False
 try:
  tokens=normal(query).split()[:8]
  filters=[];args=[]
  if kind!='all':filters.append('identities.kind=?');args.append(kind)
  if country.strip():filters.append('identities.country=?');args.append(country.strip())
  if tokens:
   expr=' AND '.join('"'+t.replace('"','')+'"*' for t in tokens)
   filters.insert(0,'lookup MATCH ?');args.insert(0,expr)
   sql='SELECT identities.id,name,kind,country,qid FROM lookup JOIN identities ON identities.id=lookup.id WHERE '+' AND '.join(filters)+' ORDER BY CASE WHEN lookup.search_name=? THEN 0 WHEN instr(" "||lookup.search_name||" "," "||?||" ")>0 THEN 1 WHEN lookup.search_name LIKE ? THEN 2 ELSE 3 END, bm25(lookup),length(name),name LIMIT ? OFFSET ?'
   args.extend([' '.join(tokens),' '.join(tokens),' '.join(tokens)+'%'])
  else:
   where=' WHERE '+' AND '.join(filters) if filters else ''
   sql='SELECT id,name,kind,country,qid FROM identities'+where+' ORDER BY name LIMIT ? OFFSET ?'
  args.extend([max(1,min(100,int(limit))),max(0,min(3_500_000,int(offset)))])
  return [result(r) for r in con.execute(sql,args)],True
 except sqlite3.Error:return [],False
 finally:con.close()

def profile(identifier):
 if not re.fullmatch(r'rp[a-z0-9]{8,30}|rc[a-z0-9]{8,30}|rt[a-z0-9]{8,30}|reep_[a-z][a-f0-9]{8,30}',identifier or ''):return None
 con=connect()
 if not con:return None
 try:
  r=con.execute('SELECT * FROM identities WHERE id=?',(identifier,)).fetchone()
  if r is None:return None
  p=result(r)
  p['gender']=r['gender'];p['confidence']=r['grade'];p['source']='Reep CC0 / '+(con.execute('SELECT value FROM metadata WHERE key=?',('release',)).fetchone() or [''])[0]
  p['url']='https://www.reep.football/'
  p['clubs']=[];p['coached']=[];p['awards']=[]
  p['lifeStatus']='unknown';p['careerStatus']='unverified'
  p['roles']=[r['kind'] for r in con.execute('SELECT DISTINCT kind FROM identities WHERE qid=? AND qid!=""',(r['qid'],))] if r['qid'] else [r['kind']]
  p['otherRoles']=[dict(x) for x in con.execute('SELECT id,name,kind FROM identities WHERE qid=? AND id!=? AND qid!=""',(r['qid'],identifier))] if r['qid'] else []
  if r['qid']:
   p['wikidataId']=r['qid']
   p['url']='https://www.wikidata.org/wiki/'+r['qid']
  return p
 finally:con.close()


@lru_cache(maxsize=8192)
def preferred_person_id(qid):
 """Canonical verified registry ID for a legacy link, with no fuzzy name matching."""
 if not re.fullmatch(r'Q[1-9][0-9]{0,11}',qid or ''):return None
 con=connect()
 if not con:return None
 try:
  row=con.execute("SELECT id FROM identities WHERE qid=? AND kind IN ('players','coaches') ORDER BY CASE WHEN kind='coaches' THEN 0 ELSE 1 END,id LIMIT 1",(qid,)).fetchone()
  return row[0] if row else None
 except sqlite3.Error:return None
 finally:con.close()


def countries(limit=240):
 con=connect()
 if not con:return []
 try:
  return [{'country':r[0],'count':r[1]} for r in con.execute('SELECT country,COUNT(*) FROM identities WHERE country!="" GROUP BY country ORDER BY COUNT(*) DESC,country LIMIT ?',(limit,))]
 finally:con.close()
