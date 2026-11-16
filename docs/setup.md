# 本地环境搭建指南（Linux 实际执行版）

> 记录本项目在 Linux 上的真实搭建过程与踩坑，供复查与新机迁移。

## 工具链要求（本机实际版本）

| 工具 | 要求 | 本机 |
|---|---|---|
| Python | 3.12+ | 3.13.3 |
| uv | 0.6+ | 0.11.3 |
| Node.js | 20+ | 24.14.0 |
| Docker Engine | 任意 | 29.7.2 |
| Git | 任意 | 2.49.0 |

## 端口分配（统一 39xxx 段，避开常用默认端口）

| 服务 | 端口 |
|---|---|
| API（FastAPI） | 39800 |
| PostgreSQL 16 | 39432 |
| Redis 7 | 39379 |
| 前端（W3 搭建后） | 39173 |

## 搭建步骤

### 1. 初始化工程（已完成）

```bash
git init -b main
uv init --bare backend          # 最小 pyproject，依赖用 uv add 增量管理
uv add fastapi "uvicorn[standard]" "sqlalchemy[asyncio]" asyncpg alembic \
    pydantic-settings redis arq langchain-core langchain-openai langgraph \
    python-pptx httpx "pwdlib[bcrypt]" pyjwt
uv add --dev pytest pytest-asyncio ruff
```

### 2. 配置密钥

```bash
cp backend/.env.example backend/.env
```

- 必填：`LLM_API_KEY`（OpenAI 兼容接口，默认 DeepSeek，可改 `LLM_BASE_URL`/`LLM_MODEL`）
- 密钥只写本地 `.env`，**禁止提交 Git**（.gitignore 已排除）

### 3. 启动基础设施

```bash
docker compose up -d      # PostgreSQL + Redis（带 healthcheck）
docker compose ps         # 确认 healthy
```

> ⚠️ 重启机器后容器不会自启，需重新执行 `docker compose up -d`（或 `make up`）。

### 4. 启动 API

**前台启动（推荐，Ctrl+C 干净停止）**：

```bash
cd backend
uv run uvicorn app.main:app --reload --port 39800
```

**后台启动（nohup）**：

```bash
cd backend
nohup uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 39800 > uvicorn.log 2>&1 &
```

**Makefile 方式**：项目根目录执行 `make dev-api`

### 5. 验证

```bash
curl http://127.0.0.1:39800/health
# {"status":"ok","app":"AI PPT Generator","debug":false}

cd backend
uv run pytest        # 冒烟测试
uv run ruff check .  # 静态检查
```

### 6. 停止服务

```bash
# 前台运行直接 Ctrl+C；后台运行按命令行匹配停止
pkill -f "uvicorn app.main:app"
```

## Makefile 命令总览

| 命令 | 作用 |
|---|---|
| `make up` / `make down` | 启停 PG + Redis 容器 |
| `make install` | uv sync 安装依赖 |
| `make migrate` | Alembic 迁移（W1-D3 起生效，需先 `make up`） |
| `make dev-api` / `make dev-worker` / `make dev-web` | 分别启动 API / Worker / 前端 |
| `make test` / `make lint` / `make fmt` | 测试 / 检查 / 格式化 |

## 踩坑笔记

1. **Docker Hub 直连被阻断（EOF）**
   - 现象：`docker pull` 报 `Get "https://registry-1.docker.io/v2/": EOF`
   - 解决：从 DaoCloud 镜像站手动拉取并重打标签：
     ```bash
     docker pull docker.m.daocloud.io/library/postgres:16-alpine
     docker pull docker.m.daocloud.io/library/redis:7-alpine
     docker tag docker.m.daocloud.io/library/postgres:16-alpine postgres:16-alpine
     docker tag docker.m.daocloud.io/library/redis:7-alpine redis:7-alpine
     ```
   - 根治：在 `/etc/docker/daemon.json` 配置
     `"registry-mirrors": ["https://docker.m.daocloud.io"]`，然后 `sudo systemctl restart docker`

2. **uvicorn --reload 后台进程残留**
   - 现象：后台启动后若只杀父进程，子进程仍持有端口
   - 原因：`--reload` 父进程持有端口、multiprocessing spawn 子进程实际服务
   - 解决：按命令行匹配停止整个进程（见上文「停止服务」）

3. **pytest-asyncio 弃用警告**
   - 需在 pyproject 显式设置 `asyncio_default_fixture_loop_scope = "function"`

4. **WSL 发行版 Docker 集成偶发失效（docker: command not found）**
   - 现象：WSL 内 `docker` 找不到命令，但 Docker Desktop 引擎在 Windows 侧正常运行
   - 解决：直接用 Windows 侧 CLI 兜底（compose 项目只用命名卷，无绑定挂载，路径无关）：
     ```bash
     "/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe" compose up -d
     ```
   - 根治：Docker Desktop → Settings → Resources → WSL Integration 重新勾选本发行区
