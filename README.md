# 慧笔 HuiBi · v2

英语写作智能批改与个性化学习工具。Vue 3 前端 + FastAPI 后端，保留 LangGraph 批改流程与 PostgreSQL 数据，统一使用 **`deepseek-flash` 原生多模态模型**。

## 能做什么

- 通用英语、IELTS Task 1 / Task 2、TOEFL 学术讨论 / 邮件写作。
- 公开量表模拟评分，内容、结构、词汇、语法反馈；质量复核最多重写一次。
- Task 1 上传 PNG / JPEG / WebP 题图；模型识图失败时停止后续评分，避免无依据评阅。
- 修改清单、针对性练习、AI 参考范文；历史反馈、同题型得分趋势、记录与题图删除。
- 注册登录、服务端持久会话、写作知识库问答。

> AI 模拟评阅不代表官方考试成绩；参考范文由 AI 生成。作文和题图会发送至配置的 DeepSeek API，请勿提交敏感信息。

## 版本

当前工作分支为 `v2/vue3-deepseek-flash`，尚未提交或推送。按用户要求不额外保留本地原版快照，旧 Streamlit 专用文件已清理；原始代码仍可通过仓库既有 Git 历史追溯。

## 快速启动

需要 Python 3.11+、Node.js 24 LTS、运行中的 PostgreSQL 17+。

```bash
python3 -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                  # Windows 可使用 Copy-Item
# 编辑 .env，填写 DEEPSEEK_API_KEY 和 PostgreSQL 连接参数
# 在 PostgreSQL 中创建 huibi 数据库：createdb -U postgres huibi

cd frontend
npm ci
npm run build
cd ..
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

访问 **http://127.0.0.1:8000**。API 文档：**http://127.0.0.1:8000/api/docs**。

无模型密钥或数据库时，首页与 `/api/health` 仍可访问；注册登录需要数据库，批改问答还需要模型密钥。不会用假结果冒充真实批改。

本机已配置私有 PostgreSQL，可直接运行 `./scripts/start_app.sh`（数据库和模型 key 均只保存在本机）。前后端开发、可选知识库构建及测试说明见 [运行文档](Docs/03-RUNNING.md)。

## 测试

```bash
pytest -v                             # 无 TEST_DATABASE_DSN 时跳过数据库集成用例
# 指向隔离的测试库，测试仅创建/销毁随机 schema，不清空原有数据
TEST_DATABASE_DSN=postgresql://postgres:password@localhost:5432/huibi_test pytest -v
cd frontend
npm test
npm run build
npx playwright install chromium
npm run test:e2e                       # 自动启动 FastAPI，桌面 + 手机 Chromium
```

GitHub Actions 在 push / pull request 时运行 Python 3.11 / 3.12 测试、真实 PostgreSQL 集成测试、Vue 单测、类型检查、构建、依赖审计及桌面/手机 E2E；**不需要真实模型密钥，不消耗模型额度**。浏览器中的模型与账号接口使用固定响应，数据库集成测试则使用真实 PostgreSQL。

## 目录

```text
app.py                    FastAPI 入口
src/api/                  HTTP 接口、会话、请求校验
src/agents/               LangGraph 节点与 DeepSeek Flash 封装
src/storage/              PostgreSQL 及本地题图存储
src/rag/                  可选向量知识库
frontend/src/             Vue 3 + TypeScript 页面与组件
frontend/public/images/   教育主题摄影及 CREDITS.txt
frontend/tests/           Vitest 组件与 API 客户端测试
frontend/e2e/             Playwright 浏览器测试
tests/                    Python 业务、HTTP、数据库与模型契约测试
.github/workflows/        GitHub Actions
```

## 设计与资料

借鉴 [DJI 官网](https://www.dji.com/) 的大幅摄影、简洁导航、分区留白，自行实现页面，不使用其商标或素材。教育主题摄影来自 Unsplash：

- 图书馆： [syahmi syahir](https://unsplash.com/photos/J2ydRt1TIMw)
- 书写： [Alexa Williams](https://unsplash.com/photos/sXZ8vvFrTCI)
- [Unsplash License](https://unsplash.com/license)，具体资源信息见 `frontend/public/images/CREDITS.txt`。

模型资料：[DeepSeek Flash 多模态公告](https://api-docs.deepseek.com/zh-cn/news/news260910/)、[Chat Completions 图片请求格式](https://api-docs.deepseek.com/zh-cn/api/create-chat-completion/)。

## 运行边界

默认仅供本机使用，绑定 `127.0.0.1`，单进程运行。API key 只在服务端 `.env` 中；浏览器使用 HttpOnly、SameSite Cookie；历史数据与题图检查所属用户。对外部署前仍需 HTTPS、登录限流、密码找回、备份与持久任务队列等，不将当前实现描述为生产级服务。

项目使用 GPL-3.0，见 [LICENSE](LICENSE)。
