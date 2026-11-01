"""Conservative identity unification for football players who also coached.

A shared *verified* Wikidata QID is required to collapse two register rows.
Never join strangers by similar names. Legacy curated IDs are mapped only after
manual Wikipedia/Wikidata verification; expand this map deliberately, not by fuzzy search.
"""
import re

_QID = re.compile(r'^Q[1-9][0-9]{0,11}$')
_REGISTRY = re.compile(r'^r[pc][a-z0-9]{8,30}$|^reep_[a-z][a-f0-9]{8,30}$')

VERIFIED_LEGACY_QIDS = {
    'p:mikel-arteta': 'Q185572',
    'c:mikel-arteta': 'Q185572',
}
VERIFIED_ROLES = {'Q185572': ('players', 'coaches')}
KINDS = ('players', 'coaches')


def qid_of(row):
    if not isinstance(row, dict):
        return ''
    identifier = str(row.get('id') or '')
    qid = row.get('wikidataId') or row.get('qid') or VERIFIED_LEGACY_QIDS.get(identifier) or (identifier if _QID.fullmatch(identifier) else '')
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
    if qid:
        r['qid'] = qid
        r['roles'] = roles_of(r)
    return r


def _priority(row):
    # A real registry profile can be opened offline and has verified provenance.
    # Curated legacy IDs are just discovery aliases, not additional people.
    identifier = str(row.get('id') or '')
    return (3 if _REGISTRY.fullmatch(identifier) else 2 if _QID.fullmatch(identifier) else 1 if identifier in VERIFIED_LEGACY_QIDS else 0)


def unify(rows):
    """One result per verified QID in combined player/coach search results.

    Keeps different persons with the same name separate if QIDs differ/missing.
    """
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
        previous = output[pos]
        roles = list(dict.fromkeys(roles_of(previous) + roles_of(r)))
        if _priority(r) > _priority(previous):
            previous, r = r, previous
        previous['roles'] = roles
        if qid:
            previous['qid'] = qid
        output[pos] = previous
    return output
