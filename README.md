# AI Infra Arxiv Radar

复用 [monologg/nlp-arxiv-daily](https://github.com/monologg/nlp-arxiv-daily)，按十个主题跟踪端侧 AI、芯片、编译器、推理系统、算子优化与 AI 基础设施论文。

- 每两天抓取一次，每次回看三天，自动去重。
- 标题含 Survey / Review / Overview 的论文带“综述”标记并排在各主题前面。
- 自动补充论文中公开的代码地址。
- 关键词集中在 `config.yaml`，无需服务器或大模型 API。

## 首次启用

1. 在 Actions 页面启用工作流，并允许工作流读写仓库。
2. 在 Settings → Pages 中选择 GitHub Actions。
3. 把 `.github/workflows/nlp-arxiv-daily.yml` 的定时配置改为 `23 1 */2 * *`，然后手动运行一次。

公开地址：`https://ysh329.github.io/nlp-arxiv-daily/`。

注意：arXiv API 不提供作者单位，模型地址也没有统一字段，因此这两项不能保证每篇都有。
