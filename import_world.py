"""Install the verified Reep 2026-10-25.1 CC0 world football register.
No login/API key. Streams data and imports players, clubs and managers to SQLite.
Optional --file entities.csv.gz for offline import; --overlay-file for QID links.
"""
import argparse,csv,gzip,hashlib,io,json,os,sqlite3,sys,time,urllib.error,urllib.request
from pathlib import Path
from world_db import DB,normal,KINDS

ROOT=Path(__file__).resolve().parent
RELEASE='2026-10-25.1'
PINNED='https://data.reep.football/releases/2026-10-25.1/objects/a840bd0f-f3bf-420e-97bd-20d52377e67d/entities.csv.gz'
MIRROR='https://www.reep.football/downloads/csv/entities'
SHA256='c1e3393c5a30a2f86d2aa94f7ab4b6025df21b27cb028f4ac00bb49887bae9ea'
OVERLAY_URL='https://www.reep.football/downloads/csv/overlay_links'
OVERLAY_SHA='f643fa9311d51fec0bb9324a31585c45d874860199c8f09bc25e92dac5cf4e56'


def download(urls,target,expected_hash):
 for url in urls:
  try:
   print('Yükləmə ünvanı:',url,flush=True)
   req=urllib.request.Request(url,headers={'User-Agent':'MATCHLAB-AZ/0.6 (Reep CC0 public dataset installer)','Accept':'application/octet-stream'})
   sha=hashlib.sha256();size=0
   with urllib.request.urlopen(req,timeout=45) as res,open(target,'wb') as file:
    while True:
     chunk=res.read(256*1024)
     if not chunk:break
     size+=len(chunk)
     if size>160*1024*1024:raise ValueError('Arxiv gözləniləndən böyükdür (160 MB limiti)')
     sha.update(chunk);file.write(chunk)
     if size//(8*1024*1024)!=(size-len(chunk))//(8*1024*1024):print(f'  {size/1024/1024:.0f} MB...',flush=True)
   if sha.hexdigest()!=expected_hash:raise ValueError('SHA-256 uyğun gəlmir! Arxiv zədələnmiş və ya yeni buraxılışdır.')
   return target
  except Exception as e:
   print('  Bu ünvandan alınmadı:',str(e)[:160],flush=True)
   target.unlink(missing_ok=True)
 raise RuntimeError('Arxiv alınmadı. İnternet bağlantısını yoxla, yaxud saytdan özün yükləyib --file istifadə et.')


def open_csv(path):
 with open(path,'rb') as stream:
  magic=stream.read(2)
 if magic==b'\x1f\x8b':
  return io.TextIOWrapper(gzip.open(path,'rb'),encoding='utf-8-sig',errors='replace',newline='')
 return open(path,'r',encoding='utf-8-sig',errors='replace',newline='')


