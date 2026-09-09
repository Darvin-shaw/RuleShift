"""Extract conditions and source spans from controlled Chinese release rules."""

import argparse
import json
from pathlib import Path


class UnsupportedRule(ValueError):
    """The clause cannot be represented without guessing."""


def expression(text: str, start: int, end: int) -> dict:
    """Parse parentheses, disjunction, conjunction and prefix negation."""
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    if start == end:
        raise UnsupportedRule("empty condition")
    depth, operators, closing = 0, [], None
    for index in range(start, end):
        char = text[index]
        if char == '（':
            depth += 1
            if depth > 32:
                raise UnsupportedRule("parentheses nested too deeply")
        elif char == '）':
            depth -= 1
            if depth < 0:
                raise UnsupportedRule("unbalanced parentheses")
            if depth == 0 and closing is None:
                closing = index
        elif depth == 0 and char in '且或':
            operators.append((index, char))
    if depth:
        raise UnsupportedRule("unbalanced parentheses")
    node = dict(span=[start, end], text=text[start:end])
    if text[start] == '（' and closing == end - 1:
        return dict(node, op='group', children=[expression(text, start + 1, end - 1)])
    for symbol, op in [('或', 'or'), ('且', 'and')]:
        cuts = [i for i, char in operators if char == symbol]
        if cuts:
            bounds = [start - 1, *cuts, end]
            return dict(node, op=op, children=[expression(text, a + 1, b) for a, b in zip(bounds, bounds[1:])])
    if text.startswith('并非', start):
        return dict(node, op='not', children=[expression(text, start + 2, end)])
    atom = text[start:end]
    if any(char in atom for char in '（），；。()') or any(word in atom for word in ('如果', '除非', '只有', '否则', '但')):
        raise UnsupportedRule("unsupported condition syntax")
    return dict(node, op='atom')


def extract(text: str) -> dict:
    """Return exact character offsets; never read candidate labels or facts."""
    if not isinstance(text, str) or not text or len(text) > 4000:
        raise UnsupportedRule("expected 1 to 4000 characters")
    marker = '时允许放行'
    if text.count(marker) != 1:
        raise UnsupportedRule("expected one release condition")
    condition_end = text.index(marker)
    tail_start = condition_end + len(marker)
    tail = text[tail_start:].rstrip()
    condition = expression(text, 0, condition_end)
    exceptions = []
    fallback = None
    if tail == '，否则禁止放行。':
        fallback = '禁止放行'
    elif tail.startswith('；但'):
        exception_start = tail_start + len('；但')
        suffix = '时禁止放行。'
        exception_end = text.find(suffix, exception_start)
        if exception_end < 0:
            raise UnsupportedRule("missing exception outcome")
        rest = text[exception_end + len(suffix):].rstrip()
        if rest not in ('', '检验不合格时禁止放行。'):
            raise UnsupportedRule("unsupported trailing rule")
        if rest and condition['text'] != '检验合格':
            raise UnsupportedRule("unrelated fallback")
        exceptions.append(expression(text, exception_start, exception_end))
        fallback = '禁止放行' if rest else None
    else:
        raise UnsupportedRule("unsupported release outcome")
    return dict(schema_version=1, source_text=text, condition=condition,
                outcome=dict(text='允许放行', span=[condition_end + 1, tail_start]),
                exceptions=exceptions, otherwise=fallback)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='UTF-8 file containing one clause')
    args = parser.parse_args()
    try:
        result = extract(args.input.read_text(encoding='utf-8'))
    except (OSError, ValueError, RecursionError) as error:
        print(json.dumps(dict(status='unsupported', reason=type(error).__name__)))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
