import base64
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from content_modules import MODULES, module_from_title, parse_module, update_module
import publish_publication as publisher


def form_body(name, content=None):
    content = content or {}
    return '\n\n'.join('### ' + label + '\n\n' + content.get(label, '_No response_')
                         for label, _ in MODULES[name][1])


class ModuleTests(unittest.TestCase):
    def test_every_form_matches_schema(self):
        forms = [json.loads(p.read_text(encoding='utf-8')) for p in Path('.github/ISSUE_TEMPLATE').glob('*.yml')
                 if p.name not in ('publication.yml', 'news.yml')]
        self.assertEqual(len(forms), len(MODULES))
        for form in forms:
            name = module_from_title(form['title'])
            self.assertIn(name, MODULES)
            self.assertEqual([f['attributes']['label'] for f in form['body'] if f['type'] != 'markdown'],
                             [label for label, _ in MODULES[name][1]])

    def test_all_modules_preserve_unrelated_content_and_repeat_safely(self):
        for name, (filename, fields) in MODULES.items():
            with self.subTest(module=name):
                original = Path('contents', filename).read_text(encoding='utf-8')
                label, block = fields[0]
                values = parse_module(form_body(name, {label: '新的内容'}), name)
                result = update_module(original, name, values)
                self.assertEqual(result, update_module(result, name, values))
                self.assertIn('新的内容', result)
                if name != '站点信息':
                    start, end = f'<!-- module:{block}:start -->', f'<!-- module:{block}:end -->'
                    self.assertEqual(original.split(start)[0], result.split(start)[0])
                    self.assertEqual(original.split(end)[1], result.split(end)[1])
                else:
                    self.assertEqual(original.splitlines()[1:], result.splitlines()[1:])

    def test_blank_keeps_other_language_and_explicit_clear(self):
        name = '研究方向'
        values = parse_module(form_body(name, {'中文研究方向': '【清空】'}), name)
        self.assertEqual(values, {'interests-zh': ''})
        original = Path('contents/home.md').read_text(encoding='utf-8')
        result = update_module(original, name, values)
        self.assertIn('<!-- module:interests-zh:start -->\n\n<!-- module:interests-zh:end -->', result)
        self.assertIn('Bio-Big Data Analysis and Management', result)

    def test_invalid_fields_and_markers_fail_closed(self):
        for content in ('', '<!-- module:bio-zh:end -->', '### unexpected heading'):
            with self.subTest(content=content), self.assertRaises(ValueError):
                parse_module(form_body('个人简介', {'中文简介': content}), '个人简介')
        with self.assertRaises(ValueError):
            parse_module('### 中文简介\n\nnew', '个人简介')
        with self.assertRaises(ValueError):
            parse_module(form_body('个人简介', {'中文简介': 'new'}) + '\n\n### 中文简介\n\nagain', '个人简介')
        with self.assertRaises(ValueError):
            update_module('no markers', '个人简介', {'bio-zh': 'new'})
        with self.assertRaises(ValueError):
            update_module('', '个人简介', {'projects-zh': 'new'})

    def test_admissions_tables_and_contacts_are_independent(self):
        table = '##### 研究生\n\n| 要求 | 收获 |\n| --- | --- |\n| Python | 科研训练 |'
        original = Path('contents/home.md').read_text(encoding='utf-8')
        result = update_module(original, '招生说明', parse_module(form_body('招生说明', {'中文招生说明': table}), '招生说明'))
        self.assertIn(table, result)
        self.assertIn('cslqm@henu.edu.cn', result)

    def test_site_values_cannot_inject_yaml_or_html(self):
        value = '<img src=x onerror=alert(1)> : "hello" # test'
        original = Path('contents/config.yml').read_text(encoding='utf-8')
        result = update_module(original, '站点信息', parse_module(form_body('站点信息', {'网页标题': value}), '站点信息'))
        encoded = json.loads(result.splitlines()[0].split(': ', 1)[1])
        self.assertNotIn('<img', encoded)
        self.assertIn('&lt;img', encoded)
        with self.assertRaises(ValueError):
            parse_module(form_body('站点信息', {'网页标题': 'a\nb'}), '站点信息')

    def test_existing_content_is_fully_mapped(self):
        for name, (filename, fields) in MODULES.items():
            if name == '站点信息':
                continue
            text = Path('contents', filename).read_text(encoding='utf-8')
            for _, block in fields:
                self.assertEqual(text.count(f'<!-- module:{block}:start -->'), 1)
                self.assertEqual(text.count(f'<!-- module:{block}:end -->'), 1)


class WorkflowTests(unittest.TestCase):
    def run_event(self, api):
        with tempfile.TemporaryDirectory() as directory:
            event = Path(directory, 'event.json')
            event.write_text(json.dumps({'issue': {'number': 123}, 'sender': {'login': 'owner'}}))
            with patch.dict(os.environ, {'GITHUB_REPOSITORY': 'owner/repo', 'GITHUB_EVENT_PATH': str(event),
                                       'GITHUB_STEP_SUMMARY': str(Path(directory, 'summary'))}), patch.object(publisher, 'api', side_effect=api):
                publisher.main()

    def test_conflict_retry_preserves_concurrent_edit_and_requests_deployment(self):
        text = Path('contents/home.md').read_text(encoding='utf-8')
        updated_remote = update_module(text, '研究方向', {'interests-en': '- Concurrent update'})
        puts, gets, builds = [], [], []

        def api(method, endpoint, data=None):
            if '/issues/' in endpoint:
                return {'title': '[个人简介] test', 'body': form_body('个人简介', {'中文简介': 'New biography'}), 'user': {'login': 'owner'}}
            if '/permission' in endpoint:
                return {'permission': 'admin'}
            if endpoint.endswith('/pages'):
                return {'build_type': 'legacy', 'source': {'path': '/', 'branch': 'pesonal'}}
            if '/contents/' in endpoint:
                if method == 'GET':
                    gets.append(endpoint)
                    content = text if len(gets) == 1 else updated_remote
                    return {'sha': str(len(gets)), 'content': base64.b64encode(content.encode()).decode()}
                puts.append(data)
                if len(puts) == 1:
                    raise HTTPError(endpoint, 409, 'Conflict', {}, None)
                return {'commit': {'sha': 'test-sha'}}
            if endpoint.endswith('/pages/builds'):
                builds.append(data)
                return {}
            self.fail(endpoint)

        with patch.object(publisher.time, 'sleep'):
            self.run_event(api)
        final = base64.b64decode(puts[-1]['content']).decode()
        self.assertIn('Concurrent update', final)
        self.assertIn('New biography', final)
        self.assertEqual(len(builds), 1)

    def test_untrusted_actor_cannot_write(self):
        def api(method, endpoint, data=None):
            self.assertEqual(method, 'GET')
            if '/issues/' in endpoint:
                return {'title': '[站点信息] test', 'body': '', 'user': {'login': 'outsider'}}
            return {'permission': 'read'}
        with self.assertRaises(ValueError):
            self.run_event(api)


if __name__ == '__main__':
    unittest.main()
