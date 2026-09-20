"""Low-frequency Google Scholar profile sync; manual bibliography always wins."""

import argparse
import base64
import html
import json
import os
import re
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit
from urllib.request import Request, urlopen

from publish_publication import HEADING, api, escape

START = '<!-- scholar-publications:start -->'
END = '<!-- scholar-publications:end -->'
STATE_PATH = 'contents/scholar-state.json'
CONFIG_PATH = 'contents/scholar-config.json'
PUBLICATIONS_PATH = 'contents/publications.md'
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}


class Node:
    def __init__(self, tag='', attrs=None):
        self.tag, self.attrs, self.children = tag, dict(attrs or []), []

    def text(self):
        return ''.join(child if isinstance(child, str) else child.text() for child in self.children)

    def find(self, cls=None, id=None):
        found = []
        if ((cls and cls in self.attrs.get('class', '').split()) or
                (id and self.attrs.get('id') == id)):
            found.append(self)
        for child in self.children:
            if isinstance(child, Node):
                found.extend(child.find(cls, id))
        return found


class ProfileParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def clean(value):
    return ' '.join(value.split())


def parse_profile(source, profile_id):
    parser = ProfileParser()
    parser.feed(source)
    rows = parser.root.find(cls='gsc_a_tr')
    if not rows:
        raise ValueError('Scholar 未返回论文列表（可能遇到验证码、限流或页面结构变化）；保留现有内容。')
    records = []
    for row in rows:
        titles, gray = row.find(cls='gsc_a_at'), row.find(cls='gs_gray')
        if len(titles) != 1 or len(gray) < 2:
            raise ValueError('Scholar 论文行不完整，停止同步。')
        title = clean(titles[0].text())
        link = urljoin('https://scholar.google.com', titles[0].attrs.get('href', ''))
        query = parse_qs(urlsplit(link).query)
        identifier = query.get('citation_for_view', [''])[0]
        if not identifier.startswith(profile_id + ':') or not re.fullmatch(r'[A-Za-z0-9_-]+:[A-Za-z0-9_-]+', identifier):
            raise ValueError('Scholar 论文标识与配置的作者主页不一致。')
        if urlsplit(link).hostname != 'scholar.google.com' or not title:
            raise ValueError('Scholar 标题或链接无效。')
        years, citations = row.find(cls='gsc_a_y'), row.find(cls='gsc_a_ac')
        year = clean(years[0].text()) if years else ''
        if year and not re.fullmatch(r'(19|20|21)\d{2}', year):
            raise ValueError('Scholar 年份无法识别。')
        cited = clean(citations[0].text()).replace(',', '') if citations else ''
        if cited and not cited.isdigit():
            raise ValueError('Scholar 引用次数无法识别。')
        records.append({'id': identifier, 'title': title, 'authors': clean(gray[0].text()),
                        'venue': clean(gray[1].text()), 'year': year,
                        'citations': int(cited or 0),
                        'url': 'https://scholar.google.com/citations?' + urlencode({
                            'view_op': 'view_citation', 'user': profile_id, 'citation_for_view': identifier})})
    more = parser.root.find(id='gsc_bpf_more')
    # A full page without a pagination control is not safe to treat as complete.
    if not more and len(records) >= 100:
        raise ValueError('无法确认 Scholar 分页是否完整。')
    has_more = bool(more and 'disabled' not in more[0].attrs)
    return records, has_more


def fetch_profile(profile_id):
    all_records = []
    seen = set()
    for start in range(0, 1000, 100):
        url = 'https://scholar.google.com/citations?' + urlencode({
            'user': profile_id, 'hl': 'en', 'pagesize': 100, 'cstart': start, 'sortby': 'pubdate'})
        request = Request(url, headers={'User-Agent': 'AcademicHomepageSync/1.0', 'Accept': 'text/html'})
        # No captcha solving, login cookies, proxy rotation, or bypass attempts.
        with urlopen(request, timeout=45) as response:
            source = response.read().decode(response.headers.get_content_charset() or 'utf-8')
        records, has_more = parse_profile(source, profile_id)
        if len({record['id'] for record in records}) != len(records) or any(record['id'] in seen for record in records):
            raise ValueError('Scholar 分页重复，停止同步。')
        all_records.extend(records)
        seen.update(record['id'] for record in records)
        if not has_more:
            return all_records
        time.sleep(2)
    raise ValueError('Scholar 页数超过上限，未写入不完整结果。')


