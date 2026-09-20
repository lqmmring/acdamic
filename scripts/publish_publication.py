"""Publish a trusted GitHub issue to Markdown using only the Python standard library."""

import base64
import html
import json
import os
import re
import time
from datetime import date
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen
from content_modules import MODULES, module_from_title, parse_module, update_module


FIELDS = ('论文标题', '作者', '年份', '期刊或会议', '卷期页码或发表状态', '论文链接', '代码链接')
HEADING = '#### 发表期刊论文列表（List of Journal Publications）'
NEWS_FIELDS = ('新闻日期', '中文内容', '英文内容', '相关链接')


def parse_body(body, news=False):
    fields = NEWS_FIELDS if news else FIELDS
    parts = re.split(r'^### (.+)\s*$', body.replace('\r\n', '\n'), flags=re.M)
    values = {}
    for label, value in zip(parts[1::2], parts[2::2]):
        label, value = label.strip(), value.strip()
        if label not in fields or label in values:
            raise ValueError('未知或重复字段：' + label)
        values[label] = '' if value == '_No response_' else value
    for label in fields[:2] if news else fields[:4]:
        if not values.get(label):
            raise ValueError('缺少必填字段：' + label)
    for label, value in values.items():
        if '\n' in value or len(value) > 3000:
            raise ValueError('字段必须为单行且不超过 3000 字符：' + label)
    if news:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', values['新闻日期']):
            raise ValueError('新闻日期须为 YYYY-MM-DD')
        date.fromisoformat(values['新闻日期'])
    elif not re.fullmatch(r'(19|20|21)\d{2}', values['年份']):
        raise ValueError('年份必须为 1900–2199 的四位数字')
    for label in fields[-1:] if news else fields[-2:]:
        value = values.get(label, '')
        if value:
            url = urlsplit(value)
            if url.scheme != 'https' or not url.hostname or url.username or any(c.isspace() for c in value):
                raise ValueError('链接必须为完整的 HTTPS 地址：' + label)
    return values


def escape(value):
    return re.sub(r'([\\`*_{}\[\]()#!|])', r'\\\1', html.escape(value, quote=False))


def citation(values):
    authors = escape(values['作者'])
    for name in ('Liu, Q.', '刘翘铭'):
        authors = authors.replace(name, '**' + name + '**')
    text = f"{authors} ({values['年份']}). {escape(values['论文标题'])}. {escape(values['期刊或会议'])}."
    if values.get(FIELDS[4]):
        text += ' ' + escape(values[FIELDS[4]])
    for field, label in ((FIELDS[5], 'Paper'), (FIELDS[6], 'Code')):
        if values.get(field):
            url = quote(values[field], safe=':/?=&%#+@~;,!$*-._')
            text += f' [{label}]({url})'
    return text


def update_markdown(original, number, values):
    # A manually curated version takes precedence over a Scholar-imported row.
    if '<!-- scholar-publications:start -->' in original:
        from sync_scholar import prefer_manual_entry
        original = prefer_manual_entry(original, values['论文标题'])
    if original.count(HEADING) != 1:
        raise ValueError('论文列表标题缺失或重复，请检查 publications.md')
    prefix, entries = original.split(HEADING, 1)
    start = f'<!-- publication-issue:{number} -->'
    end = f'<!-- /publication-issue:{number} -->'
    entry = start + '\n1. ' + citation(values) + '\n' + end
    pattern = re.escape(start) + r'.*?' + re.escape(end)
    if start in entries:
        if entries.count(start) != 1 or entries.count(end) != 1:
            raise ValueError('论文标记损坏')
        entries = re.sub(pattern, lambda _: entry, entries, flags=re.S)
    else:
        entries = '\n' + entry + '\n\n' + entries.lstrip('\n')
    count = 0

    def renumber(match):
        nonlocal count
        count += 1
        return str(count) + '. '

    entries = re.sub(r'^\d+\. ', renumber, entries, flags=re.M)
    return prefix + HEADING + entries


