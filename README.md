#### 刘翘铭的个人主页

主页由静态 HTML、Markdown 和 YAML 组成，无需安装前端构建工具。

### 通过表单更新主页

打开 [新增内容表单](https://github.com/lqmmring/acdamic/issues/new/choose)，选择：

- **新增或更新论文**：填写标题、作者、年份、期刊或会议，可附论文和代码链接。新论文添加到列表顶部，原有科研项目和论文保留，列表自动重新编号。作者中的 `Liu, Q.` 和 `刘翘铭` 自动加粗。
- **发布或更新新闻**：填写 `YYYY-MM-DD` 日期、中文内容，可附英文内容和链接。新闻按日期倒序显示；没有新闻时，主页隐藏新闻区和 NEWS 导航。

点击 **Submit new issue** 后，查看 [Actions](https://github.com/lqmmring/acdamic/actions) 中的 **Publish homepage content**。流程校验内容和权限，提交更新并请求 Pages 构建；网页需等待 Pages 部署完成后才会更新。

修改同一个 Issue 的正文可更新原条目，重复运行不会重复添加。请保留 `[论文]` / `[新闻]` 标题前缀及表单字段标题，不要把同一个 Issue 改成另一种内容类型。关闭 Issue 不会删除内容。删除已发布条目需要编辑对应 Markdown 文件，移除该条目和前后的 Issue 标记。

仅仓库所有者及具有写权限的维护者提交、编辑的内容可自动发布。表单字段使用纯文本，HTML 和 Markdown 控制字符会转义；链接必须为 HTTPS。不需要配置个人访问令牌。

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
