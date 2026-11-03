"""CC0 historical football fixtures, on-demand and explicitly NOT live.

Source: openfootball/football.json (CC0-1.0).
Do not mistake missing season files, absent scores or partial schedules for
current/live results. All URLs come from this static mapping and validated years.
"""
import re

LEAGUES={
    "eng.1":("en.1","Premier League"),
    "eng.2":("en.2","Championship"),
    "esp.1":("es.1","La Liga"),
    "esp.2":("es.2","Segunda División"),
    "ger.1":("de.1","Bundesliga"),
    "ger.2":("de.2","2. Bundesliga"),
    "ita.1":("it.1","Serie A"),
    "ita.2":("it.2","Serie B"),
    "fra.1":("fr.1","Ligue 1"),
    "fra.2":("fr.2","Ligue 2"),
    "por.1":("pt.1","Primeira Liga"),
    "ned.1":("nl.1","Eredivisie"),
    "sco.1":("sco.1","Scottish Premiership"),
    "tur.1":("tr.1","Süper Lig"),
    "bel.1":("be.1","Belgian Pro League"),
    "aut.1":("at.1","Austrian Bundesliga"),
    "gre.1":("gr.1","Super League Greece"),
}
START_YEAR=2010
END_YEAR=2026

def allowed_season(season):
    if not re.fullmatch(r"20[12][0-9]-[0-9]{2}",season or ""):
        return False
    first=int(season[:4])
    return START_YEAR<=first<=END_YEAR and season[-2:]==str((first+1)%100).zfill(2)

def _score(match):
    raw=match.get("score")
    if isinstance(raw,dict):
        value=raw.get("ft")
    else:
        value=raw
    if isinstance(value,list) and len(value)==2 and all(type(v)==int and 0<=v<=99 for v in value):
        return value
    return None

def view(league,season,fetch,limit=60,offset=0,team=""):
    if league not in LEAGUES or not allowed_season(season):
        return {"available":False,"items":[],"message":"Tarixi liqa və ya mövsüm düzgün deyil."}
    limit=max(1,min(80,int(limit)))
    offset=max(0,min(2000,int(offset)))
    team=str(team or "").strip().casefold()[:60]
    filename,name=LEAGUES[league]
    url=f"https://raw.githubusercontent.com/openfootball/football.json/master/{season}/{filename}.json"
    try:
        payload=fetch(url,1800 if season.startswith("2026") else 86400)
    except Exception:
        return {"available":False,"items":[],"message":"Bu mövsümün CC0 arxivi hazırda əlçatan deyil.",
                "source":"OpenFootball CC0","season":season,"league":league,"live":False}
    if not isinstance(payload,dict) or not isinstance(payload.get("matches"),list):
        return {"available":False,"items":[],"message":"Arxiv formatı uyğun deyil.",
                "source":"OpenFootball CC0","season":season,"league":league,"live":False}
    rows=[]
    for index,match in enumerate(payload["matches"][:3000]):
        if not isinstance(match,dict):continue
        home=match.get("team1");away=match.get("team2");date=match.get("date")
        if not (isinstance(home,str) and isinstance(away,str) and
                isinstance(date,str) and re.fullmatch(r"20[0-3][0-9]-[01][0-9]-[0-3][0-9]",date)):
            continue
        if team and team not in home.casefold() and team not in away.casefold():continue
        score=_score(match)
        rows.append({
            "id":f"historical:{season}:{filename}:{index}",
            "home":home[:100],"away":away[:100],"date":date,
            "time":str(match.get("time") or "")[:10],
            "round":str(match.get("round") or "")[:90],
            "homeScore":score[0] if score else None,
            "awayScore":score[1] if score else None,
            "resultRecorded":score is not None,
            "live":False,
        })
    return {"available":True,"items":rows[offset:offset+limit],"count":len(rows),
            "offset":offset,"nextOffset":offset+limit if offset+limit<len(rows) else None,
            "season":season,"league":league,"leagueName":name,"live":False,
            "source":"OpenFootball CC0 / football.json",
            "message":"Tarixi arxivdir, canlı matç nəticələri deyil. Yalnız mənbədə olan hesablar göstərilir."}
