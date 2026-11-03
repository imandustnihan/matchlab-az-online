"""Best-effort background refresh of recently viewed football identities.

Wikidata QIDs are verified in wikipedia_enrichment before facts are stored.
This watcher is bounded and cannot guarantee real-time changes; hosting must
remain running. Infrequently viewed identities update when opened again.
"""
import json
import os
import re
import threading
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
FILE=ROOT/"score_cache"/"profile_watchlist.json"
QID=re.compile(r"^Q[1-9][0-9]{0,11}$")
KINDS={"players","coaches","teams"}
LOCK=threading.RLock()
WATCHED={}
_STARTED=False
MAX_PROFILES=240
REFRESH_AFTER=24*3600
MAX_PER_HOUR=8

def _load():
    try:
        data=json.loads(FILE.read_text(encoding="utf8"))
        if isinstance(data,dict):
            for qid,entry in list(data.items())[:MAX_PROFILES]:
                if QID.fullmatch(qid) and isinstance(entry,dict) and entry.get("kind") in KINDS:
                    WATCHED[qid]={"kind":entry["kind"],"seen":float(entry.get("seen",0)),
                                   "checked":float(entry.get("checked",0))}
    except (OSError,ValueError,TypeError):
        pass

def _save():
    try:
        FILE.parent.mkdir(exist_ok=True)
        temp=FILE.with_suffix(".tmp")
        temp.write_text(json.dumps(WATCHED,separators=(",",":")),encoding="utf8")
        os.replace(temp,FILE)
    except (OSError,TypeError,ValueError):
        pass

def watch(qid,kind):
    if not QID.fullmatch(qid or "") or kind not in KINDS:
        return None
    with LOCK:
        item=WATCHED.get(qid,{"kind":kind,"seen":0,"checked":0})
        item["kind"]=kind
        now=time.time()
        # Persist on first view and at most once every 10 minutes on repeat views.
        needs_save=qid not in WATCHED or now-item["seen"]>600
        item["seen"]=now
        WATCHED[qid]=item
        if len(WATCHED)>MAX_PROFILES:
            oldest=min(WATCHED,key=lambda k:WATCHED[k]["seen"])
            WATCHED.pop(oldest,None)
        if needs_save:_save()
        return {"autoRefresh":True,"checkedUtc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime(item["checked"])) if item["checked"] else None,
                "intervalHours":24,"source":"Wikidata / Wikipedia (verified identity)",
                "coverage":"recently_viewed_only"}

def refresh_once(enrich,fetch,now=None,max_items=2):
    """Runs from the server's daemon, with strict upper bounds and TTL."""
    current=time.time() if now is None else now
    max_items=max(0,min(MAX_PER_HOUR,int(max_items)))
    with LOCK:
        candidates=sorted(((qid,v.copy()) for qid,v in WATCHED.items()
                           if 0<=current-v["seen"]<30*86400
                           and current-v["checked"]>=REFRESH_AFTER),
                          key=lambda t:(t[1]["checked"],-t[1]["seen"]))[:max_items]
        # Reserve each slot before external HTTP requests, even if they fail.
        for qid,_ in candidates:WATCHED[qid]["checked"]=current
        if candidates:_save()
    updated=0
    for qid,entry in candidates:
        try:
            info=enrich(qid,fetch,refresh=True,kind=entry["kind"])
            if isinstance(info,dict) and info.get("wikiMatch"):updated+=1
        except Exception:
            pass  # Existing verified profile cache must survive provider outage.
    return {"attempted":len(candidates),"verified":updated}

def _run(enrich,fetch):
    # Slow ramp-up, then 2 identities each 15 minutes = <= 8/hour.
    while True:
        try:refresh_once(enrich,fetch,max_items=2)
        except Exception:pass
        time.sleep(900)

def start(enrich,fetch):
    global _STARTED
    with LOCK:
        if _STARTED:return
        _load()
        _STARTED=True
        threading.Thread(target=_run,args=(enrich,fetch),daemon=True,name="matchlab-profile-refresh").start()
