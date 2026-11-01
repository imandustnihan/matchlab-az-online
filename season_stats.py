"""MATCHLAB AZ: conservative, request-limited football season statistics.

TheSportsDB V1 public API: searches are on demand, and the free player-stats
endpoint can return at most 10 statistic records per player. Never infer that
missing stats are zero, or that the first search hit is the right person.
A full date-of-birth plus a compatible name is required for linkage (unless
an externally verified provider ID has been explicitly recorded).

Provider terms (2026): free API is for development projects; app-store
publication requires a paid subscription. No site scraping.
"""
import datetime as dt
import re
import unicodedata
import urllib.parse

ROOT = 'https://www.thesportsdb.com/api/v1/json/123/'


def normalize(value):
    raw = str(value or '').casefold().replace('ə', 'e').replace('ı', 'i').replace('ł', 'l')
    raw = ''.join(c for c in unicodedata.normalize('NFKD', raw) if not unicodedata.combining(c))
    return ' '.join(re.findall(r'[^\W_]+', raw, re.UNICODE))


def iso_birth(value):
    """Accept unambiguous *full* dates. Year-only is insufficient for identity."""
    value = str(value or '').strip()
    m = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})(?:T[^\s]*)?', value)
    if not m:
        return ''
    try:
        return dt.date(*map(int, m.groups())).isoformat()
    except ValueError:
        return ''


def name_compatible(profile_name, provider_name):
    a = normalize(profile_name)
    b = normalize(provider_name)
    if not a or not b:
        return False
    if a == b:
        return True
    # Two distinctive shared tokens + identical full DOB. Handles
    # "Lionel Messi" vs "Lionel Andrés Messi" without fuzzy conflation.
    aa = {x for x in a.split() if len(x) >= 3}
    bb = {x for x in b.split() if len(x) >= 3}
    return len(aa & bb) >= 2


def verified_provider_id(profile, results):
    birth = iso_birth(profile.get('birth'))
    if not birth or profile.get('kind') not in ('players', 'coaches'):
        return None, 'Kimlik yoxlaması üçün tam doğum tarixi mövcud deyil.'
    matches = []
    for x in results if isinstance(results, list) else []:
        if not isinstance(x, dict) or normalize(x.get('strSport')) not in ('soccer', 'football'):
            continue
        candidate_birth = iso_birth(x.get('dateBorn') or x.get('strDateBorn') or x.get('dateBirth') or '')
        if candidate_birth != birth:
            continue
        if not name_compatible(profile.get('name'), x.get('strPlayer')):
            continue
        ident = str(x.get('idPlayer') or '')
        if re.fullmatch(r'\d{1,12}', ident):
            matches.append(ident)
    uniq = list(dict.fromkeys(matches))
    if len(uniq) == 1:
        return uniq[0], ''
    if len(uniq) > 1:
        return None, 'Birdən çox uyğun şəxs tapıldı. Kimlik qeyri-müəyyəndir.'
    return None, 'TheSportsDB-də ad və doğum tarixi ilə təsdiqlənmiş uyğun profil tapılmadı.'


def stat_category(value):
    x = normalize(value)
    if x in ('assists','assist','goal assists','goal assist','total assists','total goal assists'):
        return 'assists'
    if x in ('goals','goal','goals scored','total goals','scored goals'):
        return 'goals'
    if x in ('appearances','appearance','matches played','games played','matches','games','total appearances'):
        return 'appearances'
    if x in ('minutes played','minutes','playing time minutes'):
        return 'minutes'
    if x in ('yellow cards','yellow card'):
        return 'yellowCards'
    if x in ('red cards','red card'):
        return 'redCards'
    return None


def valid_stat(value):
    if isinstance(value, bool):
        return None
    s = str(value if value is not None else '').strip().replace(',', '')
    if not re.fullmatch(r'\d{1,6}(?:\.0+)?', s):
        return None
    n = int(float(s))
    return n if n <= 200000 else None


