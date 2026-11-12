# 本地环境搭建指南（Windows 实际执行版）

> 记录本项目在 Windows 上的真实搭建过程与踩坑，供复查与新机迁移。

## 工具链要求（本机实际版本）

| 工具 | 要求 | 本机 |
|---|---|---|
| Python | 3.12+ | 3.13.3 |
| uv | 0.6+ | 0.11.3 |
| Node.js | 20+ | 24.14.0 |
| Docker Desktop | 任意 | 29.7.2（需 WSL2） |
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

```powershell
git init -b main
uv init --bare backend          # 最小 pyproject，依赖用 uv add 增量管理
uv add fastapi "uvicorn[standard]" "sqlalchemy[asyncio]" asyncpg alembic `
    pydantic-settings redis arq langchain-core langchain-openai langgraph `
    python-pptx httpx "pwdlib[bcrypt]" pyjwt
uv add --dev pytest pytest-asyncio ruff
```

### 2. 配置密钥

```powershell
Copy-Item backend\.env.example backend\.env
```

- 必填：`LLM_API_KEY`（OpenAI 兼容接口，默认 DeepSeek，可改 `LLM_BASE_URL`/`LLM_MODEL`）
- 密钥只写本地 `.env`，**禁止提交 Git**（.gitignore 已排除）

### 3. 启动基础设施

```powershell
docker compose up -d      # PostgreSQL + Redis（带 healthcheck）
docker compose ps         # 确认 healthy
```

> ⚠️ 重启机器后容器不会自启，需重新执行 `docker compose up -d`（或 `make up`）。

### 4. 启动 API

**前台启动（推荐，Ctrl+C 干净停止）**：

```powershell
cd backend
uv run uvicorn app.main:app --reload --port 39800
```

**后台启动（PowerShell）**：

```powershell
Start-Process -FilePath ".venv\Scripts\python.exe" -ArgumentList "-m","uvicorn","app.main:app","--reload","--host","127.0.0.1","--port","39800" -WorkingDirectory "D:\Development\Workspace\vscodepro\ai-ppt-generator\backend" -WindowStyle Hidden
```

**Makefile 方式（Git Bash）**：项目根目录执行 `make dev-api`

### 5. 验证

```powershell
curl http://127.0.0.1:39800/health
# {"status":"ok","app":"AI PPT Generator","debug":false}

cd backend
uv run pytest        # 冒烟测试
uv run ruff check .  # 静态检查
```

### 6. 停止服务

```powershell
# 可靠停止（必须杀整个进程树，见踩坑笔记 #2）
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*uvicorn*" -or $_.CommandLine -like "*spawn_main*" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

## Makefile 命令总览（Git Bash 执行）

| 命令 | 作用 |
|---|---|
| `make up` / `make down` | 启停 PG + Redis 容器 |
| `make install` | uv sync 安装依赖 |
| `make migrate` | Alembic 迁移（W2-D2 起生效） |
| `make dev-api` / `make dev-worker` / `make dev-web` | 分别启动 API / Worker / 前端 |
| `make test` / `make lint` / `make fmt` | 测试 / 检查 / 格式化 |

## 踩坑笔记

1. **Docker Hub 直连被阻断（EOF）**
   - 现象：`docker pull` 报 `Get "https://registry-1.docker.io/v2/": EOF`
   - 解决：从 DaoCloud 镜像站手动拉取并重打标签：
     ```powershell
     docker pull docker.m.daocloud.io/library/postgres:16-alpine
     docker pull docker.m.daocloud.io/library/redis:7-alpine
     docker tag docker.m.daocloud.io/library/postgres:16-alpine postgres:16-alpine
     docker tag docker.m.daocloud.io/library/redis:7-alpine redis:7-alpine
     ```
   - 根治：在 Docker Desktop → Settings → Docker Engine 配置
     `"registry-mirrors": ["https://docker.m.daocloud.io"]`

2. **uvicorn --reload 父子进程停止问题**
   - 现象：杀掉父进程后端口仍被占用，netstat 显示已死 PID 仍在 LISTENING
   - 原因：`--reload` 父进程持有端口、multiprocessing spawn 子进程实际服务；父进程被杀时 socket 被子进程继承
   - 解决：按命令行匹配杀整个进程树（见上文「停止服务」）

3. **pytest-asyncio 弃用警告**
   - 需在 pyproject 显式设置 `asyncio_default_fixture_loop_scope = "function"`

4. **Windows 下 Makefile**
   - 原生 PowerShell 无 make，需在 Git Bash 中执行，或手动拆解命令
