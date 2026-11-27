# CLAUDE.md

任务开始前阅读本文件。进度见 `Docs/02-Progress.md`，待决策见 `Docs/TODO.md`，运行与测试见 `Docs/03-RUNNING.md`。更新文档要精炼。

## 当前版本（v2，2026-11-27）

用户明确要求：本地不再额外保留原始代码；改用 **DeepSeek Flash 多模态**、**Vue 3** 前端、**FastAPI** 后端；页面布局参考大疆官网，但**摄影以教育场景为主**；补充 GitHub 测试。

- 当前版本由 `main` 维护，开发源分支为 `v2/vue3-deepseek-flash`；按用户后续要求清理本地 v1 专用快照与 Streamlit 文件，Git 原有历史不改写。未经用户要求不要 commit / push / 发布标签。
- `app.py` 导出 FastAPI；`src/api/` HTTP 接口与 Pydantic 校验；`frontend/` Vue 3 + TypeScript + Vite。
- `src/agents/` 保留 LangGraph：校验 → 图片理解 → 检索 → 语法 → 反馈/评分 → critic（最多重写一次）→ coach → PostgreSQL。识图失败短路，不继续评分。
- 文本、评分、视觉统一 `deepseek-flash`，服务端 `DEEPSEEK_MODEL_NAME` 可配置；不再依赖 GLM。图片和评分仍为独立调用，复用同一模型供应商。
- PostgreSQL 用 psycopg v3，历史 JSON 用 JSONB。图片在 `data/uploads/`，数据库只存路径。不要换成 SQLite。
- 前端仅保留 Vue 3，旧 Streamlit 页面、主题、测试和部署脚本已移除。
- 只做本地运行，默认绑定 `127.0.0.1:8000`、单 worker；不要根据旧文档的地址操作服务器。

## 工作方式

- 需求滚动迭代；按合理判断处理常规歧义，并在汇报说明取舍。存在 advisor 等项目指定工具时，实质改动前和完成后使用；本机无该工具时不能伪造调用。
- 每轮在进度文档记录背景/改法/实际验证，重要待定项留 `Docs/TODO.md`。不要将未运行的验证称为成功。
- 不要堆砌多余 Agent 或无限循环。critic 最多重写一次，目前重写会连带再评分，这是已接受的成本取舍。
- 真实 key 只进 `.env`，不进 Markdown、前端、测试 fixture 或提交；不向浏览器返回上游异常或数据库连接信息。
- PBKDF2 密码哈希属于本地项目方案，不宣称生产级身份系统。Cookie 会话必须持久于数据库，题图和删除接口必须检查记录所有权。
- 所有分数是公开量表的 AI 模拟对照，不是官方成绩；AI 范文必须标注，不能伪装成真实考生作品。

## 测试与易错点

- Python 3.11+、Node 24 LTS。按 `Docs/03-RUNNING.md` 安装运行，不沿用 v1 的 Windows 专用 `.venv-uv` 路径。
- `pytest -v`；`TEST_DATABASE_DSN` 开启真实 PostgreSQL 集成测试。测试使用随机 schema，禁止清空真实用户数据。
- `cd frontend && npm ci && npm test && npm run build && npx playwright install chromium && npm run test:e2e`。
- CI 不使用真实模型 key、不消耗额度；HTTP/模型契约测试替换外部边界，不等于真实模型验证。
- UI 需要浏览器实测和截图，不能只看源码断言。移动端不允许横向溢出。
- DeepSeek 使用 OpenAI 兼容 `image_url` 内容块，data URL 必须匹配真实图片 MIME；JPEG 不能硬编码为 PNG。服务端校验文件内容、大小与像素数。
- 图片理解失败必须短路；`max_tokens=8192`，JSON/工具调用关闭 thinking。`bind_tools(..., strict=True)` 保留。
- `grammar_tools.py` 不依赖 LangChain；`nodes.py` 中数据库及重模型保持懒加载。
- 可选 RAG 依赖单独在 `requirements-rag.txt`；未构建库时明确说明，不伪造检索依据。Embedding 使用本地缓存 `BAAI/bge-small-en-v1.5`。
- 历史趋势按考试子任务和满分量表分组，不把 IELTS 9 分与 GENERAL 100 分直接混画。
