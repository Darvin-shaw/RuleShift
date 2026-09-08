import copy
import json
import unittest
from unittest.mock import patch

from scripts import run_w3_eval as evaluation
from scripts.w3_baselines import predict
from scripts import update_stargazers as stars
from scripts.ai_annotate import build_annotations, validate


class W3Tests(unittest.TestCase):
    def setUp(self):
        self.raw = (evaluation.ROOT / 'data/public/SYN-W3-AI-TRIAL-001.json').read_bytes()
        self.freeze = json.loads((evaluation.ROOT / 'data/public/SYN-W3-FREEZE-001.json').read_bytes())
        self.records = evaluation.prepare(self.raw, self.freeze)

    def test_freeze_and_label_separation(self):
        self.assertEqual(len(self.records), 50)
        self.assertEqual(sum(r['split'] == 'test' for r in self.records), 20)
        self.assertTrue(all('reference' not in r['prompt'] for r in self.records))
        fixture = json.loads(self.raw)
        for family in fixture['families']:
            for pair in family['pairs']:
                for judgment in pair['judgments']:
                    judgment['candidate_label'] = '否定'
        raw = json.dumps(fixture).encode()
        freeze = dict(self.freeze, source_sha256=evaluation.digest(raw))
        changed = evaluation.prepare(raw, freeze)
        self.assertEqual([predict(r['prompt']) for r in self.records],
                         [predict(r['prompt']) for r in changed])

    def test_reject_changed_data_and_leakage(self):
        with self.assertRaisesRegex(ValueError, 'freeze_mismatch'):
            evaluation.prepare(self.raw + b' ', self.freeze)
        self.freeze['splits']['test'].append(self.freeze['splits']['train'][0])
        with self.assertRaisesRegex(ValueError, 'family_leakage'):
            evaluation.prepare(self.raw, self.freeze)

    def test_reject_duplicate_pair(self):
        fixture = json.loads(self.raw)
        family = fixture['families'][0]
        family['pairs'].append(copy.deepcopy(family['pairs'][0]))
        raw = json.dumps(fixture).encode()
        self.freeze['source_sha256'] = evaluation.digest(raw)
        with self.assertRaisesRegex(ValueError, 'duplicate_pair'):
            evaluation.prepare(raw, self.freeze)

    def test_date_boundary_and_invalid_number(self):
        task = copy.deepcopy(self.records[0]['prompt'])
        task['facts'] = {'defects': True}
        self.assertEqual(predict(task)['label'], '无法确定')
        task['facts'] = {'defects': 0}
        self.assertEqual(predict(task)['label'], '支持')
        task['target_time'] = task['version']['valid_until']
        self.assertEqual(predict(task)['evidence'], '')

    def test_decisive_conditions_with_missing_facts(self):
        examples = [('且审批', {'approved': False}, '否定'),
                    ('或让步', {'waiver': True}, '支持'),
                    ('但发生', {'contaminated': True}, '否定')]
        for fragment, facts, label in examples:
            task = copy.deepcopy(next(r['prompt'] for r in self.records if fragment in r['prompt']['version']['text']))
            task['facts'] = facts
            self.assertEqual(predict(task)['label'], label)
            self.assertEqual(predict(task)['missing_facts'], [])

    def test_metrics_by_hand(self):
        rows = [dict(pair_id='p', reference='支持', label='支持', evidence='x', reference_evidence='x'),
                dict(pair_id='p', reference='否定', label='支持', evidence='', reference_evidence='y')]
        result = evaluation.metrics(rows)
        self.assertEqual(result['accuracy'], 0.5)
        self.assertEqual(result['pair_accuracy'], 0)
        self.assertEqual(result['change_accuracy'], 0)
        self.assertAlmostEqual(result['macro_f1'], 2 / 9)

    def test_projection_tampering(self):
        fixture = json.loads(self.raw)
        result = build_annotations(self.raw, fixture)
        result['tasks'][0]['facts'] = {'fabricated': True}
        self.assertIn('projection_mismatch', validate(result, self.raw, fixture))


class StarTests(unittest.TestCase):
    def test_render_idempotent_and_removes_users(self):
        original = 'before\n' + stars.START + '\nold\n' + stars.END + '\nafter'
        result = stars.render(original, ['Alice'])
        self.assertEqual(result, stars.render(result, ['Alice']))
        self.assertNotIn('@Alice', stars.render(result, []))
        self.assertTrue(result.startswith('before\n'))
        self.assertTrue(result.endswith('\nafter'))
        with self.assertRaises(ValueError):
            stars.render(result + stars.START, [])

    def test_pagination(self):
        from io import BytesIO
        pages = [BytesIO(json.dumps([{'login': f'user{i}'} for i in range(100)]).encode()),
                 BytesIO(b'[{"login":"last"}]')]
        with patch.object(stars, 'urlopen', side_effect=pages) as request:
            self.assertEqual(len(stars.fetch_users('owner/repo')), 101)
            self.assertIn('page=2', request.call_args.args[0].full_url)

    def test_api_failure_propagates(self):
        with patch.object(stars, 'urlopen', side_effect=OSError('unavailable')):
            with self.assertRaises(OSError):
                stars.fetch_users('owner/repo')
