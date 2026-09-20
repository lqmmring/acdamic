学术主页更新使用说明
====================

一、入口与适用范围

主页：https://lqmmring.github.io/acdamic/
仓库：https://github.com/lqmmring/acdamic
选择提交表单：https://github.com/lqmmring/acdamic/issues/new/choose
已提交的内容：https://github.com/lqmmring/acdamic/issues
更新进度：https://github.com/lqmmring/acdamic/actions

所有在用文字模块均支持 GitHub Issue 表单：论文、新闻、个人简介、研究方向、
学术兼职、招生说明、联系方式、教育与工作经历、科研项目、站点信息。
图片资源仍按原方式上传和维护。
请使用仓库所有者账号或具有该仓库写权限的维护者账号登录 GitHub。
日常填写表单无需安装软件，也无需手动上传项目或配置个人访问令牌。

二、新增论文

1. 打开论文表单：
   https://github.com/lqmmring/acdamic/issues/new?template=publication.yml
2. 在 Issue 标题中保留“[论文]”前缀，后面填写便于查找的简称。
   例如：[论文] 新论文标题
3. 填写以下字段：
   必填：论文标题、作者、年份、期刊或会议。
   选填：卷期页码或发表状态、论文链接、代码链接。
4. 点击“Submit new issue”提交。
5. 等待自动更新和部署完成，再刷新主页查看 PUBLICATIONS。

填写规则：
年份使用四位数字，例如 2026。
作者按发表顺序填写，通讯作者可用 * 标记。
作者中的 Liu, Q. 和 刘翘铭 会自动加粗，无需自己添加加粗标记。
链接使用完整的 https:// 地址；DOI 请写成 https://doi.org/具体DOI。
所有字段使用单行纯文本，不超过 3000 字符，不填写 HTML 或 Markdown 排版代码。
没有内容的选填项直接留空。

显示规则：
新论文放在论文列表顶部，列表自动重新编号，不会按年份重新排序。
现有论文和科研项目保留。每篇新论文创建一个独立 Issue。

三、发布新闻

1. 打开新闻表单：
   https://github.com/lqmmring/acdamic/issues/new?template=news.yml
2. 保留 Issue 标题的“[新闻]”前缀，后面填写简短标题。
   例如：[新闻] 论文录用消息
3. 填写以下字段：
   新闻日期（必填）：使用 YYYY-MM-DD，例如 2026-09-19。
   中文内容（必填）：填写新闻正文。
   英文内容（选填）：填写后显示在中文内容下方。
   相关链接（选填）：填写完整的 https:// 地址。
4. 点击“Submit new issue”提交。
5. 等待部署完成后，在主页 NEWS 区查看。

示例（仅展示格式，请替换成真实信息）：
新闻日期：2026-09-19
中文内容：课题组一篇论文被某期刊接收。
英文内容：A paper from our group has been accepted by a journal.
相关链接：有正式链接时填写，否则留空。

新闻按日期从新到旧显示。日期相同时，Issue 编号较大的排在前面。
NEWS 导航和新闻区始终显示。没有新闻时显示“暂无新闻”，发布后自动显示新闻列表。
新闻各字段同样使用单行纯文本，每个字段不超过 3000 字符。

四、更新其他文字模块

选择表单总入口：https://github.com/lqmmring/acdamic/issues/new/choose

个人简介：https://github.com/lqmmring/acdamic/issues/new?template=biography.yml
研究方向：https://github.com/lqmmring/acdamic/issues/new?template=interests.yml
学术兼职：https://github.com/lqmmring/acdamic/issues/new?template=services.yml
招生说明：https://github.com/lqmmring/acdamic/issues/new?template=admissions.yml
联系方式：https://github.com/lqmmring/acdamic/issues/new?template=contact.yml
教育与工作经历：https://github.com/lqmmring/acdamic/issues/new?template=experience.yml
科研项目：https://github.com/lqmmring/acdamic/issues/new?template=projects.yml
站点信息：https://github.com/lqmmring/acdamic/issues/new?template=site.yml

操作步骤：
1. 选择对应模块表单，保留自动生成的标题前缀。
2. 只填写要修改的字段。中文与英文可独立更新，空白表示保留原内容。
3. 如需清空某个字段，单独填写【清空】（包含括号）。
4. 每个填写的字段会整体替换该区域，不是追加。列表必须填写完整列表。
5. 点击 Submit new issue，等待更新流程和 Pages 部署完成。

示例：研究方向的中文列表改为以下两项，可在“中文研究方向”填写：
- 单细胞数据分析
- 空间多组学分析
“英文研究方向”留空，则英文部分不变。

新增经历或项目：复制当前完整列表，加入新项后提交。
修改经历或项目：在完整列表中修改相应条目后提交。
删除经历或项目：从完整列表中去掉相应条目后提交。
表单不会自动填入当前内容；可通过表单中的“当前内容”链接查看、复制最新内容。
复制时只复制相应模块和语言的正文，不要复制 <!-- module:... --> 标记。
更新招生说明不会修改联系方式；科研项目更新不会修改论文列表。

