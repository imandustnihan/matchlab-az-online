"""Source-labeled match details for free match providers.

No synthetic lineups, stats, game events, or claimed formations. Supports
ESPN (unofficial API), TheSportsDB v1 free, and community OpenLigaDB. Parsers
are pure functions suitable for offline fixture-based tests.
"""
from __future__ import annotations

import re


def short(value, limit=140):
    return str(value or '').strip()[:limit]


def is_yes(value):
    return value is True or str(value).strip().lower() in ('yes','true','1')


def numeric(value):
    if value is None or str(value).strip() == '':
        return None
    try:
        num = float(str(value).replace(',', '').replace('%', ''))
        if num != num or abs(num) > 10000000:
            return None
        return int(num) if num.is_integer() else round(num, 2)
    except (TypeError, ValueError, OverflowError):
        return None


def safe_formation(value):
    name = short(value, 24).strip()
    if not re.fullmatch(r'[1-9](?:-[1-9]){1,4}', name):
        return ''
    return name if sum(int(n) for n in name.split('-')) == 10 else ''


def player_record(name, number='', position='', image='', place=None, player_id=''):
    return {'id': short(player_id, 32), 'name': short(name, 85),
            'number': short(number, 6), 'position': short(position, 32),
            'image': short(image, 400), 'place': place if isinstance(place, int) and 1 <= place <= 11 else None}


def blank_side():
    return {'formation':'', 'formationVerified':False, 'starters':[], 'substitutes':[], 'incomplete':False}


def empty_details(provider, message=''):
    return {'available':False, 'source':provider, 'message':message,
            'lineup':{'home':blank_side(), 'away':blank_side()},
            'events':[], 'statistics':[]}


def sportsdb_details(lineup_raw, stats_raw, timeline_raw):
    out = empty_details('TheSportsDB (pulsuz, limitli)')
    rows = lineup_raw.get('lineup') if isinstance(lineup_raw,dict) else None
    if isinstance(rows,list):
        for row in rows[:80]:
            if not isinstance(row,dict):
                continue
            side = 'home' if is_yes(row.get('strHome')) else 'away'
            record = player_record(row.get('strPlayer'), row.get('intSquadNumber'), row.get('strPosition'),
                                   row.get('strThumb') or row.get('strCutout'), player_id=row.get('idPlayer'))
            if not record['name']:
                continue
            key = 'substitutes' if is_yes(row.get('strSubstitute')) else 'starters'
            if len(out['lineup'][side][key]) < 35:
                out['lineup'][side][key].append(record)
    for side in ('home','away'):
        group=out['lineup'][side]
        group['incomplete']=bool(group['starters']) and len(group['starters']) != 11
    stats = stats_raw.get('eventstats') if isinstance(stats_raw,dict) else None
    if isinstance(stats,list):
        for x in stats[:50]:
            if not isinstance(x,dict):continue
            name=short(x.get('strStat'),54)
            h=numeric(x.get('intHome'));a=numeric(x.get('intAway'))
            if name and (h is not None or a is not None):
                out['statistics'].append({'name':name,'home':h,'away':a})
    times=timeline_raw.get('timeline') if isinstance(timeline_raw,dict) else None
    if isinstance(times,list):
        for x in times[:100]:
            if not isinstance(x,dict):continue
            minute=numeric(x.get('intTime'))
            who=short(x.get('strPlayer'),80)
            what=short(x.get('strTimeline') or x.get('strEvent') or x.get('strTimelineDetail'),130)
            if not (who or what):continue
            out['events'].append({'clock':str(minute)+"'" if minute is not None else '',
                'text':short(' — '.join(v for v in [what,who,short(x.get('strAssist'),60)] if v),220),
                'side':'home' if is_yes(x.get('strHome')) else 'away'})
        out['events'].sort(key=lambda x:numeric(x['clock'].replace("'",'')) or 0)
    out['available']=bool(out['statistics'] or out['events'] or any(out['lineup'][s]['starters'] or out['lineup'][s]['substitutes'] for s in ('home','away')))
    out['message']=('Pulsuz mənbə heyətin yalnız bir hissəsini qaytara bilər.' if any(out['lineup'][s]['incomplete'] for s in ('home','away')) else '')
    return out


def espn_details(data):
    out=empty_details('ESPN (qeyri-rəsmi)')
    if not isinstance(data,dict):return out
    rosters=data.get('rosters') or []
    for row in rosters[:2]:
        if not isinstance(row,dict):continue
        side=row.get('homeAway')
        if side not in ('home','away'):continue
        group=out['lineup'][side]
        form=safe_formation(row.get('formation'))
        group['formation']=form
        group['formationVerified']=bool(form)
        for x in (row.get('roster') or [])[:40]:
            if not isinstance(x,dict):continue
            ath=x.get('athlete') or {}
            if not isinstance(ath,dict):ath={}
            photo=ath.get('headshot') or {}
            if isinstance(photo,dict):photo=photo.get('href','')
            place=numeric(x.get('formationPlace'))
            record=player_record(ath.get('displayName') or ath.get('fullName'),x.get('jersey'),
                (x.get('position') or {}).get('abbreviation','') if isinstance(x.get('position'),dict) else '',
                photo,place=place if isinstance(place,int) else None,player_id=ath.get('id'))
            if not record['name']:continue
            key='starters' if x.get('starter') is True else 'substitutes'
            if len(group[key])<35:group[key].append(record)
        # Order starters only by known ESPN formationPlace; no fabricated 1-11.
        if group['starters'] and all(p['place'] is not None for p in group['starters']):
            group['starters'].sort(key=lambda x:x['place'])
        group['incomplete']=bool(group['starters']) and len(group['starters'])!=11
    plays=data.get('scoringPlays') or data.get('plays') or data.get('details') or []
    if isinstance(plays,list):
        for x in plays[:80]:
            if not isinstance(x,dict):continue
            clock=x.get('clock') or {}
            if isinstance(clock,dict):clock=clock.get('displayValue','')
            typ=x.get('type') or {}
            if isinstance(typ,dict):typ=typ.get('text','')
            text=short(x.get('text') or x.get('description') or typ,220)
            if text:out['events'].append({'clock':short(clock,16),'text':text})
    out['available']=bool(out['events'] or any(out['lineup'][s]['starters'] or out['lineup'][s]['substitutes'] for s in ('home','away')))
    out['message']='ESPN interfeysi qeyri-rəsmidir; məlumatlar xəbərdarlıq olmadan dəyişə bilər.'
    return out


def openliga_details(raw):
    out=empty_details('OpenLigaDB (icma məlumatı)')
    if not isinstance(raw,dict):return out
    for x in (raw.get('goals') or [])[:60]:
        if not isinstance(x,dict):continue
        minute=numeric(x.get('matchMinute'))
        name=short(x.get('goalGetterName'),85)
        if not name:continue
        out['events'].append({'clock':str(minute)+"'" if minute is not None else '',
           'text':'⚽ '+name,
           'score':(str(x.get('scoreTeam1'))+' : '+str(x.get('scoreTeam2'))) if x.get('scoreTeam1') is not None and x.get('scoreTeam2') is not None else ''})
    out['available']=bool(out['events'])
    out['message']='OpenLigaDB matçın ilk 11-liyini və formasiya məlumatını vermir.'
    return out
