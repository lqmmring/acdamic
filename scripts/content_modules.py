"""Explicitly scoped updates for the remaining homepage text modules."""

import html
import json
import re


# label: (file, [(form field, managed block)])
MODULES = {
    '个人简介': ('home.md', [('中文简介', 'bio-zh'), ('英文简介', 'bio-en')]),
    '研究方向': ('home.md', [('中文研究方向', 'interests-zh'), ('英文研究方向', 'interests-en')]),
    '学术兼职': ('home.md', [('中文学术兼职', 'services-zh'), ('英文学术兼职', 'services-en')]),
    '招生说明': ('home.md', [('中文招生说明', 'admissions-zh'), ('英文招生说明', 'admissions-en')]),
    '联系方式': ('home.md', [('中文联系方式', 'contact-zh'), ('英文联系方式', 'contact-en')]),
    '教育经历': ('experience.md', [('中文教育与工作经历', 'experience-zh'), ('英文教育与工作经历', 'experience-en')]),
    '科研项目': ('publications.md', [('中文科研项目', 'projects-zh'), ('英文科研项目', 'projects-en')]),
    '站点信息': ('config.yml', [('网页标题', 'title'), ('导航姓名', 'page-top-title'),
                            ('横幅标语', 'top-section-bg-text'), ('主页姓名', 'home-subtitle'),
                            ('版权文字', 'copyright-text')]),
}
CLEAR = '【清空】'


def module_from_title(title):
    for name in MODULES:
        if title.startswith('[' + name + ']'):
            return name
    return None


def parse_module(body, name):
    allowed = dict(MODULES[name][1])
    # Fields use h3; nested Markdown headings must use h4 or deeper.
    parts = re.split(r'^### ([^\n]+)\n', body.replace('\r\n', '\n') + '\n', flags=re.M)
    values = {}
    for label, content in zip(parts[1::2], parts[2::2]):
        label, content = label.strip(), content.strip()
        if label not in allowed or label in values:
            raise ValueError('未知或重复字段：' + label)
        values[label] = content
    if set(values) != set(allowed):
        raise ValueError('请保留所有表单字段标题，包括留空字段')
    changed = {allowed[label]: ('' if value == CLEAR else value)
               for label, value in values.items() if value and value != '_No response_'}
    if not changed:
        raise ValueError('请至少填写一个字段；留空表示保留原内容')
    for content in changed.values():
        if len(content) > 20000:
            raise ValueError('单字段不得超过 20000 字符')
        if name == '站点信息':
            if '\n' in content or len(content) > 500:
                raise ValueError('站点信息必须为不超过 500 字符的单行纯文本')
        elif re.search(r'<!--|-->|^#{1,3}\s', content, re.M):
            raise ValueError('内容中不能包含 HTML 注释或一级至三级标题；小标题请使用 ####')
    return changed


def replace_block(original, block, content):
    start, end = f'<!-- module:{block}:start -->', f'<!-- module:{block}:end -->'
    if original.count(start) != 1 or original.count(end) != 1:
        raise ValueError('模块标记缺失或重复：' + block)
    before, remaining = original.split(start)
    old, after = remaining.split(end)
    return before + start + '\n' + content + '\n' + end + after


def update_module(original, name, values):
    result = original
    for block, content in values.items():
        if block not in dict(MODULES[name][1]).values():
            raise ValueError('不允许修改模块外的字段')
        if name == '站点信息':
            # JSON strings are valid YAML scalars. Config is injected as innerHTML.
            encoded = json.dumps(html.escape(content, quote=False), ensure_ascii=False)
            pattern = r'^' + re.escape(block) + r':[^\n]*$'
            if len(re.findall(pattern, result, flags=re.M)) != 1:
                raise ValueError('配置字段缺失或重复：' + block)
            result = re.sub(pattern, lambda _: block + ': ' + encoded, result, flags=re.M)
        else:
            result = replace_block(result, block, content)
    return result
