"""Align release clauses using structure, explicit IDs and lexical candidates."""

from collections import Counter
from difflib import SequenceMatcher
import re

if __package__:
    from .extract_rules import UnsupportedRule, extract_document
else:
    from extract_rules import UnsupportedRule, extract_document


def condition_key(node: dict) -> tuple:
    """Normalize only explicit Boolean structure and documented score wording."""
    op = node['op']
    if op == 'atom':
        text = ''.join(node['text'].split())
        match = re.fullmatch(r'复检评分(?:至少|达到)(\d+)分', text)
        return ('score_ge', int(match[1])) if match else ('atom', text)
    if op == 'group':
        return condition_key(node['children'][0])
    children = [condition_key(child) for child in node['children']]
    if op in ('and', 'or'):
        flattened = []
        for child in children:
            flattened.extend(child[1:] if child[0] == op else [child])
        children = sorted(set(flattened))
    return (op, *children)


def rule_key(rule: dict) -> tuple:
    return (condition_key(rule['condition']), rule['outcome']['text'],
            tuple(sorted(condition_key(e) for e in rule['exceptions'])), rule['otherwise'])


def describe(clauses: list[dict]) -> list[dict]:
    if not isinstance(clauses, list) or len(clauses) > 100:
        raise ValueError('expected at most 100 clauses per version')
    result, ids = [], set()
    for clause in clauses:
        if (not isinstance(clause, dict) or set(clause) != {'id', 'text'}
                or not isinstance(clause['id'], str) or not clause['id'] or clause['id'] in ids):
            raise ValueError('invalid or duplicate clause ID')
        if not isinstance(clause['text'], str) or len(clause['text']) > 10000:
            raise ValueError('invalid clause text')
        ids.add(clause['id'])
        try:
            rules = extract_document(clause['text'])
            result.append(dict(clause, rules=rules, key=tuple(rule_key(rule) for rule in rules)))
        except UnsupportedRule as error:
            result.append(dict(clause, rules=[], key=None, issue=str(error)))
    return result


def similarity(left: str, right: str) -> float:
    # Averaging directions avoids SequenceMatcher's tie-order asymmetry.
    a, b = ''.join(left.split()), ''.join(right.split())
    return (SequenceMatcher(None, a, b, autojunk=False).ratio()
            + SequenceMatcher(None, b, a, autojunk=False).ratio()) / 2


def align(old: list[dict], new: list[dict], threshold: float = 0.65) -> dict:
    """Return conservative correspondences; lexical matches remain candidates."""
    if type(threshold) not in (int, float) or not 0 < threshold <= 1:
        raise ValueError('threshold must be in (0, 1]')
    before, after = describe(old), describe(new)
    pending_old = {i for i, row in enumerate(before) if row['key'] is not None}
    pending_new = {i for i, row in enumerate(after) if row['key'] is not None}
    matches = []

    def record(left, right, kind, basis, score=None):
        matches.append(dict(old_ids=[before[i]['id'] for i in left],
                            new_ids=[after[j]['id'] for j in right], kind=kind, basis=basis, score=score))
        pending_old.difference_update(left)
        pending_new.difference_update(right)

    # Repeated clauses require an ID anchor or stay ambiguous.
    old_counts = Counter(before[i]['key'] for i in pending_old)
    new_counts = Counter(after[j]['key'] for j in pending_new)
    for i in sorted(pending_old):
        key = before[i]['key']
        if old_counts[key] == new_counts[key] == 1:
            j = next(j for j in pending_new if after[j]['key'] == key)
            kind = 'unchanged' if before[i]['text'] == after[j]['text'] else 'wording'
            record([i], [j], kind, 'structure')

    candidates = []
    for reverse in (False, True):
        singles, groups = (after, before) if reverse else (before, after)
        single_ids, group_ids = (pending_new, pending_old) if reverse else (pending_old, pending_new)
        for i in sorted(single_ids):
            for start in sorted(group_ids):
                for size in range(2, 5):
                    indices = list(range(start, start + size))
                    if not set(indices) <= group_ids:
                        continue
                    key = tuple(k for j in indices for k in groups[j]['key'])
                    if singles[i]['key'] == key:
                        left, right = (indices, [i]) if reverse else ([i], indices)
                        candidates.append((left, right, 'merge' if reverse else 'split'))
    for left, right, kind in candidates:
        competing = [c for c in candidates if set(c[0]) & set(left) or set(c[1]) & set(right)]
        if len(competing) == 1:
            record(left, right, kind, 'ordered_rule_structure')

    for i in sorted(pending_old):
        anchored = [j for j in pending_new if before[i]['id'] == after[j]['id']]
        if anchored:
            j = anchored[0]
            equivalent = before[i]['key'] == after[j]['key']
            kind = ('unchanged' if before[i]['text'] == after[j]['text'] else 'wording') if equivalent else 'modified'
            record([i], [j], kind, 'stable_id')

    lexical = [dict(old_id=before[i]['id'], new_id=after[j]['id'], score=round(score, 6))
               for i in sorted(pending_old) for j in sorted(pending_new)
               if (score := similarity(before[i]['text'], after[j]['text'])) >= threshold]
    return dict(matches=matches, candidates=lexical,
                unmatched_old=[before[i]['id'] for i in sorted(pending_old)],
                unmatched_new=[after[j]['id'] for j in sorted(pending_new)],
                unsupported=[dict(side=side, id=row['id'], reason=row['issue'])
                             for side, rows in [('old', before), ('new', after)] for row in rows if row['key'] is None],
                extraction=dict(old=before, new=after))
