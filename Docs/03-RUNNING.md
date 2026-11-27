# 运行与验证 · v2

## 环境

- Python 3.11 / 3.12、Node.js 24 LTS、PostgreSQL 17+。
- 在仓库根目录运行 Python 命令。依赖：`requirements.txt`（运行）、`requirements-dev.txt`（测试）、`requirements-rag.txt`（可选知识库）。
- `.env.example` 复制成 `.env`：必填 `DEEPSEEK_API_KEY`，模型默认 `deepseek-flash`；配置 `POSTGRES_*`，并先创建 `huibi` 数据库。
- 表及兼容旧表的 `essay_text` 等字段自动创建；保留 v1 历史记录，旧记录没有作文原文时不显示原文折叠区。迁移前建议自行备份真实数据库。

## 启动

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
# 编辑 .env
cd frontend && npm ci && npm run build && cd ..
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Windows 激活环境用 `.venv\Scripts\activate`；构建完成后也可运行根目录批处理，或 `scripts/start_app.ps1`。macOS / Linux 可运行 `scripts/start_app.sh`。可使用项目私有 PostgreSQL（仅监听 127.0.0.1，数据在被忽略的 `data/postgres/`，运行文件在 `.runtime/postgres/`）。这些组件不随 Git 发布；macOS/Linux 启动脚本仅在本机已初始化此集群时复用或启动，否则需自行安装并启动 PostgreSQL。不会自动下载 embedding 模型。

- 页面：http://127.0.0.1:8000
- API 文档：http://127.0.0.1:8000/api/docs
- 健康检查：`curl http://127.0.0.1:8000/api/health`（不探测数据库或付费模型）

开发模式开两个终端：

```bash
# 根目录；先激活 .venv
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
# 另一个终端
cd frontend && npm run dev
```

浏览器访问 http://127.0.0.1:5173，Vite 将 `/api` 代理到 8000。`.env` 的 `FRONTEND_ORIGIN` 需改为 `http://127.0.0.1:5173`（若访问 localhost，则保持模板的 localhost）。不设置 `VITE_DEEPSEEK_API_KEY`，不把密钥打包进前端。

## 数据与会话

- 用户/批改/会话存 PostgreSQL；会话 token 在数据库中仅保存 SHA-256 摘要，7 天过期，退出时撤销。
- 图片保存在 `data/uploads/`，只通过校验所属用户的 API 访问，不作为公开静态目录挂载。删除记录时删除关联图片。
- 图片限制 5 MB、2000 万像素，按真实内容校验 PNG / JPEG / WebP，不能只改扩展名。只允许 IELTS Task 1 上传。
- 同一账号同一进程同时只允许一个模型任务。页面切换标签不打断批改；离开整个工作台前提示，已开始的服务端任务可能继续完成并保存。当前不提供取消付费上游请求的保证。
- 生产构建由 FastAPI 同源托管，无跨域认证配置。对外部署须开启 HTTPS 并设置 `COOKIE_SECURE=true`。当前只按本机单进程设计，不应直接加多 worker 后宣称具备分布式任务互斥。

## 可选 RAG

不构建向量库也可运行批改，公开评分量表仍直接注入 prompt；知识库缺失会明确标注，不能宣称完成检索。

```bash
pip install -r requirements-rag.txt
# 首次需预下载 BAAI/bge-small-en-v1.5 到 Hugging Face 本地缓存；构建和运行均只读缓存
hf download BAAI/bge-small-en-v1.5
python -m src.rag.build_kb
```

## 测试

```bash
pytest -v
ruff check src/api src/agents/llm.py tests/test_api.py tests/test_multimodal.py tests/test_postgres.py
# PostgreSQL 集成测试使用随机 schema，finally/fixture 清理，不 TRUNCATE 现有数据
TEST_DATABASE_DSN=postgresql://postgres:password@localhost:5432/huibi_test pytest -v
cd frontend
npm test
npm run build
npx playwright install chromium
npm run test:e2e
```

Windows PowerShell 设置变量：`$env:TEST_DATABASE_DSN="postgresql://..."`。Playwright 默认用 `python` 启动 FastAPI；未激活环境时可通过 `PYTHON` 指定解释器绝对路径。测试会自动打开 8000 端口，截图/报告位于 `frontend/test-results/`、`frontend/playwright-report/`，均不提交。

GitHub Actions：Python 3.11 / 3.12 + PostgreSQL 17 服务；Node 24 + Vitest + 类型构建 + Chromium 桌面/手机 E2E。真实模型调用必须单独手动验证，CI 不配置、不使用模型密钥。

## 旧版代码

按用户要求，本地不额外保留 v1 快照，旧 Streamlit 页面、主题和部署脚本已清理。原始 Git 历史不改写。当前只使用 FastAPI + Vue 3 入口。

## 本机真实验收

密钥只放 `.env`；若曾误填到 `.env.example`，先移至 `.env` 并恢复示例占位值。本机已经完成这一步，密码与数据库文件均不进入 Git。

```bash
./scripts/start_app.sh                # 本机可直接启动；页面 http://127.0.0.1:8000
# 手动付费验收，临时账户及其记录会自动清理；仅使用合成英文作文和 JPEG 表格图片
.venv/bin/python -m scripts.live_smoke_test --run-live
```

验收脚本的本地 HTTP 连接禁用系统代理，避免将 localhost 请求错误转发到外部代理。外部模型连接仍沿用应用正常网络配置。摘要输出在被忽略的 `reports/live-smoke-summary.json`。