def normalized(value):
    value = html.unescape(value)
    return ''.join(c for c in unicodedata.normalize('NFKC', value).casefold() if c.isalnum())


def split_managed(original):
    if START not in original and END not in original:
        return original, ''
    if original.count(START) != 1 or original.count(END) != 1:
        raise ValueError('Scholar 自动区标记缺失或重复，停止同步。')
    before, rest = original.split(START)
    block, after = rest.split(END)
    return before + after, block


def remove_metadata(text):
    return re.sub(r' <!-- scholar-meta:[A-Za-z0-9_:-]+ -->.*?<!-- /scholar-meta -->', '', text)


def prefer_manual_entry(original, title):
    """Remove an automatic row immediately when an Issue supplies its manual version."""
    if START not in original:
        return original
    manual, block = split_managed(original)
    target = normalized(title)
    rows = [line for line in block.splitlines() if re.match(r'^\d+\. ', line)]
    kept = [line for line in rows if target not in normalized(line)]
    if len(kept) == len(rows):
        return original
    if not kept:
        return manual
    before, rest = original.split(START)
    _, after = rest.split(END)
    return before + START + '\n' + '\n\n'.join(kept) + '\n' + END + after


def render_record(record):
    authors = escape(record['authors'])
    for name in ('Q Liu', 'Qiaoming Liu', 'Qiaoming LIU', '刘翘铭', 'LIU Qiao-ming'):
        authors = re.sub(r'(?<!\w)' + re.escape(name) + r'(?!\w)', '**' + name + '**', authors)
    year = record['year'] or '年份待补充'
    return (f"1. {authors} ({year}). {escape(record['title'])}. {escape(record['venue'])}. "
            f"[Google Scholar]({record['url']}) · 引用次数：{record['citations']}")


def merge_records(original, fetched, previous, config):
    manual, _ = split_managed(original)
    manual = remove_metadata(manual)
    if manual.count(HEADING) != 1:
        raise ValueError('论文列表标题缺失或重复。')
    # Preserve known records absent from a later response; never infer deletion.
    records = {record['id']: record for record in previous.get('records', [])}
    records.update({record['id']: record for record in fetched})
    records = sorted(records.values(), key=lambda record: (record['year'] or '0', record['title']), reverse=True)
    bibliography = normalized(manual.split(HEADING, 1)[1])
    excluded = set(config.get('excluded_ids', []))
    aliases = config.get('title_aliases', {})
    rendered, matches, used_titles = [], [], set()
    for record in records:
        title = normalized(aliases.get(record['title'], record['title']))
        if record['id'] in excluded:
            continue
        if len(title) < 8:
            raise ValueError('标题过短，无法安全去重：' + record['title'])
        if title in bibliography or normalized(record['title']) in bibliography:
            matches.append(record['id'])
            continue
        if title in used_titles:
            continue
        used_titles.add(title)
        rendered.append(record)
    # Add source metadata without replacing manually curated authors, links or prose.
    def annotate(match):
        line = match.group(0)
        line_key = normalized(line)
        candidates = [record for record in records if record['id'] not in excluded
                      and (normalized(aliases.get(record['title'], record['title'])) in line_key
                           or normalized(record['title']) in line_key)]
        if not candidates:
            return line
        record = max(candidates, key=lambda r: (len(normalized(r['title'])), r['citations']))
        label = escape(record['venue'] or record['year'] or '待补充')
        return (line + f' <!-- scholar-meta:{record["id"]} -->'
                f' · [Scholar 收录：{label}；引用 {record["citations"]}]({record["url"]})'
                '<!-- /scholar-meta -->')
    prefix, body = manual.split(HEADING, 1)
    manual = prefix + HEADING + re.sub(r'^\d+\. [^\n]+', annotate, body, flags=re.M)
    prefix, body = manual.split(HEADING, 1)
    if rendered:
        block = START + '\n' + '\n\n'.join(render_record(r) for r in rendered) + '\n' + END + '\n\n'
        updated = prefix + HEADING + '\n' + block + body.lstrip('\n')
    else:
        updated = prefix + HEADING + '\n' + body.lstrip('\n')
    number = 0
    def renumber(match):
        nonlocal number
        number += 1
        return str(number) + '. '
    prefix, body = updated.split(HEADING, 1)
    updated = prefix + HEADING + re.sub(r'^\d+\. ', renumber, body, flags=re.M)
    return updated, records, rendered, matches