def parse_player_stats(payload, player_id):
    entries = payload.get('playerstats') if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        entries = []
    groups = {}
    valid_records = 0
    for item in entries[:10]:
        if not isinstance(item, dict):
            continue
        if str(item.get('idPlayer') or '') != str(player_id):
            continue
        if normalize(item.get('strSport')) not in ('soccer', 'football'):
            continue
        category = stat_category(item.get('strStatistic'))
        val = valid_stat(item.get('strValue'))
        if category is None or val is None:
            continue
        season = str(item.get('strSeason') or '').strip()
        if not re.fullmatch(r'(?:19|20)\d{2}(?:[-/](?:\d{2}|(?:19|20)\d{2}))?', season):
            continue
        league = str(item.get('strLeague') or '')[:100].strip()
        team = str(item.get('strTeam') or '')[:100].strip()
        key = (season, league, team)
        group = groups.setdefault(key, {
            'season': season, 'competition': league, 'team': team,
            'appearances': None, 'goals': None, 'assists': None,
            'minutes': None, 'yellowCards': None, 'redCards': None,
        })
        # Duplicate category rows may represent different phases; don't add
        # them up or pick an arbitrary row as an authoritative total.
        if group[category] is None:
            group[category] = val
        elif group[category] != val:
            group[category] = None
        valid_records += 1
    rows = sorted(groups.values(), key=lambda x: (x['season'], x['competition'], x['team']), reverse=True)
    return {
        'items': rows,
        'available': bool(rows),
        'partial': len(entries) >= 10,
        'recordsSeen': min(len(entries), 10),
        'source': 'TheSportsDB V1 Free (məhdud)',
        'sourceUrl': ROOT + 'lookupplayerstats.php?id=' + str(player_id),
        'scope': 'Mövsüm / yarış / klub üzrə; tam karyera deyil',
        'notice': 'Pulsuz API ən çox 10 statistika qeydi qaytarır. Göstərilməyən assist və matçlar sıfır deyil.',
    }


def lookup(profile, get_json):
    """On-demand public API lookup, no account/key requirement.

    get_json is a caller-provided (url, ttl) adapter, so this module is
    unit-testable without network access.
    """
    result = {
        'items': [], 'available': False, 'partial': False,
        'source': 'TheSportsDB V1 Free (məhdud)',
        'scope': 'Mövsüm / yarış / klub üzrə', 'sourceUrl': '',
        'identityVerified': False,
        'message': 'Bu futbolçu üzrə mənbədə təsdiqlənmiş mövsüm statistikası tapılmadı.',
    }
    if not isinstance(profile, dict) or profile.get('kind') not in ('players','coaches'):
        result['message'] = 'Yalnız futbolçu karyerası üçün statistika sorğulana bilər.'
        return result
    if not iso_birth(profile.get('birth')):
        result['message'] = 'Dəqiq kimlik yoxlaması üçün tam doğum tarixi yoxdur; başqa şəxsin statistikası göstərilmir.'
        return result
    name = str(profile.get('name') or '').strip()[:100]
    if len(name) < 3:
        return result
    url = ROOT + 'searchplayers.php?' + urllib.parse.urlencode({'p': name})
    payload = get_json(url, 7200)
    provider_id, error = verified_provider_id(profile, payload.get('player') if isinstance(payload, dict) else [])
    if provider_id is None:
        result['message'] = error
        return result
    result['identityVerified'] = True
    result['providerPlayerId'] = provider_id
    data = get_json(ROOT + 'lookupplayerstats.php?id=' + provider_id, 7200)
    parsed = parse_player_stats(data, provider_id)
    result.update(parsed)
    result['identityVerified'] = True
    result['message'] = ('Mövsüm statistikası mənbədən alındı.' if parsed['available'] else
                         'Kimlik təsdiqləndi, amma bu futbolçu üçün pulsuz mövsüm statistikası yoxdur.')
    return result
