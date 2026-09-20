import base64
import json
import os
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from email.message import Message
from io import BytesIO

import sync_scholar as sync
from publish_publication import HEADING, update_markdown


PROFILE = 'qksAJxwAAAAJ'
CONFIG = {'profile_id': PROFILE, 'interval_days': 15, 'excluded_ids': [], 'title_aliases': {}}


def record(id='paper1', title='A novel single cell analysis method', **changes):
    result = {'id': PROFILE + ':' + id, 'title': title, 'authors': 'Q Liu, G Wang',
              'venue': 'Journal 1, 10-20, 2026', 'year': '2026', 'citations': 3,
              'url': 'https://scholar.google.com/citations?citation_for_view=' + PROFILE + ':' + id}
    result.update(changes)
    return result


def page(more=False, title='A novel single cell analysis method', year='2026'):
    return ('<html><table><tr class="gsc_a_tr"><td><a class="gsc_a_at" '
            'href="/citations?view_op=view_citation&amp;citation_for_view=' + PROFILE + ':paper1">'
            + title + '</a><div class="gs_gray">Q Liu, G Wang</div><div class="gs_gray">Journal 1</div></td>'
            '<td><a class="gsc_a_ac">1,234</a></td><td class="gsc_a_y"><span>' + year + '</span></td>'
            '</tr></table><button id="gsc_bpf_more"' + ('' if more else ' disabled=""') + '>More</button></html>')


class ParseTests(unittest.TestCase):
    def test_fetch_respects_http_charset(self):
        response = BytesIO(page(title='Cell\xa0analysis method').encode('iso-8859-1'))
        response.headers = Message()
        response.headers['Content-Type'] = 'text/html; charset=ISO-8859-1'
        with patch.object(sync, 'urlopen', return_value=response):
            rows = sync.fetch_profile(PROFILE)
        self.assertEqual(rows[0]['title'], 'Cell analysis method')

    def test_realistic_row_and_pagination(self):
        rows, more = sync.parse_profile(page(), PROFILE)
        self.assertFalse(more)
        self.assertEqual(rows[0]['id'], PROFILE + ':paper1')
        self.assertEqual(rows[0]['citations'], 1234)
        self.assertEqual(rows[0]['year'], '2026')
        self.assertTrue(sync.parse_profile(page(more=True), PROFILE)[1])

    def test_fail_closed_on_captcha_empty_wrong_profile_and_bad_year(self):
        for source in ('<html>unusual traffic captcha</html>', '', page(year='unknown'),
                       page().replace(PROFILE, 'different-author')):
            with self.subTest(source=source[:30]), self.assertRaises(ValueError):
                sync.parse_profile(source, PROFILE)

    def test_escaped_html_and_truncated_authors(self):
        rows, _ = sync.parse_profile(page(title='&lt;script&gt;alert(1)&lt;/script&gt; &amp; cells'), PROFILE)
        rendered = sync.render_record(rows[0])
        self.assertNotIn('<script>', rendered)
        self.assertIn('&lt;script&gt;', rendered)
        self.assertIn('**Q Liu**', rendered)
        rendered = sync.render_record(record(authors='A Name, ...'))
        self.assertIn('A Name, ...', rendered)


