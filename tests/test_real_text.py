import unittest

from scripts.check_real_text import assess


class RealTextGateTests(unittest.TestCase):
    def test_unsupported_is_not_a_successful_abstention(self):
        result = assess([dict(id='synthetic-test', text='本句是原创测试输入。')])
        self.assertEqual(result['coverage'], 0)
        self.assertEqual(result['decision'], 'not_passed')
        self.assertIsNone(result['semantic_accuracy'])

    def test_parsing_cannot_prove_generalization(self):
        result = assess([dict(id='synthetic-test', text='甲时允许放行，否则禁止放行。')])
        self.assertEqual(result['coverage'], 1)
        self.assertEqual(result['decision'], 'semantic_validation_required')

    def test_empty_and_duplicate_samples_rejected(self):
        with self.assertRaises(ValueError):
            assess([])
        with self.assertRaises(ValueError):
            assess([dict(id='a', text='甲'), dict(id='a', text='乙')])

    def test_synthetic_source_cannot_be_used_for_real_acceptance(self):
        import subprocess
        import sys
        from scripts.source_registry import ROOT
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/check_real_text.py'),
                                 '--source', 'data/public/SYN-W3-AI-TRIAL-001.json'], capture_output=True)
        self.assertEqual(result.returncode, 1)
