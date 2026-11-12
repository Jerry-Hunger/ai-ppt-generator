# 架构设计

> 自研仿版「AI 智能 PPT 生成器」的架构蓝图。基于项目总览信息自主设计，每个决策出自本项目之手，面试可全链路自证。

## 核心设计思想

1. **前端不直接调用模型**：所有 LLM 调用由后端编排
2. **内容 / 布局 / 主题三分离**：三份独立 JSON 定义
3. **Web 与 PPTX 同源渲染**：两个渲染器读同一份内容数据，保证所见即所得

## 分层架构

```
┌─ 前端 React 19 + TS ──────────────────────────────┐
│  项目列表 / 大纲工作台 / 在线编辑器（缩略图+16:9画布+右侧面板）  │
│  TanStack Query · Zustand · Tailwind · Container Query 等比缩放│
└──────────┬── REST API ──┬── SSE（实时进度）────────┐
           ▼              ▼                          │
┌─ API 层 FastAPI ─────────────────────┐               │
│  JWT 鉴权 · 项目归属校验 · OpenAPI 类型单源        │               │
│  收到请求 → 状态落库 → 任务入队 → 立即返回        │               │
└──────┬───────────────┬───────────────┘               │
       ▼               ▼                               │
┌─ PostgreSQL ─┐  ┌─ Redis ──────────────────┐          │
│ 用户/项目/大纲 │  │ 任务队列 · pub/sub 事件    │          │
│ 页面/revision │  │ 状态快照 · 取消标记        │          │
└──────────────┘  └──────┬───────────────────┘          │
                         ▼                              │
┌─ ARQ Worker（异步任务编排）───────────────────────────┐ │
│  页级并发（asyncio.Semaphore 限流）                    │ │
│  ├─ 单页生成工作流：生成 → 结构检查 → 业务检查 → 修复轮次  │ │
│  ├─ 图片管线：AI 生图 → 图库检索 → 占位图降级            │ │
│  └─ 进度事件写 Redis → SSE 推给前端（断线可恢复）        │ │
└───────────────────────────────────────────────────┘ │
                         ▼                            │
┌─ 导出管线 ──────────────────────────────────────────┐
│  质量门禁：文字溢出 / 越界 / 来源数字 / 结构完整性        │
│  warning 提醒放行 · error 阻断导出                    │
│  python-pptx 逐块构造原生对象 → 回读验证（页数/画布/边界）│
└─────────────────────────────────────────────────────┘
```

## 六个关键架构决策（面试深挖点）

1. **为什么不让模型直接输出 HTML 或 PPTX**
   → 统一内容模型（Deck/Page/Block JSON）。直接输出 HTML 难以校验与二次编辑；直接输出 PPTX 无法在 Web 端同源渲染。统一模型让 Web 与 PPTX 双端读取同一份数据。

2. **为什么需要异步任务队列**
   → 10 页 PPT 串行调用模型要 1 分钟以上，HTTP 连接无法支撑。拆成页级任务由 ARQ 并发执行，API 立即返回，进度经 Redis pub/sub → SSE 推送。

3. **为什么用 SSE 而不是 WebSocket**
   → 生成进度是服务端单向推送场景，SSE 协议更简单、自动重连、无需双向通道。

4. **大纲确认作为人工节点**
   → 大纲决定整份 PPT 的叙事顺序。方向错了，并发生成越快浪费的模型调用越多。先让用户修改标题/目标/要点，确认后再生成。

5. **生成自纠环与修复轮次上限**
   → 生成 → 结构检查 → 业务检查 → 修复，最多一轮，避免死循环与成本失控。

6. **导出前质量门禁 + 导出后回读验证**
   → AI 输出文字长度不可预测，直接导出会溢出/缺页。导出前分级检查（warning 放行 / error 阻断），导出后回读文件验证页数、画布、边界、原生对象类型，证明「真的可编辑」。

## 内容模型（MVP）

```
Deck (项目)
 └─ Page[] (页面，有序)
     └─ Block[] (内容块)
         ├─ type: text | list | kpi | card   ← MVP 四类
         ├─ region: 归一化坐标 (0-1, 相对画布)
         └─ data: 各类型私有数据
```

- **三分离**：Deck JSON（内容）+ 固定布局坐标（归一化）+ 主题 JSON（颜色/字体）
- 扩展类型（表格 / 图表 / 提示）在 W5 加入

## MVP 范围与取舍

| 特性 | MVP 做法 | 后续扩展 |
|---|---|---|
| 输入 | 主题 + 长文本粘贴 | PDF/DOCX/MD 解析 |
| 工作流 | 朴素「生成→校验→修复1次」循环 | 重构为 LangGraph 自纠环 |
| 内容块 | 文本/列表/KPI/卡片 4 类 | 表格/图表/提示、新块类型 |
| 图片 | 主题占位块 | AI 生图→Unsplash→占位三级降级 |
| 排版 | 固定布局（归一化坐标） | 布局树 + solver 灵活排版 |
| 溢出检测 | 字符数估算 + error/warning 分级 | FontTools 字形级度量 |
| AI 编辑 | 无 | bind_tools 工具调用编辑 |

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI、Pydantic v2、SQLAlchemy 2（async）、Alembic、PostgreSQL 16 |
| AI | langchain-core + langchain-openai（OpenAI 兼容/DeepSeek）、langgraph |
| 异步 | ARQ、Redis（队列/pub-sub/状态/取消标记）、SSE |
| 文档 | python-pptx（原生对象导出） |
| 前端 | Vite + React 19 + TS、TanStack Query、Zustand、Tailwind CSS 4、Recharts |
| 工程化 | uv、Docker Compose、pytest、ruff、openapi-typescript（计划） |

## 目录结构

```
ai-ppt-generator/
├─ backend/
│  ├─ app/
│  │  ├─ api/        # FastAPI 路由
│  │  ├─ core/       # 配置、JWT
│  │  ├─ models/     # SQLAlchemy（User/Project/Deck/Page/Revision）
│  │  ├─ schemas/    # Pydantic（内容模型 + 接口契约）
│  │  ├─ services/   # outline / generation / web_render / pptx_render / quality
│  │  ├─ workers/    # ARQ worker + 单页任务
│  │  └─ llm/        # LLM Protocol 封装（可切换厂商）
│  ├─ tests/  ├─ alembic/  ├─ .env.example
├─ docs/             # 本文档目录
├─ frontend/         # Vite + React 19 + TS（W3 创建）
├─ docker-compose.yml  # PG(39432) + Redis(39379)
├─ Makefile
└─ README.md         # W6 编写
```