这些模块支持 Markdown 排版，例如：
列表：每行以 - 开头。
链接：[显示文字](https://完整地址)
小标题：使用 #### 或 ##### 开头，不使用一级至三级标题。
招生表格示例：
| 要求 | 培养收获 |
| --- | --- |
| Python 基础 | 科研训练 |

模块内容每字段最多 20000 字符，禁止填写 HTML 注释，所有表单字段标题都要保留。
站点信息使用单行纯文本，每字段最多 500 字符；不要填写 Markdown 或 HTML 排版。
站点信息包括：网页标题、导航姓名、横幅标语、主页姓名、版权文字。
注意：版权年份需要填写希望展示的值，不会根据日期自动递增。

同一模块以最后成功处理的更新为准，不要重跑旧 Issue，以免覆盖较新的内容。
关闭 Issue 不会撤销更新。误改时可重新提交正确内容，或通过 Git 历史恢复。

五、修改已经通过表单发布的内容

1. 打开仓库 Issues，找到最初提交该论文或新闻的 Issue。
   如果已关闭，可切换到 Closed 列表查找。
2. 编辑该 Issue 的正文（首条内容），修改相应字段并保存。
   注意：追加评论不会触发内容更新。
3. 保留正文中的字段标题，例如“### 新闻日期”“### 中文内容”。
   保留 Issue 标题中的模块前缀，例如 [论文]、[新闻]、[招生说明]。
4. 等待自动流程和部署完成。

修改同一个 Issue 会替换原条目，不会重复新增。
修改新闻日期后，新闻会自动重新排序。
论文和新闻不要为修改已有条目另建 Issue，否则会生成新的条目。
其他模块也可新建表单更新，它们会替换对应区域，不会追加重复区域。
不要将同一个 Issue 从论文改为新闻，或从新闻改为论文。
原先手动录入的论文没有对应 Issue，修改时仍需编辑 publications.md。

六、检查是否更新成功

1. 打开：https://github.com/lqmmring/acdamic/actions
2. 找到本次提交对应的“Publish homepage content”运行记录。
3. 该流程成功后，还需要等待“pages build and deployment”完成。
   前一个流程负责更新文件并请求发布，后一个流程负责部署网页。
4. 部署成功后打开主页刷新；若仍显示旧内容，可按 Ctrl+F5 强制刷新。

提交后不是立即上线。具体等待时间取决于 GitHub 的任务排队和部署进度。

七、常见问题

1. 没有找到表单或无法提交
   确认已登录正确账号，并使用本文中的表单链接。
   仓库 Settings → General → Features 中需要开启 Issues。

2. 提交后没有运行记录
   确认标题保留对应表单的模块前缀。
   确认修改的是 Issue 正文，而不是发表评论。
   检查仓库 Actions 是否被禁用。

3. Actions 显示失败
   打开失败记录，查看“Validate, update and request Pages build”步骤日志。
   常见原因包括：必填项缺失、日期或年份格式错误、链接不是 HTTPS、
   字段标题被删除或重复、提交者或编辑者没有仓库写权限。
   修正 Issue 正文并保存会重新触发更新。
   若是临时网络或部署故障，可在失败运行页面使用 Re-run jobs 重试。

4. 工作流成功，但页面未更新
   检查后续 pages build and deployment 是否完成或失败。
   确认访问的是本文开头的主页地址，再尝试强制刷新。

5. 关闭 Issue 后，主页内容仍存在
   这是正常行为。关闭 Issue 不会删除论文或新闻。

八、删除内容和手动维护

论文和新闻的删除暂不提供表单操作，需要编辑内容文件。
其他模块可提交完整列表删除其中条目，或填写【清空】清空对应字段。
如需手动维护，可以编辑下列文件，但必须保留 module:... 的区域标记。
在 GitHub 仓库选择发布分支 pesonal，打开文件，点击编辑并提交更改：

contents/news.md：新闻。
contents/publications.md：论文及科研项目。
contents/home.md：个人简介、研究方向、学术兼职、招生说明、联系方式。
contents/experience.md：教育与工作经历。
contents/config.yml：网页标题、姓名、横幅标语、版权信息。

删除通过 Issue 发布的条目时，需要一起删除该条目前后的配对注释标记：
论文：<!-- publication-issue:编号 --> 至 <!-- /publication-issue:编号 -->。
新闻：<!-- news-issue:编号 date:日期 --> 至 <!-- /news-issue:编号 -->。
删除新闻时务必保留整个新闻区的 managed-news:start 和 managed-news:end 标记。
删除后不要再次编辑或重新打开原 Issue，否则它可能被重新发布。

如果在本地编辑，先同步 GitHub 上由表单生成的最新提交，处理好本地未提交修改，
再编辑、提交并推送，避免与自动更新产生冲突。

九、维护者配置说明

默认分支和 Pages 发布分支目前均为 pesonal（保留仓库原有拼写）。
Pages 使用 Settings → Pages → Deploy from a branch，目录为 /(root)。
工作流文件必须存在于默认分支。
仓库规则需允许 github-actions[bot] 更新发布分支。
自动流程会读取实际 Pages 来源分支，写入内容后显式请求 Pages 构建。
若更改发布方式或仓库权限，需要同步检查自动更新流程是否仍适用。

表单：.github/ISSUE_TEMPLATE/ 下各模块的 .yml 文件
工作流：.github/workflows/publish-publication.yml
更新脚本：scripts/publish_publication.py
模块定义与更新逻辑：scripts/content_modules.py

本地测试命令：
python -m unittest discover -s scripts -p "test_*.py" -v

本地预览命令（在项目根目录运行）：
python -m http.server 8000
然后访问 http://localhost:8000，不要直接双击 index.html 打开。
