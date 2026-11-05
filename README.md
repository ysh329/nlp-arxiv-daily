# AI Infra Radar

基于 [monologg/nlp-arxiv-daily](https://github.com/monologg/nlp-arxiv-daily) 改造的 AI 系统论文雷达。

## 改造内容

- 十个主题：端侧 AI、处理器与 GPU、推理系统、AI 基础设施、编译器、模型压缩、HPC、算子优化、软硬件协同、基础算子。
- 每两天抓取一次，每次回看三天，避免时区与延迟公告造成遗漏。
- 标题包含 Survey / Review / Overview 的论文显示“综述”标记，并在主题内优先排列。
- 自动发现开源项目地址；论文摘要明确给出 Hugging Face 模型地址时显示 `model`，数据集地址不会误标为模型。
- 保留原项目的搜索、RSS、BibTeX、月度归档和 GitHub Pages 静态部署。
- 手机端使用紧凑导航和 44px 触控目标。

## 修改关键词

只改 `config.yaml` 中的 `keywords`。不需要服务器、数据库或大模型 API。

## 首次启用

1. 在 Actions 页面启用工作流，并在 Settings → Actions → General 中允许 Read and write permissions。
2. 在 Settings → Pages 中将 Source 设为 GitHub Actions。
3. 把 `.github/workflows/nlp-arxiv-daily.yml` 中的 cron 改为 `23 1 */2 * *`。
4. 手动运行一次 `Run Arxiv Papers Daily`。

固定地址：`https://ysh329.github.io/nlp-arxiv-daily/`。

## 数据限制

arXiv API 通常不提供作者单位，因此当前版本不自动生成机构信息。代码和模型地址只在公开接口或论文摘要明确给出时展示。