def update_news(original, number, values):
    start, end = '<!-- managed-news:start -->', '<!-- managed-news:end -->'
    if original.count(start) != 1 or original.count(end) != 1:
        raise ValueError('新闻区标记缺失或重复')
    before, rest = original.split(start)
    managed, after = rest.split(end)
    pattern = r'<!-- news-issue:(\d+) date:(\d{4}-\d{2}-\d{2}) -->\n(.*?)\n<!-- /news-issue:\1 -->'
    entries = {int(n): (d, content) for n, d, content in re.findall(pattern, managed, flags=re.S)}
    leftover = re.sub(pattern, '', managed, flags=re.S).strip()
    if leftover:
        raise ValueError('新闻区包含无法识别的内容，停止更新以防覆盖')
    content = '- **' + values['新闻日期'] + '** — ' + escape(values['中文内容'])
    if values.get('相关链接'):
        content += ' [详情](' + quote(values['相关链接'], safe=':/?=&%#+@~;,!$*-._') + ')'
    if values.get('英文内容'):
        content += '\n  <br>' + escape(values['英文内容'])
    entries[number] = (values['新闻日期'], content)
    blocks = [f'<!-- news-issue:{n} date:{d} -->\n{content}\n<!-- /news-issue:{n} -->'
              for n, (d, content) in sorted(entries.items(), key=lambda item: (item[1][0], item[0]), reverse=True)]
    return before + start + '\n' + '\n\n'.join(blocks) + '\n' + end + after


def api(method, endpoint, data=None):
    request = Request('https://api.github.com' + endpoint,
                      data=json.dumps(data).encode() if data is not None else None,
                      headers={'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
                               'Accept': 'application/vnd.github+json',
                               'X-GitHub-Api-Version': '2022-11-28',
                               'User-Agent': 'academic-homepage-publisher'}, method=method)
    with urlopen(request, timeout=60) as response:
        body = response.read()
        return json.loads(body) if body else {}


def main():
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text(encoding='utf-8'))
    repo = '/repos/' + os.environ['GITHUB_REPOSITORY']
    number = int(event['issue']['number'])
    # Fetch current content, so queued edits never publish an outdated event body.
    issue = api('GET', f'{repo}/issues/{number}')
    module = module_from_title(issue['title'])
    news = issue['title'].startswith('[新闻]')
    if not module and not news and not issue['title'].startswith('[论文]'):
        print('非内容表单，跳过。')
        return
    for login in {issue['user']['login'], event['sender']['login']}:
        permission = api('GET', repo + '/collaborators/' + quote(login, safe='') + '/permission')
        if permission['permission'] not in ('admin', 'write', 'maintain'):
            raise ValueError('仅有仓库写权限的提交者和编辑者可发布')
    values = parse_module(issue['body'] or '', module) if module else parse_body(issue['body'] or '', news=news)
    pages = api('GET', repo + '/pages')
    if pages['build_type'] != 'legacy' or pages['source']['path'] != '/':
        raise ValueError('此流程要求 Pages 从分支根目录发布；请参阅 README')
    branch = pages['source']['branch']
    filename = MODULES[module][0] if module else ('news.md' if news else 'publications.md')
    endpoint = repo + '/contents/contents/' + filename
    for attempt in range(5):
        current = api('GET', endpoint + '?ref=' + quote(branch, safe=''))
        original = base64.b64decode(current['content']).decode('utf-8')
        updated = update_module(original, module, values) if module else (update_news if news else update_markdown)(original, number, values)
        if original == updated:
            print('内容已同步；重新请求发布。')
            break
        try:
            result = api('PUT', endpoint, {
                'message': f'Update homepage content from issue #{number}',
                'content': base64.b64encode(updated.encode('utf-8')).decode(),
                'sha': current['sha'], 'branch': branch})
            print('已提交：' + result['commit']['sha'])
            break
        except HTTPError as error:
            if error.code != 409 or attempt == 4:
                raise
            time.sleep(2)
    # GITHUB_TOKEN commits do not trigger branch-based Pages automatically.
    api('POST', repo + '/pages/builds', {})
    print('已请求 GitHub Pages 构建。')
    with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as summary:
        summary.write(f'Issue #{number} 已同步。已请求 Pages 构建，请在仓库 Actions 中确认部署结果。\n')


if __name__ == '__main__':
    main()
