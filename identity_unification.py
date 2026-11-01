"""Verified Wikidata identities for catalogue player/coach roles.

Only explicitly verified Wikidata identities merge. An unlinked database row
is never assigned a QID based on name alone. For curated exact-name listings,
we may hide an obvious *uncertain* extra search hit (without altering its ID or
its underlying profile) when one reviewed identity with the same country is
already displayed. Such hiding is deliberately whitelist-only.
"""
import re
import unicodedata

_QID = re.compile(r'^Q[1-9][0-9]{0,11}$')
_REGISTRY = re.compile(r'^r[pc][a-z0-9]{8,30}$|^reep_[a-z][a-f0-9]{8,30}$')
KINDS = ('players', 'coaches')

# Explicit source-verified links: these are only for the curated legacy IDs.
# Registry records with different QIDs are NEVER merged by similar names.
VERIFIED_LEGACY_QIDS = {
    'p:mikel-arteta': 'Q185572', 'c:mikel-arteta': 'Q185572',
    'p:pep-guardiola': 'Q164038', 'c:pep-guardiola': 'Q164038',
    'p:carlo-ancelotti': 'Q174614', 'c:carlo-ancelotti': 'Q174614',
    'p:xabi-alonso': 'Q208104', 'c:xabi-alonso': 'Q208104',
    'p:jurgen-klopp': 'Q83106', 'c:jurgen-klopp': 'Q83106',
    'p:thierry-henry': 'Q45901', 'c:thierry-henry': 'Q45901',
    'c:zinedine-zidane': 'Q1835',
    'p:xavi-hern-ndez': 'Q17500', 'c:xavi-hern-ndez': 'Q17500',
    'p:wayne-rooney': 'Q266613', 'c:wayne-rooney': 'Q266613',
    'p:robin-van-persie': 'Q2339', 'c:robin-van-persie': 'Q2339',
    'p:andrea-pirlo': 'Q43926', 'c:andrea-pirlo': 'Q43926',
    'p:luis-enrique': 'Q222789', 'c:luis-enrique': 'Q222789',
    'p:antonio-conte': 'Q26580', 'c:antonio-conte': 'Q26580',
    'p:diego-simeone': 'Q258115', 'c:diego-simeone': 'Q258115',
    'p:frank-lampard': 'Q41533', 'c:frank-lampard': 'Q41533',
    'p:steven-gerrard': 'Q459830', 'c:steven-gerrard': 'Q459830',
    'c:jos-mourinho': 'Q79983',
    'p:neymar': 'Q142794',
    'p:ronaldo-naz-rio': 'Q529207',
    'p:andr-s-iniesta': 'Q43729',
    # The old seeded catalogue mislabeled Catalonia Q5705 as Lionel Messi.
    'Q5705': 'Q615',
}

# Each individual here has a source-verified player AND coaching career.
_VERIFIED_DUAL_ROLES = {
    'Q185572','Q164038','Q174614','Q208104','Q83106','Q45901',
    'Q1835','Q17500','Q266613','Q2339','Q43926','Q222789',
    'Q26580','Q258115','Q41533','Q459830',
}
VERIFIED_ROLES = {qid: KINDS for qid in _VERIFIED_DUAL_ROLES}

# This list is deliberately only used to suppress *unlinked* exact duplicates
# in search results, never to assign identity facts or rewrite database rows.
# Restrict to full names and countries that were reviewed as curated aliases.
REVIEWED_DISPLAY_NAMES = {
    ('carlo ancelotti','italy'): 'Q174614',
    ('jürgen klopp','germany'): 'Q83106',
    ('pep guardiola','spain'): 'Q164038',
    ('mikel arteta','spain'): 'Q185572',
    ('xabi alonso','spain'): 'Q208104',
    ('thierry henry','france'): 'Q45901',
    ('wayne rooney','england'): 'Q266613',
    ('andrea pirlo','italy'): 'Q43926',
    ('antonio conte','italy'): 'Q26580',
    ('frank lampard','england'): 'Q41533',
    ('steven gerrard','england'): 'Q459830',
}


def _normal(value):
    raw = str(value or '').casefold().replace('ə','e').replace('ı','i')
    raw = ''.join(c for c in unicodedata.normalize('NFKD', raw) if not unicodedata.combining(c))
    return ' '.join(re.findall(r'[^\W_]+', raw))


def qid_of(row):
    if not isinstance(row, dict):
        return ''
    identifier = str(row.get('id') or '')
    mapped = VERIFIED_LEGACY_QIDS.get(identifier)
    qid = mapped or row.get('wikidataId') or row.get('qid') or (identifier if _QID.fullmatch(identifier) else '')
    return str(qid) if _QID.fullmatch(str(qid)) else ''


def roles_of(row):
    roles = []
    for role in [*(row.get('roles') or []), row.get('kind'), *VERIFIED_ROLES.get(qid_of(row), ())]:
        if role in KINDS and role not in roles:
            roles.append(role)
    return roles


def decorate(row):
    r = dict(row)
    qid = qid_of(r)
    if qid and r.get('kind') in KINDS:
        r['qid'] = qid
        r['roles'] = roles_of(r)
    return r


def _priority(row):
    identifier = str(row.get('id') or '')
    return (3 if _REGISTRY.fullmatch(identifier) else 2 if _QID.fullmatch(identifier) else 1 if identifier in VERIFIED_LEGACY_QIDS else 0)


def unify(rows):
    """One result per verified QID, preserving all separate verified persons."""
    output = []
    by_key = {}
    for item in rows:
        r = decorate(item)
        qid = qid_of(r)
        key = 'person:' + qid if qid and r.get('kind') in KINDS else 'id:' + str(r.get('id') or '')
        if key not in by_key:
            by_key[key] = len(output)
            output.append(r)
            continue
        pos = by_key[key]
        old = output[pos]
        roles = list(dict.fromkeys(roles_of(old) + roles_of(r)))
        if _priority(r) > _priority(old):
            old = r
        old['roles'] = roles
        if qid:
            old['qid'] = qid
        output[pos] = old
    return output


def suppress_reviewed_display_duplicates(rows):
    """Hide unlinked, full-name, country-matched legacy duplicates in search only.

    No inference on unknown names, no collapsing different QIDs. Source rows
    remain intact and can still be opened via their exact IDs.
    """
    linked = {}
    for row in rows:
        if row.get('kind') not in KINDS:
            continue
        key = (_normal(row.get('name')), _normal(row.get('country')))
        qid = qid_of(row)
        if qid:
            linked.setdefault(key, set()).add(qid)
    out = []
    for row in rows:
        if row.get('kind') not in KINDS or qid_of(row):
            out.append(row)
            continue
        key = (_normal(row.get('name')), _normal(row.get('country')))
        target = REVIEWED_DISPLAY_NAMES.get(key)
        if target and linked.get(key) == {target}:
            continue
        out.append(row)
    return out
