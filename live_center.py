"""MATCHLAB AZ live scoreboard aggregation.

Data is always upstream supplied (never guessed). The 'all' view fetches all
configured competitions concurrently with bounded work and short-lived caches.
A checkedAt timestamp refers to OUR last upstream check, not proof of provider
real-time latency. ESPN endpoints are undocumented and best-effort.
"""
import concurrent.futures
import datetime
import threading
import time
import league_catalog
from zoneinfo import ZoneInfo

LEAGUE_NAMES = {
    'eng.1': 'Premier League', 'esp.1': 'La Liga', 'ger.1': 'Bundesliga',
    'ita.1': 'Serie A', 'fra.1': 'Ligue 1', 'uefa.champions': 'Champions League',
    'uefa.europa': 'Europa League', 'tur.1': 'Süper Lig',
    'por.1': 'Primeira Liga', 'ned.1': 'Eredivisie',
    'usa.1': 'MLS', 'ksa.1': 'Saudi Pro League',
    'aze.1': 'Azərbaycan Premyer Liqası', 'sco.1':'Scottish Premiership', 'bel.1':'Belgian Pro League',
}
LEAGUE_NAMES.update(league_catalog.EXTRA_LEAGUES)
_LOCK = threading.Lock()
_CACHE = {}
_FLIGHT = {}


def baku_today():
    return datetime.datetime.now(ZoneInfo('Asia/Baku')).date().isoformat()


def _compute_view(league, date, load_one):
    """Produce honest match lists. load_one(league, date) is injected for tests."""
    if league != 'all' and league not in LEAGUE_NAMES:
        return {'items': [], 'available': False, 'message': 'Liqa mövcud deyil'}
    ttl = 25 if date == baku_today() else 600
    key = (league, date)
    now = time.monotonic()
    with _LOCK:
        old = _CACHE.get(key)
        if old and now - old[0] < ttl:
            return dict(old[1], cached=True)
    targets = list(league_catalog.CORE_LEAGUES) if league == 'all' else [league]
    results = {}
    def load(name):
        try:
            r = load_one(name, date)
            if not isinstance(r, dict) or not isinstance(r.get('items'), list):
                raise ValueError('unexpected provider response')
            return name, r
        except Exception as exc:
            return name, {'items': [], 'available': False, 'partial': True,
                          'source': name, 'message': type(exc).__name__}
    if league == 'all':
        # 8 concurrent adapters bound per-user latency; the API cache prevents
        # every open browser tab from hammering the sources.
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            for name, result in executor.map(load, targets):
                results[name] = result
    else:
        name, result = load(league)
        results[name] = result
    all_items = []
    errors = []
    seen = set()
    partial = False
    ok = 0
    for name in targets:
        r = results[name]
        if r.get('available'):
            ok += 1
        else:
            errors.append(name)
        partial = partial or bool(r.get('partial')) or not bool(r.get('available')) or bool(r.get('stale'))
        for item in r['items']:
            if not isinstance(item, dict):
                continue
            item = dict(item)
            item['league'] = name
            item['leagueName'] = LEAGUE_NAMES[name]
            item['stale'] = bool(r.get('stale'))
            ident = str(item.get('id') or '')
            if not ident or ident in seen:
                continue
            seen.add(ident)
            all_items.append(item)
    def sort_key(match):
        # A genuine live match is placed first, then fixtures by kick-off time.
        priority = {'live': 0, 'scheduled': 1, 'final': 2}.get(match.get('state'), 3)
        return (priority, str(match.get('date') or ''), match.get('leagueName', ''))
    all_items.sort(key=sort_key)
    result = {
        'items': all_items, 'available': ok > 0,
        'partial': partial,
        'stale': not bool(ok) and bool(all_items),
        'source': f'{ok}/{len(targets)} liqa mənbəsi' if league == 'all' else results[league].get('source', ''),
        'message': ('Bəzi liqalar üçün canlı məlumat əlçatan deyil: '+', '.join(errors)) if errors else '',
        'checkedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
        'coverage': {'checked': len(targets), 'available': ok, 'failedLeagues': errors},
        'liveCount': sum(1 for x in all_items if x.get('state') == 'live' and not x.get('stale')),
    }
    if not ok and not all_items:
        result['message'] = 'Seçilmiş liqalar üçün mənbə cavab vermədi.'
    with _LOCK:
        _CACHE[key] = (time.monotonic(), result)
        # Bound the cache to 40 date/league keys.
        if len(_CACHE) > 40:
            for k in list(_CACHE)[:len(_CACHE)-40]:
                _CACHE.pop(k, None)
    return result


def view(league, date, load_one):
    """Coalesce concurrent tabs for a single date/league to one upstream check."""
    if league != 'all' and league not in LEAGUE_NAMES:
        return {'items': [], 'available': False, 'message': 'Liqa mövcud deyil'}
    key = (league, date)
    ttl = 25 if date == baku_today() else 600
    with _LOCK:
        old = _CACHE.get(key)
        if old and time.monotonic() - old[0] < ttl:
            return dict(old[1], cached=True)
        lock = _FLIGHT.setdefault(key, threading.Lock())
    with lock:
        with _LOCK:
            old = _CACHE.get(key)
            if old and time.monotonic() - old[0] < ttl:
                return dict(old[1], cached=True)
        return _compute_view(league, date, load_one)
