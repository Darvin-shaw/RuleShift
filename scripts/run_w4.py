"""Extract and align registered rule versions without changing W3 artifacts."""

import argparse
import hashlib
import json
from pathlib import Path

if __package__:
    from .align_versions import align
    from .source_registry import MANIFEST, read_local, strict_json, validate_manifest
else:
    from align_versions import align
    from source_registry import MANIFEST, read_local, strict_json, validate_manifest

ROOT = Path(__file__).resolve().parents[1]


def process(data: dict, threshold: float = 0.65) -> list[dict]:
    """Process explicit clause pairs or adjacent versions within each family."""
    if set(data) == {'old', 'new'}:
        return [dict(pair_id='input', **align(data['old'], data['new'], threshold))]
    results, ids = [], set()
    for family in data['families']:
        fid = family['family_id']
        if not isinstance(fid, str) or not fid or fid in ids:
            raise ValueError('invalid family ID')
        ids.add(fid)
        versions = family['versions']
        if len(versions) < 2 or len({v['version_id'] for v in versions}) != len(versions):
            raise ValueError('expected distinct adjacent versions')
        for old, new in zip(versions, versions[1:]):
            def clauses(version):
                return version['clauses'] if 'clauses' in version else [dict(id=fid, text=version['text'])]
            results.append(dict(pair_id=f"{fid}:{old['version_id']}:{new['version_id']}",
                                **align(clauses(old), clauses(new), threshold)))
    if not results:
        raise ValueError('empty dataset')
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/w4.json')
    args = parser.parse_args()
    try:
        config = strict_json(args.config.read_bytes())
        if set(config) != {'source', 'output', 'similarity_threshold'}:
            raise ValueError('invalid configuration fields')
        manifest = strict_json(read_local(ROOT, MANIFEST))
        if validate_manifest(manifest, ROOT, 'research'):
            raise ValueError('source registry rejected')
        if config['source'] not in {a['path'] for s in manifest['sources'] for a in s['artifacts']}:
            raise ValueError('source must be registered')
        raw = read_local(ROOT, config['source'])
        pairs = process(strict_json(raw), config['similarity_threshold'])
        output = (ROOT / config['output']).resolve()
        if not output.is_relative_to(ROOT / 'data/generated'):
            raise ValueError('output must be under data/generated')
        unsupported = sum(len(pair['unsupported']) for pair in pairs)
        report = dict(schema_version=1, source_sha256=hashlib.sha256(raw).hexdigest(),
                      code_sha256={name: hashlib.sha256((ROOT / 'scripts' / name).read_bytes()).hexdigest()
                                   for name in ('extract_rules.py', 'align_versions.py', 'run_w4.py')},
                      similarity_threshold=config['similarity_threshold'], pairs=pairs,
                      summary=dict(pair_count=len(pairs), unsupported=unsupported,
                                   matched=sum(len(p['matches']) for p in pairs),
                                   candidates=sum(len(p['candidates']) for p in pairs)))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        print(json.dumps(report['summary']))
        return 2 if unsupported else 0
    except (OSError, ValueError, KeyError, TypeError, RecursionError):
        print('W4 input or configuration rejected')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