class MergeTests(unittest.TestCase):
    def setUp(self):
        self.original = '#### Projects\n- Preserve me\n\n' + HEADING + '\n1. **Liu, Q.*** (2026). A novel single cell analysis method. Manual journal. [Code](https://example.org).\n'

    def test_dedup_metadata_update_and_manual_preservation(self):
        updated, records, rendered, matches = sync.merge_records(self.original, [record()], {}, CONFIG)
        self.assertEqual(len(rendered), 0)
        self.assertEqual(len(matches), 1)
        self.assertIn('Manual journal. [Code](https://example.org).', updated)
        self.assertIn('**Liu, Q.***', updated)
        self.assertIn('引用 3', updated)
        self.assertEqual(sync.remove_metadata(updated), self.original)
        again, _, _, _ = sync.merge_records(updated, [record(citations=8)], {'records': records}, CONFIG)
        self.assertNotIn('引用 3', again)
        self.assertIn('引用 8', again)
        self.assertEqual(sync.remove_metadata(again), self.original)

    def test_new_records_repeat_update_and_never_delete_absent_records(self):
        new = record(id='paper2', title='Another distinct spatial omics paper')
        updated, records, rendered, _ = sync.merge_records(self.original, [record(), new], {}, CONFIG)
        self.assertEqual(len(rendered), 1)
        again, _, _, _ = sync.merge_records(updated, [record(), new], {'records': records}, CONFIG)
        self.assertEqual(updated, again)
        changed, _, _, _ = sync.merge_records(updated, [dict(new, citations=9)], {'records': records}, CONFIG)
        self.assertIn('引用次数：9', changed)
        self.assertIn('引用 3', changed)
        preserved, _, _, _ = sync.merge_records(updated, [record()], {'records': records}, CONFIG)
        self.assertIn(new['title'], preserved)

    def test_manual_issue_takes_over_auto_entry(self):
        new = record(id='paper2', title='Another distinct spatial omics paper')
        updated, records, _, _ = sync.merge_records(self.original, [new], {}, CONFIG)
        manual = update_markdown(updated, 8, {'论文标题': new['title'], '作者': 'Liu, Q.*', '年份': '2026', '期刊或会议': 'Curated venue'})
        self.assertEqual(manual.count(new['title']), 1)
        self.assertIn('Curated venue', manual)
        final, _, rendered, _ = sync.merge_records(manual, [new], {'records': records}, CONFIG)
        self.assertEqual(len(rendered), 0)
        self.assertEqual(final.count(new['title']), 1)

    def test_exclusions_aliases_and_corrected_manual_title(self):
        wrong = self.original.replace('novel', 'novl')
        aliases = dict(CONFIG, title_aliases={record()['title']: record()['title'].replace('novel', 'novl')})
        self.assertEqual(len(sync.merge_records(wrong, [record()], {}, aliases)[2]), 0)
        self.assertEqual(len(sync.merge_records(self.original, [record()], {}, aliases)[2]), 0)
        excluded = dict(CONFIG, excluded_ids=[record()['id']])
        self.assertEqual(sync.merge_records(self.original, [record()], {}, excluded)[0], self.original)

    def test_duplicate_titles_and_damaged_markers(self):
        new = record(title='Another distinct spatial omics paper')
        other = dict(new, id=PROFILE + ':other')
        self.assertEqual(len(sync.merge_records(self.original, [new, other], {}, CONFIG)[2]), 1)
        with self.assertRaises(ValueError):
            sync.merge_records(self.original + sync.START, [record()], {}, CONFIG)


class ScheduleTests(unittest.TestCase):
    def test_exact_15_days_across_month_boundary(self):
        last = datetime(2026, 1, 31, 2, 17, tzinfo=timezone.utc)
        state = {'last_success_at': last.isoformat()}
        self.assertFalse(sync.is_due(state, last + timedelta(days=14, hours=23), 15))
        self.assertTrue(sync.is_due(state, last + timedelta(days=15), 15))
        self.assertTrue(sync.is_due({}, last, 15))

    def test_not_due_never_fetches_scholar_or_writes(self):
        def api(method, endpoint, data=None):
            self.assertEqual(method, 'GET')
            if endpoint.endswith('/pages'):
                return {'build_type': 'legacy', 'source': {'branch': 'pesonal', 'path': '/'}}
            if '/git/ref/' in endpoint:
                return {'object': {'sha': 'current'}}
            content = CONFIG if sync.CONFIG_PATH in endpoint else {'last_success_at': datetime.now(timezone.utc).isoformat()}
            return {'content': base64.b64encode(json.dumps(content).encode()).decode()}
        with patch.dict(os.environ, {'GITHUB_REPOSITORY': 'owner/repo'}), patch('sys.argv', ['sync_scholar.py']), \
                patch.object(sync, 'api', side_effect=api), patch.object(sync, 'fetch_profile') as fetch:
            sync.main()
            fetch.assert_not_called()

    def test_failed_fetch_never_mutates_repository(self):
        def api(method, endpoint, data=None):
            self.assertEqual(method, 'GET')
            if endpoint.endswith('/pages'):
                return {'build_type': 'legacy', 'source': {'branch': 'pesonal', 'path': '/'}}
            if '/git/ref/' in endpoint:
                return {'object': {'sha': 'current'}}
            content = CONFIG if sync.CONFIG_PATH in endpoint else {}
            return {'content': base64.b64encode(json.dumps(content).encode()).decode()}
        with patch.dict(os.environ, {'GITHUB_REPOSITORY': 'owner/repo'}), patch('sys.argv', ['sync_scholar.py']), \
                patch.object(sync, 'api', side_effect=api), patch.object(sync, 'fetch_profile', side_effect=ValueError('blocked')):
            with self.assertRaises(ValueError):
                sync.main()


if __name__ == '__main__':
    unittest.main()
