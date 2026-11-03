"""Export source-verified Reep CC0 identity data for offline native search.

The verified 506207 row SQLite archive is rebuilt from Git-committed SHA256-checked
fragments before export. No fabricated biographies, photos or match stats.
"""
import argparse
import gzip
import hashlib
import json
import sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
TARGET=ROOT / "native" / "shared" / "registry_offline.tsv.gz"
EXPECTED=506207

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=TARGET)
    a=parser.parse_args()
    from sys import path
    path.insert(0,str(ROOT))
    import prepare_database
    prepare_database.main()
    target=a.output
    target.parent.mkdir(parents=True,exist_ok=True)
    count=0
    with sqlite3.connect("file:"+str((ROOT/"world_football.sqlite").resolve())+"?mode=ro",uri=True) as con:
        with target.open("wb") as destination:
            with gzip.GzipFile(filename="",mode="wb",fileobj=destination,compresslevel=6,mtime=0) as out:
                for rid,name,kind,country in con.execute("SELECT id,name,kind,country FROM identities ORDER BY name COLLATE NOCASE, id"):
                    fields=[str(x or "").replace("\t"," ").replace("\r"," ").replace("\n"," ") for x in (rid,name,kind,country)]
                    out.write(("\t".join(fields)+"\n").encode("utf-8"))
                    count+=1
    if count!=EXPECTED:raise RuntimeError("Identity row count mismatch: "+str(count))
    with gzip.open(target,"rt",encoding="utf-8") as stream:
        sampled=sum(1 for _ in stream)
    if sampled!=EXPECTED:raise RuntimeError("Export truncated")
    size=target.stat().st_size
    print("MATCHLAB CC0 offline registry:",count,"identities;",round(size/1024/1024,2),"MiB; SHA256",hashlib.sha256(target.read_bytes()).hexdigest(),flush=True)
    if size<1_000_000:raise RuntimeError("Implausibly small offline registry")
if __name__=="__main__":main()