def install(entities,overlay=None,release=RELEASE):
 temp=DB.with_suffix('.building.sqlite');temp.unlink(missing_ok=True)
 con=sqlite3.connect(temp)
 counts={key:0 for key in KINDS.values()}
 try:
  con.execute('PRAGMA journal_mode=OFF');con.execute('PRAGMA synchronous=OFF')
  con.executescript('''
    CREATE TABLE identities(id TEXT PRIMARY KEY,name TEXT NOT NULL,kind TEXT NOT NULL,country TEXT,gender TEXT,grade TEXT,qid TEXT DEFAULT '');
    CREATE INDEX ix_identity_kind ON identities(kind);
    CREATE INDEX ix_identity_country ON identities(country);
    CREATE INDEX ix_identity_kind_name ON identities(kind,name);
    CREATE INDEX ix_identity_name ON identities(name);
    CREATE VIRTUAL TABLE lookup USING fts5(id UNINDEXED, search_name, search_country, tokenize='unicode61 remove_diacritics 2');
    CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
  ''')
  with open_csv(entities) as fp:
   reader=csv.DictReader(fp)
   required={'reep_id','entity_type','canonical_name'}
   if not required.issubset(set(reader.fieldnames or [])):raise ValueError('Yanlış CSV başlıqları: '+str(reader.fieldnames))
   batch=[];fts=[]
   for ix,r in enumerate(reader,1):
    kind=KINDS.get((r.get('entity_type') or '').strip())
    if not kind:continue
    id=(r.get('reep_id') or '').strip();name=(r.get('canonical_name') or '').strip()
    if not id or not name:continue
    country=(r.get('country') or '').strip();grade=(r.get('grade') or '').strip()
    batch.append((id,name,kind,country,(r.get('gender') or ''),grade,''))
    fts.append((id,normal(name),normal(country)))
    counts[kind]+=1
    if len(batch)>=2500:
     con.executemany('INSERT OR IGNORE INTO identities VALUES (?,?,?,?,?,?,?)',batch)
     con.executemany('INSERT INTO lookup(id,search_name,search_country) VALUES (?,?,?)',fts)
     batch.clear();fts.clear()
     if ix%100000<2500:print(f'  {ix:,} sətir işlənib...',flush=True)
   if batch:
    con.executemany('INSERT OR IGNORE INTO identities VALUES (?,?,?,?,?,?,?)',batch)
    con.executemany('INSERT INTO lookup(id,search_name,search_country) VALUES (?,?,?)',fts)
  if sum(counts.values())<1:raise ValueError('Futbolçu və ya klub sətri tapılmadı.')
  if overlay is not None and Path(overlay).is_file():
   with open_csv(overlay) as fp:
    reader=csv.DictReader(fp)
    if {'reep_id','qid'}.issubset(set(reader.fieldnames or [])):
     changes=[]
     for r in reader:
      qid=(r.get('qid') or '').strip();rid=(r.get('reep_id') or '').strip()
      if rid and qid.startswith('Q') and qid[1:].isdigit():
       changes.append((qid,rid))
       if len(changes)>=2000:
        con.executemany('UPDATE identities SET qid=? WHERE id=? AND qid=""',changes);changes=[]
     if changes:con.executemany('UPDATE identities SET qid=? WHERE id=? AND qid=""',changes)
  con.execute('INSERT INTO metadata VALUES (?,?)',('release',release));con.execute('INSERT INTO metadata VALUES (?,?)',('installed_at',time.strftime('%Y-%m-%d')))
  con.execute('INSERT INTO metadata VALUES (?,?)',('counts',json.dumps(counts)))
  con.commit();con.execute('PRAGMA quick_check');con.close()
  os.replace(temp,DB)
  print('QURULDU:',counts,'YER:',DB, 'ÖLÇÜ:',round(DB.stat().st_size/1024/1024,1),'MB',flush=True)
  return counts
 except:
  con.close();temp.unlink(missing_ok=True);raise


def main(argv=None):
 ap=argparse.ArgumentParser(description='MATCHLAB AZ: 500 min+ dünya futbolçu / klub / məşqçi reyestri idxalı')
 ap.add_argument('--file',type=Path,help='Öncədən yüklənmiş entities.csv.gz (internet tələb olunmur)')
 ap.add_argument('--overlay-file',type=Path,help='İstəyə bağlı Wikidata QID overlay_links.csv.gz')
 ap.add_argument('--skip-overlay',action='store_true',help='Əlavə Wikidata bağlantı faylını yükləmə')
 ap.add_argument('--skip-sha',action='store_true',help='Yalnız əl ilə seçilmiş CSV üçün hash yoxlamanı keç')
 ns=ap.parse_args(argv)
 raw=ns.file;cached=ROOT/'entities.csv.gz';overlay=ns.overlay_file
 try:
  if raw is None:
   if cached.exists() and hashlib.sha256(cached.read_bytes()).hexdigest()==SHA256:raw=cached
   else:raw=download([MIRROR,PINNED],cached,SHA256)
  elif not ns.skip_sha:
   print('Manual faylda SHA-256 yoxlanır...',flush=True)
   if hashlib.sha256(raw.read_bytes()).hexdigest()!=SHA256:raise ValueError('Fayl təsdiqlənmiş 2026-10-25.1 buraxılışı deyil. Öz test CSV-n üçün --skip-sha.')
  if overlay is None and not ns.skip_overlay:
   cached_overlay=ROOT/'overlay_links.csv.gz'
   try:
    if cached_overlay.exists() and hashlib.sha256(cached_overlay.read_bytes()).hexdigest()==OVERLAY_SHA:overlay=cached_overlay
    else:overlay=download([OVERLAY_URL],cached_overlay,OVERLAY_SHA)
   except Exception as e:
    print('Wikidata ID-ləri alınmadı; baza yenə qurulacaq:',str(e)[:160],flush=True)
  install(raw,overlay)
  return 0
 except Exception as e:
  print('\nXƏTA:',e,flush=True);return 1
if __name__=='__main__':sys.exit(main())
