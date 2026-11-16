# AI PPT 生成器

基于 **FastAPI + LangChain + ARQ + React** 的 AI PPT 生成器：输入主题或长文本，生成可编辑大纲，并发生成完整页面，最终导出**原生可编辑的 PPTX** 文件。

> 自研实战项目，从零实现，核心目标是完整实践 AI 工程化、异步任务编排、文档双端同源渲染的工程链路。

## 功能特性（MVP）

- **多输入生成大纲**：主题 / 长文本粘贴，通过 LangChain 结构化输出生成可修改的大纲（增删页面、调整要点）
- **异步并发生成**：页级任务拆分，ARQ Worker 并发执行，SSE 实时推送进度，失败单页重试
- **在线编辑**：React 19 编辑器，内容/布局/主题三分离数据模型
- **原生 PPTX 导出**：python-pptx 逐块构造原生文本框等对象（非截图渲染），导出前质量分级检查（error 阻断 / warning 放行），导出后回读验证

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI · SQLAlchemy 2 (async) · Alembic · PostgreSQL 16 · Pydantic v2 |
| AI | langchain-core · langchain-openai（OpenAI 兼容/DeepSeek）· langgraph |
| 异步 | ARQ · Redis 7（队列 / pub-sub / 状态）· SSE |
| 导出 | python-pptx |
| 前端 | Vite · React 19 · TypeScript · TanStack Query · Zustand · Tailwind CSS 4 |
| 工程化 | uv · Docker Compose · pytest · ruff |

## 快速开始

### 环境要求

- Python 3.12+ / [uv](https://docs.astral.sh/uv/) / Node.js 20+ / Docker

### 步骤

```bash
# 1. 克隆并安装依赖
git clone <repo-url>
cd ai-ppt-generator
make install            # 或: cd backend && uv sync

# 2. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend\.env，填入 LLM_API_KEY（OpenAI 兼容接口）

# 3. 启动 PostgreSQL + Redis
make up                 # 或: docker compose up -d

# 4. 数据库迁移（W2 起可用）
make migrate

# 5. 启动 API（三选一）
make dev-api
# 或前台: cd backend && uv run uvicorn app.main:app --reload --port 39800

# 6. 验证
curl http://127.0.0.1:39800/health
```

## 端口分配

| 服务 | 端口 |
|---|---|
| API | 39800 |
| PostgreSQL | 39432 |
| Redis | 39379 |
| 前端 | 39173（W3 起可用） |

## 目录结构

```
ai-ppt-generator/
├─ backend/           # FastAPI 后端（api / core / models / schemas / services / workers / llm）
├─ docs/              # 架构设计 · 学习计划 · 环境搭建指南
├─ frontend/          # React 前端（W3 创建）
├─ docker-compose.yml # PostgreSQL + Redis
└─ Makefile
```

## 文档

- [架构设计](docs/architecture.md)：分层架构、关键决策、内容模型
- [6 周学习计划](docs/learning-plan.md)：里程碑与进度追踪
- [环境搭建指南](docs/setup.md)：Linux 实际执行记录与踩坑笔记

## 开发进度

- [x] W1-D1 工程初始化（uv / docker-compose / FastAPI 骨架 / 冒烟测试）
- [ ] W1-D2~D3 数据层（SQLAlchemy async + Alembic）
- [ ] W1-D4 JWT 鉴权
- [ ] W1-D5 统一内容模型
- [ ] W1-D6 LangChain 结构化输出
- [ ] W2 异步生成链路（ARQ + SSE）
- [ ] W3 前端
- [ ] W4 双端渲染 + PPTX 导出
- [ ] W5 编辑器 + 主题
- [ ] W6 部署 + 求职产出

## License

MIT