def is_due(state, now, interval):
    stamp = state.get('last_success_at')
    if not stamp:
        return True
    return now - datetime.fromisoformat(stamp) >= timedelta(days=interval)


def read_file(repo, path, ref, optional=False):
    try:
        result = api('GET', repo + '/contents/' + path + '?ref=' + ref)
    except HTTPError as error:
        if optional and error.code == 404:
            return None
        raise
    return base64.b64decode(result['content']).decode('utf-8')


def summary(text):
    print(text)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as handle:
            handle.write(text + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--preview-html', type=Path)
    parser.add_argument('--preview-dir', type=Path, default=Path('.local-maintenance'))
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    if args.preview_html:
        config = json.loads(Path(CONFIG_PATH).read_text(encoding='utf-8'))
        fetched, more = parse_profile(args.preview_html.read_text(encoding='utf-8'), config['profile_id'])
        if more:
            raise ValueError('预览文件仅包含部分论文，请获取完整分页。')
        original = Path(PUBLICATIONS_PATH).read_text(encoding='utf-8')
        updated, records, rendered, matches = merge_records(original, fetched, {}, config)
        args.preview_dir.mkdir(parents=True, exist_ok=True)
        (args.preview_dir / 'scholar-preview.md').write_text(updated, encoding='utf-8')
        (args.preview_dir / 'scholar-preview.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
        summary(f'Fetched {len(fetched)} records; matched {len(matches)} manual entries; automatic entries: {len(rendered)}.')
        for record in rendered:
            print(record['id'], record['title'])
        return
    repo = '/repos/' + os.environ['GITHUB_REPOSITORY']
    pages = api('GET', repo + '/pages')
    if pages['build_type'] != 'legacy' or pages['source']['path'] != '/':
        raise ValueError('此同步流程要求 Pages 从分支根目录发布。')
    branch = pages['source']['branch']
    ref_endpoint = repo + '/git/refs/heads/' + branch
    fetched = None
    for attempt in range(5):
        head = api('GET', repo + '/git/ref/heads/' + branch)['object']['sha']
        config = json.loads(read_file(repo, CONFIG_PATH, head))
        state = json.loads(read_file(repo, STATE_PATH, head, optional=True) or '{}')
        interval = config['interval_days']
        if not isinstance(interval, int) or interval < 15:
            raise ValueError('同步间隔不得短于 15 天。')
        if state.get('profile_id', config['profile_id']) != config['profile_id']:
            raise ValueError('Scholar 作者 ID 已变化，需人工确认并重新初始化同步状态。')
        if not args.force and not is_due(state, now, interval):
            summary('距离上次成功同步未满 15 天，本次未访问 Google Scholar。')
            return
        if fetched is None:
            fetched = fetch_profile(config['profile_id'])
        if not fetched:
            raise ValueError('空论文列表，保留原内容。')
        if any(not record['id'].startswith(config['profile_id'] + ':') for record in fetched):
            raise ValueError('配置在同步期间发生变化，停止发布。')
        original = read_file(repo, PUBLICATIONS_PATH, head)
        updated, records, rendered, matches = merge_records(original, fetched, state, config)
        new_state = {'profile_id': config['profile_id'], 'last_success_at': now.isoformat(),
                     'fetched_count': len(fetched), 'records': records}
        files = {STATE_PATH: json.dumps(new_state, ensure_ascii=False, indent=2) + '\n'}
        if updated != original:
            files[PUBLICATIONS_PATH] = updated
        tree = api('POST', repo + '/git/trees', {'base_tree': head, 'tree': [
            {'path': path, 'mode': '100644', 'type': 'blob', 'content': content} for path, content in files.items()]})
        commit = api('POST', repo + '/git/commits', {'message': 'Sync Google Scholar publications',
                                                   'tree': tree['sha'], 'parents': [head]})
        try:
            api('PATCH', ref_endpoint, {'sha': commit['sha'], 'force': False})
        except HTTPError as error:
            if error.code not in (409, 422) or attempt == 4:
                raise
            time.sleep(2)
            continue
        api('POST', repo + '/pages/builds', {})
        summary(f'读取 {len(fetched)} 条记录；其中 {len(matches)} 条记录匹配已有论文（可能包含合并版本）；自动展示 {len(rendered)} 条。'
                f'\n已提交 {commit["sha"]} 并请求 Pages 发布。手工条目未被覆盖。')
        return


if __name__ == '__main__':
    main()
