#### 刘翘铭的个人主页

主页由静态 HTML、Markdown 和 YAML 组成，无需安装前端构建工具。

### 通过表单更新主页

打开 [新增内容表单](https://github.com/lqmmring/acdamic/issues/new/choose)，选择：

- **新增或更新论文**：填写标题、作者、年份、期刊或会议，可附论文和代码链接。新论文添加到列表顶部，原有科研项目和论文保留，列表自动重新编号。作者中的 `Liu, Q.` 和 `刘翘铭` 自动加粗。
- **发布或更新新闻**：填写 `YYYY-MM-DD` 日期、中文内容，可附英文内容和链接。新闻按日期倒序显示；NEWS 导航和新闻区始终显示，没有新闻时显示“暂无新闻”。
- **更新个人简介、研究方向、学术兼职、招生说明、联系方式、教育经历、科研项目**：各有独立表单。只填写需要更新的语言版本，留空保留原文；填写的字段整体替换对应区域，列表请提交完整列表。输入 `【清空】` 可清除该字段内容。支持 Markdown 列表、链接和表格，小标题请用 `####` 或 `#####`，不要写 HTML 注释。
- **更新站点信息**：可分别修改网页标题、导航姓名、横幅标语、主页姓名、版权文字。填写单行纯文本；留空保留原值，`【清空】` 清除字段。

模块表单不自动预填当前内容。修改完整列表前，可通过表单中的“当前内容”链接复制最新内容再调整；删除列表中的一项即从完整列表中移除该项后提交。请至少填写一个字段。同一模块后提交的内容会替换先前内容，不要重跑旧 Issue 来覆盖较新的版本。图片仍通过原来的资源文件维护。

详细操作及各表单链接见 [readme.txt](readme.txt)。

### Google Scholar 定期同步

在保留 Issue 手工录入的同时，`Sync Google Scholar` 工作流会同步 [Qiaoming LIU 的 Scholar 主页](https://scholar.google.com/citations?user=qksAJxwAAAAJ)。每天北京时间约 10:17 检查距上次成功同步是否满 15 天，未满则不请求 Scholar；满 15 天后读取公开论文列表。GitHub 调度可能延迟，实际间隔可能略长于 15 天。

- 按标准化标题去重，补充尚未展示的记录；自动区按年份倒序。列表含 Scholar 收录的期刊、会议及预印本，类型以刊物信息为准。
- 手工论文的作者、通讯标记、链接和正文保留，附加 Scholar 收录信息和引用次数。自动导入条目的年份、刊物和引用次数随同步更新。
- Scholar 列表可能截断作者或刊物信息，不推测缺失内容；可通过论文表单提交完整版本接管自动条目。
- 读取失败、验证码、空列表、分页不完整时不写入；后续定时检查会重试。暂时从 Scholar 消失的记录不会自动删除。
- 配置在 `contents/scholar-config.json`：`excluded_ids` 可排除不希望展示的 Scholar 记录，`title_aliases` 用于标题差异的去重。同步记录及上次成功时间在 `contents/scholar-state.json`（首次成功后生成）。不要在自动区直接编辑论文，否则下次同步会重新生成。
- 可在 Actions → **Sync Google Scholar** → **Run workflow** 勾选 `force` 立即同步；不要频繁运行。若同步提交成功但 Pages 请求失败，可重跑并强制同步以重新发布。

Google Scholar 访问可能受到限流，不能保证每次抓取成功。失败记录会出现在 Actions，不会清空主页。GitHub 公共仓库长时间没有活动时可能自动停用定时任务，可在 Actions 中重新启用。无需配置第三方付费 API。

参考：[GitHub 定时任务说明](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)、[Google Scholar 访问说明](https://scholar.google.com/intl/en/scholar/help.html)。

点击 **Submit new issue** 后，查看 [Actions](https://github.com/lqmmring/acdamic/actions) 中的 **Publish homepage content**。流程校验内容和权限，提交更新并请求 Pages 构建；网页需等待 Pages 部署完成后才会更新。

修改同一个 Issue 的正文可更新原内容，重复运行不会重复添加。请保留对应模块的标题前缀及表单字段标题，不要把同一个 Issue 改成另一种内容类型。关闭 Issue 不会删除内容。论文和新闻的删除仍需编辑对应 Markdown 文件，移除该条目和前后的 Issue 标记。

仅仓库所有者及具有写权限的维护者提交、编辑的内容可自动发布。论文和新闻字段使用纯文本，HTML 和 Markdown 控制字符会转义，链接必须为 HTTPS；其他文字模块允许维护者填写 Markdown，站点信息按纯文本处理。不需要配置个人访问令牌。

### 仓库设置

1. 在 **Settings → General → Features** 开启 Issues。
2. 允许 GitHub Actions 运行；工作流必须存在于默认分支（当前为 `pesonal`）。
3. **Settings → Pages** 使用 **Deploy from a branch**，目录选择 **/(root)**。脚本读取实际 Pages 来源分支并更新该分支；该分支需要包含本项目的页面、`contents/publications.md` 和 `contents/news.md`。
4. 仓库规则须允许 `github-actions[bot]` 更新发布分支；如果规则要求所有变更经过 PR，自动提交会失败，需要另行改为 PR 流程。

工作流显式请求 Pages 构建，因为使用 `GITHUB_TOKEN` 写入文件不会自动触发分支式 Pages 发布。失败可在 Actions 日志中查看原因，修正表单后编辑保存或重跑失败任务。

### 本地验证

```sh
python -m unittest discover -s scripts -p "test_*.py" -v
python -m http.server 8000
```

浏览器访问 `http://localhost:8000`。内容通过 fetch 加载，请勿直接双击 HTML 使用 `file://` 打开。
