import unittest

from scripts.extract_rules import UnsupportedRule, extract


class ExtractionTests(unittest.TestCase):
    def test_nested_logic_and_spans(self):
        text = '检验合格且（审批通过或并非需要审批）时允许放行，否则禁止放行。'
        result = extract(text)
        condition = result['condition']
        self.assertEqual(condition['op'], 'and')
        nested = condition['children'][1]['children'][0]
        self.assertEqual(nested['op'], 'or')
        self.assertEqual(nested['children'][1]['op'], 'not')

        def check(node):
            start, end = node['span']
            self.assertEqual(text[start:end], node['text'])
            for child in node.get('children', []):
                check(child)
        check(condition)
        check(result['outcome'])

    def test_precedence(self):
        node = extract('甲或乙且丙时允许放行，否则禁止放行。')['condition']
        self.assertEqual(node['op'], 'or')
        self.assertEqual(node['children'][1]['op'], 'and')

    def test_exception_and_explicit_fallback(self):
        result = extract('检验合格时允许放行；但发生污染时禁止放行。检验不合格时禁止放行。')
        self.assertEqual(result['exceptions'][0]['text'], '发生污染')
        self.assertEqual(result['otherwise'], '禁止放行')
        result = extract('检验合格时允许放行；但发生污染时禁止放行。')
        self.assertIsNone(result['otherwise'])

    def test_negation_not_inferred_from_atom(self):
        node = extract('缺陷数不超过3时允许放行，否则禁止放行。')['condition']
        self.assertEqual(node['op'], 'atom')
        self.assertEqual(node['text'], '缺陷数不超过3')

    def test_reject_ambiguous_or_broken_input(self):
        for condition in ('', '甲且', '（甲或乙', '甲）', '除非甲', '甲，但乙', '甲(乙)'):
            with self.subTest(condition=condition), self.assertRaises(UnsupportedRule):
                extract(condition + '时允许放行，否则禁止放行。')
        with self.assertRaises(UnsupportedRule):
            extract('甲时允许放行。额外要求')
