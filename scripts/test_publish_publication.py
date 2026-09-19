import unittest
from pathlib import Path
from publish_publication import parse_body, update_markdown, update_news, citation, HEADING


def body(values):
    return '\n\n'.join('### ' + k + '\n\n' + v for k, v in values.items())


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.values = {'论文标题': 'A study', '作者': 'Liu, Q., Wang, Y*',
                       '年份': '2026', '期刊或会议': 'Journal', '代码链接': '_No response_'}

    def test_form_and_idempotence(self):
        values = parse_body(body(self.values))
        original = Path('contents/publications.md').read_text(encoding='utf-8')
        result = update_markdown(original, 12, values)
        self.assertEqual(result, update_markdown(result, 12, values))
        self.assertEqual(original.split(HEADING)[0], result.split(HEADING)[0])
        self.assertIn('25. ', result)
        values['论文标题'] = 'Changed title'
        result = update_markdown(result, 12, values)
        self.assertEqual(result.count('<!-- publication-issue:12 -->'), 1)
        self.assertNotIn('A study', result)
        self.assertIn('Changed title', result)

    def test_invalid_inputs(self):
        for key, value in [('年份', 'tomorrow'), ('论文链接', 'javascript:alert(1)'),
                           ('论文链接', 'https://example.org/a b'), ('论文标题', '')]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                parse_body(body(dict(self.values, **{key: value})))
        with self.assertRaises(ValueError):
            parse_body(body(self.values) + '\n\n### 年份\n\n2025')

    def test_html_and_markdown_are_escaped(self):
        values = parse_body(body(dict(self.values, **{'论文标题': '<script>alert(1)</script> [x](javascript:bad)',
                                                      '论文链接': 'https://example.org/a(b)'})))
        rendered = citation(values)
        self.assertNotIn('<script>', rendered)
        self.assertIn('\\[x\\]', rendered)
        self.assertIn('a%28b%29', rendered)
        self.assertIn('**Liu, Q.**', rendered)


class NewsTests(unittest.TestCase):
    def test_order_edits_and_preservation(self):
        original = 'before\n<!-- managed-news:start -->\n<!-- managed-news:end -->\nafter'
        first = parse_body(body({'新闻日期': '2026-01-01', '中文内容': '旧新闻'}), news=True)
        newer = parse_body(body({'新闻日期': '2026-09-19', '中文内容': '新新闻', '英文内容': 'News'}), news=True)
        result = update_news(update_news(original, 1, first), 2, newer)
        self.assertLess(result.index('新新闻'), result.index('旧新闻'))
        self.assertEqual(result, update_news(result, 2, newer))
        first['新闻日期'] = '2026-12-01'
        result = update_news(result, 1, first)
        self.assertLess(result.index('旧新闻'), result.index('新新闻'))
        self.assertTrue(result.startswith('before\n'))
        self.assertTrue(result.endswith('\nafter'))

    def test_invalid_date_and_damaged_markers(self):
        with self.assertRaises(ValueError):
            parse_body(body({'新闻日期': '2026-02-30', '中文内容': '新闻'}), news=True)
        with self.assertRaises(ValueError):
            update_news('no markers', 1, {})
        with self.assertRaises(ValueError):
            update_news('<!-- managed-news:start -->manual text<!-- managed-news:end -->', 1, {})


if __name__ == '__main__':
    unittest.main()
