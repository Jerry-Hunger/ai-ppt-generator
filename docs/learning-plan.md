# 6 周学习计划（从零自研版）

> 背景：Node.js 技术栈后端求职者，Python 会基本语法，每天投入约 1 小时，目标 6 周完成 MVP 并用于简历。
> 策略：MVP 纵切优先——先打通「输入→大纲→并发生成→编辑→导出 PPTX」最小闭环，再逐步加深。
> 不购买教程源码，基于公开总览信息自主设计实现，每个决策出自己之手。

## 总体里程碑

| 里程碑 | 时间 | 验收标准 |
|---|---|---|
| M1 | W1 末 | curl 调大纲 API 返回结构化大纲 JSON |
| M2 | W2 末 | 发起生成 → 页面逐页落库，curl SSE 可见进度流 |
| M3 | W3 末 | 浏览器全流程走通（登录→建项目→大纲→生成→进度） |
| M4 | W4 末 | 导出 PPTX 在 PowerPoint/WPS 中文字可编辑 |
| M5 | W5 末 | 编辑后导出、切主题双端一致 |
| M6 | W6 末 | 可部署访问 + 简历段落 + 面试问答材料齐 |

## 周计划（每天 ~1h，周日缓冲）

### W1 地基（后端骨架与 AI 首链路）
- D1 ✅ uv 初始化 + docker-compose（PG 39432 / Redis 39379）+ Makefile + ruff/pytest + FastAPI `/health` 骨架
- D2-3 SQLAlchemy 2 异步引擎 + AsyncSession + Base 声明基类；Alembic 初始化，第一版迁移（User 表）
- D4 JWT 注册/登录（pwdlib 哈希 + pyjwt 签发验证）
- D5 Deck/Page/Block Pydantic 内容模型（三分离 JSON 设计）
- D6 LangChain 接 LLM（OpenAI 兼容），试通 `with_structured_output` 生成大纲

### W2 异步链路（后端核心）
- D1-2 ARQ 集成 + 生成任务入队 API（POST /generate）
- D3-4 单页生成任务（Semaphore 并发限流 + 校验失败重试 1 次）
- D5 Redis pub/sub 进度事件 + SSE 端点
- D6 失败单页重试接口 + 软取消

### W3 前端最小可用
- D1 Vite + React 19 + TS + Tailwind 4 初始化、Router、Zustand、TanStack Query
- D2-3 登录页 + 项目列表 + 创建项目（openapi-typescript 生成接口类型）
- D4-5 大纲工作台（展示/编辑标题要点/增删页）
- D6 生成页 + SSE 进度展示（EventSource）

### W4 双端渲染（项目最大卖点）
- D1-2 Web 画布（cqw 单位等比缩放 + BlockView 分发 4 类块）
- D3-4 python-pptx 渲染器（同一 JSON → 原生文本框，中文字体微软雅黑）
- D5 质量检查简版（error/warning 分级）+ 导出后回读验证
- D6 前端导出按钮 + 下载

### W5 编辑器 + 主题
- D1-2 contenteditable 受约束编辑 + 自动保存 + 撤销重做（简化版）
- D3 两套主题 JSON（米白商务/深蓝科技），双端同源切换
- D4 表格块 + 图表块（Recharts + python-pptx）
- D5 图片占位块（可扩展 Unsplash）
- D6 长文本输入入口 + 收尾

### W6 部署 + 求职产出
- D1-2 Docker 全量编排（api/worker/web）+ 冒烟测试
- D3 README（架构图 + 设计决策记录 + 运行指南）
- D4 简历项目段落（STAR + 量化）
- D5 面试问答清单 15 题
- D6 选定扩展方向

## 每周学习重心（技术栈映射）

- W1：FastAPI / SQLAlchemy async / Pydantic v2 / 结构化输出 —— 对照 Express / Sequelize 学
- W2：ARQ、Redis pub/sub、SSE、asyncio 并发原语 —— 对照 BullMQ
- W3：React 19 + TanStack Query + 前后端类型单源
- W4：python-pptx / OOXML、同源渲染思想
- W5：contenteditable 受约束编辑、主题系统设计
- W6：Docker 编排、工程化收尾

## 面试可讲的 6 个关键决策

1. 为什么不让模型直接输出 HTML/PPTX → 统一内容模型，双端同源渲染
2. 为什么用异步队列 → 串行 1 分钟+ 拆为页级并发生成
3. 为什么 SSE 而非 WebSocket → 服务端单向推送，协议更简单
4. 大纲确认人工节点 → 避免方向错误浪费并发生成
5. LangGraph/自纠环 → 生成→检查→修复，上限一轮
6. 导出质量门禁 → warning/error 分级 + 回读验证证明可编辑

## 风险与应对

1. **每天仅 1h** → 任务按天拆，每周里程碑独立可交付，中断不报废整周
2. **LangGraph 曲线陡** → W2 朴素实现先跑通，后续重构为 LangGraph（简历上是「演进故事」亮点）
3. **python-pptx 图表能力有限** → 图表块受阻时降级为形状绘制，不阻塞主线
4. **Linux 环境** → make 原生可用；导出 PPTX 中文字体仍声明微软雅黑（由打开端渲染，本机预览缺字体记入踩坑笔记）
5. **无源码参考** → 每周产出可运行增量，随时可停；设计决策自行论证（对面试反而有利）

## 简历定位

与 Node.js 主项目形成「**双栈 + AI 工程化**」差异化组合。面试深挖点提前备好：
为什么不用 WebSocket、为什么统一内容模型、如何证明导出文件可编辑、ARQ 幂等与断点续跑怎么做。
