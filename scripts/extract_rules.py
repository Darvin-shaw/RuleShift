"""Extract conditions and source spans from controlled Chinese release rules."""

import argparse
import json
from pathlib import Path


class UnsupportedRule(ValueError):
    """The clause cannot be represented without guessing."""


def expression(text: str, start: int, end: int, depth_limit: int = 64) -> dict:
    """Parse parentheses, disjunction, conjunction and prefix negation."""
    if depth_limit <= 0:
        raise UnsupportedRule("condition nested too deeply")
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
        return dict(node, op='group', children=[expression(text, start + 1, end - 1, depth_limit - 1)])
    for symbol, op in [('或', 'or'), ('且', 'and')]:
        cuts = [i for i, char in operators if char == symbol]
        if cuts:
            bounds = [start - 1, *cuts, end]
            return dict(node, op=op, children=[expression(text, a + 1, b, depth_limit - 1) for a, b in zip(bounds, bounds[1:])])
    if text.startswith('并非', start):
        return dict(node, op='not', children=[expression(text, start + 2, end, depth_limit - 1)])
    atom = text[start:end]
    if any(char in atom for char in '（），；。()') or any(word in atom for word in ('如果', '除非', '只有', '否则', '但')):
        raise UnsupportedRule("unsupported condition syntax")
    return dict(node, op='atom')


def extract(text: str) -> dict:
    """Return exact character offsets; never read candidate labels or facts."""
    if not isinstance(text, str) or not text or len(text) > 4000:
        raise UnsupportedRule("expected 1 to 4000 characters")
    if any(word in text for word in ('或者', '而且', '并且')):
        raise UnsupportedRule("use explicit 且 or 或 operators")
    marker = '时允许放行'
    if text.count(marker) != 1:
        raise UnsupportedRule("expected one release condition")
    condition_end = text.index(marker)
    tail_start = condition_end + len(marker)
    tail = text[tail_start:].rstrip()
    condition = expression(text, 0, condition_end)
    exceptions = []
    exception_outcomes = []
    fallback = None
    fallback_evidence = None
    if tail == '，否则禁止放行。':
        fallback = '禁止放行'
        fallback_start = tail_start + len('，否则')
        fallback_evidence = dict(text=fallback, span=[fallback_start, fallback_start + len(fallback)])
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
        exception_outcomes.append(dict(text='禁止放行', span=[exception_end + 1, exception_end + 5]))
        fallback = '禁止放行' if rest else None
        if rest:
            fallback_start = exception_end + len(suffix) + len('检验不合格时')
            fallback_evidence = dict(text=fallback, span=[fallback_start, fallback_start + len(fallback)])
    else:
        raise UnsupportedRule("unsupported release outcome")
    return dict(schema_version=1, source_text=text, condition=condition,
                outcome=dict(text='允许放行', span=[condition_end + 1, tail_start]),
                exceptions=exceptions, exception_outcomes=exception_outcomes,
                otherwise=fallback, otherwise_evidence=fallback_evidence)


def extract_document(text: str) -> list[dict]:
    """Extract newline-separated rules with offsets into the complete document."""
    if not isinstance(text, str) or len(text) > 100000:
        raise UnsupportedRule("invalid document size")
    results, offset = [], 0

    def shift(value, amount):
        if isinstance(value, dict):
            for key, child in value.items():
                if key == 'span':
                    value[key] = [n + amount for n in child]
                else:
                    shift(child, amount)
        elif isinstance(value, list):
            for child in value:
                shift(child, amount)

    for line in text.splitlines(keepends=True):
        if line.strip():
            rule = extract(line)
            shift(rule, offset)
            results.append(rule)
        offset += len(line)
    if not results:
        raise UnsupportedRule("empty document")
    return results


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
