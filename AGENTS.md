# Repository Guidelines

## 项目结构与模块分工

FastAPI 入口位于 `backend/app/main.py`。HTTP 路由放在 `backend/app/api/routes/`，共享 API 依赖放在 `backend/app/api/deps.py`。Pydantic 请求和响应模型放在 `backend/app/schemas/`，SQLAlchemy 模型放在 `backend/app/models/`，配置、数据库初始化和安全工具放在 `backend/app/core/`。数据库迁移位于 `backend/alembic/versions/`，测试位于 `backend/tests/`，架构与环境搭建文档位于 `docs/`。

## 本地开发命令

使用 Python 3.13 或更新版本、`uv` 和 Docker Compose。将 `backend/.env.example` 复制为 `backend/.env`，本地凭据和 API 密钥仅保存在本地。在仓库根目录执行以下命令。

- `make install` 根据 `backend/uv.lock` 同步后端依赖。
- `make up` 启动 PostgreSQL 和 Redis，端口分别为 `39432` 和 `39379`。
- `make migrate` 对配置中的数据库执行 Alembic 迁移。
- `make dev-api` 在 `http://127.0.0.1:39800` 启动支持热重载的 API。访问 `/health` 检查服务是否正常。
- `make lint` 使用 Ruff 检查后端代码，`make fmt` 格式化后端 Python 文件。

## 编码风格与命名

Python 代码使用 4 个空格缩进，遵循 `backend/pyproject.toml` 中设置的 100 字符行宽。模块、函数和变量使用 `snake_case`，类使用 `PascalCase`。修改数据库表结构时，随模型改动一并提交 Alembic 迁移。

## 测试指南

后端使用 pytest 和 pytest-asyncio，接口测试使用 FastAPI 的 `TestClient`。测试文件命名为 `test_*.py`，测试函数命名为 `test_<行为>`。运行鉴权集成测试前，先启动 PostgreSQL 并执行迁移。使用 `make test` 运行全部后端测试，或使用 `cd backend && uv run pytest tests/test_auth.py` 单独运行鉴权测试。

## 提交与拉取请求

沿用 Git 历史中的提交格式，例如 `feat(auth): 新增 JWT 登录鉴权`、`feat(db): 新增用户表迁移` 或 `docs: 更新环境搭建指南`。每次提交聚焦一项改动。PR 中概述改动、列出已运行的检查，并附上相关 Issue 链接。涉及数据库迁移或环境变量时，在 PR 中注明。
