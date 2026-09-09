"""Measure extraction coverage on registered real clauses without model changes."""

import argparse
import hashlib
import json
from pathlib import Path

if __package__:
    from .extract_rules import UnsupportedRule, extract
    from .source_registry import MANIFEST, ROOT, read_local, strict_json, validate_manifest
else:
    from extract_rules import UnsupportedRule, extract
    from source_registry import MANIFEST, ROOT, read_local, strict_json, validate_manifest


def assess(samples: list[dict]) -> dict:
    """Coverage is a necessary gate, not semantic accuracy or proof of generalization."""
    if not isinstance(samples, list) or not samples:
        raise ValueError('empty samples')
    rows, ids = [], set()
    for sample in samples:
        if (not isinstance(sample, dict) or set(sample) != {'id', 'text'}
                or not isinstance(sample['id'], str) or not sample['id'] or sample['id'] in ids):
            raise ValueError('invalid sample')
        if not isinstance(sample['text'], str) or not sample['text'].strip():
            raise ValueError('empty text')
        ids.add(sample['id'])
        row = dict(id=sample['id'], text_sha256=hashlib.sha256(sample['text'].encode()).hexdigest())
        try:
            row.update(status='parsed', extraction=extract(sample['text']))
        except UnsupportedRule as error:
            row.update(status='unsupported', reason=str(error))
        rows.append(row)
    parsed = sum(row['status'] == 'parsed' for row in rows)
    coverage = parsed / len(rows)
    return dict(total=len(rows), parsed=parsed, coverage=coverage,
                minimum_coverage=0.8, decision='not_passed' if coverage < 0.8 else 'semantic_validation_required',
                semantic_accuracy=None, version_alignment=None, rows=rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, help='Registered JSON with a samples list')
    args = parser.parse_args()
    try:
        manifest = strict_json(read_local(ROOT, MANIFEST))
        if validate_manifest(manifest, ROOT, 'research'):
            raise ValueError('admission denied')
        sources = [s for s in manifest['sources'] if any(a['path'] == args.source for a in s['artifacts'])]
        if len(sources) != 1 or sources[0]['class'] == 'S' or sources[0]['permissions']['model_input'] is not True:
            raise ValueError('registered real source with local model permission required')
        raw = read_local(ROOT, args.source)
        report = assess(strict_json(raw)['samples'])
        report.update(source_id=sources[0]['id'], source_sha256=hashlib.sha256(raw).hexdigest(),
                      code_sha256={name: hashlib.sha256((ROOT / 'scripts' / name).read_bytes()).hexdigest()
                                   for name in ('extract_rules.py', 'check_real_text.py')})
        output = ROOT / 'data/generated/real-text-check.json'
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        print(json.dumps({key: report[key] for key in ('total', 'parsed', 'coverage', 'decision')}))
        return 2
    except (OSError, ValueError, KeyError, TypeError, RecursionError):
        print('Real-text source rejected before evaluation')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
