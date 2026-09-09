import copy
import json
import unittest

from scripts.align_versions import align
from scripts.extract_rules import UnsupportedRule, extract, extract_document
from scripts.run_w4 import ROOT, process


def clause(identity, condition):
    return dict(id=identity, text=f'{condition}时允许放行，否则禁止放行。')


class AlignmentTests(unittest.TestCase):
    def test_wording_and_threshold_change(self):
        before = [clause('a', '复检评分至少80分')]
        wording = align(before, [clause('b', '复检评分达到80分')])
        self.assertEqual(wording['matches'][0]['kind'], 'wording')
        changed = align(before, [clause('a', '复检评分至少81分')])
        self.assertEqual(changed['matches'][0]['kind'], 'modified')

    def test_split_merge_preserve_order(self):
        a, b = clause('a', '甲'), clause('b', '乙')
        combined = dict(id='combined', text=a['text'] + '\n' + b['text'])
        self.assertEqual(align([combined], [a, b])['matches'][0]['kind'], 'split')
        self.assertEqual(align([a, b], [combined])['matches'][0]['kind'], 'merge')
        self.assertFalse(align([combined], [b, a])['matches'])

    def test_duplicates_stay_ambiguous(self):
        result = align([clause('a', '甲'), clause('b', '甲')], [clause('c', '甲')])
        self.assertEqual(result['matches'], [])
        self.assertEqual(len(result['candidates']), 2)

    def test_similar_text_is_only_candidate(self):
        result = align([clause('a', '检验合格')], [clause('b', '检验不合格')])
        self.assertEqual(result['matches'], [])
        self.assertEqual(len(result['candidates']), 1)

    def test_boolean_normalization(self):
        result = align([clause('a', '甲且（乙且丙）')], [clause('b', '丙且乙且甲')])
        self.assertEqual(result['matches'][0]['kind'], 'wording')
        result = align([clause('a', '甲且乙')], [clause('b', '甲或乙')])
        self.assertEqual(result['matches'], [])

    def test_unsupported_and_empty_versions(self):
        result = align([dict(id='a', text='请酌情放行。')], [])
        self.assertEqual(result['unsupported'][0]['id'], 'a')
        self.assertEqual(align([], [clause('a', '甲')])['unmatched_new'], ['a'])

    def test_invalid_input(self):
        for threshold in (0, 2, True, float('nan')):
            with self.assertRaises(ValueError):
                align([], [], threshold)
        with self.assertRaises(ValueError):
            align([clause('a', '甲'), clause('a', '乙')], [])

    def test_whole_document_offsets_and_fallback(self):
        text = '\n  ' + clause('a', '甲')['text'] + '\r\n检验合格时允许放行；但发生污染时禁止放行。检验不合格时禁止放行。\n'
        rules = extract_document(text)
        self.assertEqual(len(rules), 2)
        def check(value):
            if isinstance(value, dict):
                if 'span' in value:
                    a, b = value['span']
                    self.assertEqual(text[a:b], value['text'])
                for child in value.values():
                    check(child)
            elif isinstance(value, list):
                for child in value:
                    check(child)
        check(rules)

    def test_resource_limits(self):
        for text in ('并非' * 100 + '甲', '（' * 33 + '甲' + '）' * 33):
            with self.assertRaises(UnsupportedRule):
                extract(clause('a', text)['text'])

    def test_exception_and_fallback_changes_are_not_wording(self):
        text = '检验合格时允许放行；但发生污染时禁止放行。'
        old = [dict(id='a', text=text)]
        for new_text in (text.replace('发生污染', '出现破损'), text + '检验不合格时禁止放行。'):
            self.assertEqual(align(old, [dict(id='a', text=new_text)])['matches'][0]['kind'], 'modified')

    def test_competing_splits_not_selected_arbitrarily(self):
        a, b = clause('a', '甲'), clause('b', '乙')
        compound = dict(id='whole', text=a['text'] + '\n' + b['text'])
        result = align([compound], [a, b, dict(a, id='c'), dict(b, id='d')])
        self.assertEqual(result['matches'], [])

    def test_configuration_rejection_does_not_write_report(self):
        import subprocess
        import sys
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'must-not-exist.json'
            config = Path(directory) / 'config.json'
            config.write_text(json.dumps(dict(source='data/public/SYN-W3-AI-TRIAL-001.json',
                                             output=str(output), similarity_threshold=0.65)), encoding='utf-8')
            run = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/run_w4.py'), '--config', str(config)],
                                 cwd=directory, capture_output=True)
            self.assertEqual(run.returncode, 1)
            self.assertFalse(output.exists())

    def test_machine_answers_do_not_affect_output(self):
        data = json.loads((ROOT / 'data/public/SYN-W3-AI-TRIAL-001.json').read_bytes())
        original = process(data)
        changed = copy.deepcopy(data)
        for family in changed['families']:
            family['pairs'] = []
        self.assertEqual(original, process(changed))
        self.assertEqual(sum(len(p['matches']) for p in original), 5)
        self.assertTrue(all(not p['unsupported'] for p in original))
