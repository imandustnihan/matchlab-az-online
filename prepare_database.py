"""Build verified SQLite identity index from Git-hostable 16-MiB gzip fragments."""
import gzip,hashlib,json,os,sqlite3,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MANIFEST=json.loads((ROOT/'data_manifest.json').read_text(encoding='utf8'))
TARGET=ROOT/'world_football.sqlite'

def sha_file(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while (part:=f.read(2*1024*1024)):h.update(part)
    return h.hexdigest()

def main():
    if TARGET.exists() and sha_file(TARGET)==MANIFEST['sqlite_sha256']:
        print('Existing verified SQLite database detected',flush=True);return
    # Verify every part before assembling or opening it.
    for part in MANIFEST['parts']:
        file=ROOT/part['name']
        if not file.exists() or file.stat().st_size!=part['bytes'] or sha_file(file)!=part['sha256']:
            raise RuntimeError('Missing/damaged DB archive part: '+part['name'])
    fd,p=tempfile.mkstemp(prefix='matchlab_src_',suffix='.gz',dir=ROOT);os.close(fd)
    fd,db=tempfile.mkstemp(prefix='matchlab_db_',suffix='.sqlite',dir=ROOT);os.close(fd)
    try:
        with open(p,'wb') as output:
            for part in MANIFEST['parts']:
                with (ROOT/part['name']).open('rb') as f:
                    while (chunk:=f.read(2*1024*1024)): output.write(chunk)
        with gzip.open(p,'rb') as source,open(db,'wb') as target:
            while (buf:=source.read(2*1024*1024)):target.write(buf)
        if sha_file(Path(db))!=MANIFEST['sqlite_sha256']:
            raise RuntimeError('Database checksum mismatch')
        con=sqlite3.connect('file:'+Path(db).as_posix()+'?mode=ro',uri=True)
        try:
            count=con.execute('SELECT COUNT(*) FROM identities').fetchone()[0]
            if count!=MANIFEST['total']:raise RuntimeError(f'Unexpected registry count {count}')
            if con.execute('PRAGMA quick_check').fetchone()[0]!='ok':
                raise RuntimeError('SQLite integrity check failed')
        finally:con.close()
        os.replace(db,TARGET)
        print(f'Prepared validated database: {count} identity records',flush=True)
    finally:
        for tmp in [p,db]:
            if os.path.exists(tmp):os.unlink(tmp)
if __name__=='__main__':main()
