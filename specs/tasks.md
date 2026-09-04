# AI Engineering Copilot — 基础工程 Tasks

> 基于已确认的 `requirements.md`、`design.md`  
> 状态：已执行完成  
> 约定：Health 仅进程存活；Backend 用 pyproject.toml + pip；Compose 仅 postgres + redis

## 执行顺序说明

- 按 Phase 顺序执行；同 Phase 内可并行的任务已标注。  
- 每个任务完成后应满足对应验收勾选条件。  

---

## Phase 0 — 仓库地基

### T0.1 根目录与忽略规则
- [x] 创建 `.gitignore`（Python/Node/IDE/`.env`/构建产物等）
- [x] 创建根目录 `.env.example`（无真实生产密码）
- [x] 创建根目录 `README.md` 骨架（安装/启动占位，实现末完善）

**验收：** 无敏感文件被跟踪意图；示例 env 可复制为本地 `.env`。

### T0.2 Docker Compose
- [x] 编写根目录 `docker-compose.yml`（`postgres:16-alpine`、`redis:7-alpine`）
- [x] 配置端口 5432 / 6379、volume、healthcheck
- [x] 变量与 `.env.example` 对齐（`POSTGRES_USER/PASSWORD/DB`）

**验收：** Compose YAML 结构校验通过；文档说明 `docker compose up -d`。（本机未检测到 Docker CLI，运行时 `docker compose` 需安装 Docker Desktop。）

---

## Phase 1 — Backend 核心

### T1.1 项目与依赖
- [x] 创建 `backend/` 包结构（`app/`, `tests/`, `alembic/`）
- [x] 编写 `backend/pyproject.toml`（运行时 + 开发依赖，无 Agent/LLM 包）
- [x] 提供可安装方式（`pip install -e ".[dev]"` 或等价）

**验收：** 依赖可安装；无 langchain/langgraph/openai 等。

### T1.2 配置与日志
- [x] 实现 `app/core/config.py`（Pydantic Settings；`APP_ENV` = development/test/production）
- [x] 环境变量读取 `DATABASE_URL`、`REDIS_URL`、`CORS_ORIGINS`、`LOG_LEVEL` 等
- [x] 实现 `app/core/logging.py` 并在启动时初始化

**验收：** 切换 `APP_ENV` 可区分环境；配置集中、无全局可变业务状态。

### T1.3 异常处理
- [x] 定义应用异常类型与统一错误响应 schema
- [x] 在 FastAPI 注册异常处理器（含未捕获 Exception）

**验收：** 抛出应用异常时返回结构化 JSON，不向客户端泄露原始堆栈。

### T1.4 DB / Alembic 骨架
- [x] `app/db/base.py`、`session.py`（同步 SQLAlchemy 2.x Engine/Session）
- [x] 初始化 Alembic（`alembic.ini`、`env.py`），`versions/` 无业务 migration
- [x] **不**创建 User/Project/Agent 等表或 Model

**验收：** Alembic 可识别空 metadata；无业务 Model 文件。

### T1.5 分层 Health API
- [x] Schema：`HealthResponse`
- [x] Repository（可选空实现或占位，不强绑 DB 探测）
- [x] Service：返回进程存活状态 + `environment`
- [x] API：`GET /health`
- [x] `main.py`：CORS、路由挂载、日志/异常注册
- [x] `api/router` 聚合

**验收：** Backend 独立启动后 `GET /health` 返回成功（仅进程存活）。

### T1.6 Pytest
- [x] `tests/conftest.py`（TestClient / 测试 env）
- [x] `tests/test_health.py` 至少一条通过用例

**验收：** 在 backend 目录执行 pytest 通过。

---

## Phase 2 — Frontend 核心

### T2.1 Vite + React + TS 工程
- [x] 创建 `frontend/`（Vite React-TS）
- [x] 安装 antd、react-router-dom；配置 TypeScript / Vite
- [x] 可选 `.env.example`（`VITE_API_BASE_URL`）

**验收：** `npm install` 成功；无多余状态管理/图表/Agent 依赖。

### T2.2 Layout + Dashboard
- [x] `MainLayout`（Ant Design Layout，产品名展示）
- [x] `Dashboard` 占位页
- [x] 路由：`/` → Dashboard；挂到 `App.tsx`

**验收：** `npm run dev` 可独立启动并看到 Layout + Dashboard。

### T2.3 生产构建检查
- [x] 确保 `npm run build` 通过

**验收：** 构建无错误。

---

## Phase 3 — 文档与交付核验

### T3.1 README 完善
- [x] 项目结构说明
- [x] 架构决策摘要（指向 design ADR）
- [x] 安装与启动：Compose、Backend、Frontend、测试、build

**验收：** 按 README 可完成本地拉起。

### T3.2 交付检查清单（实现后执行并记录结果）
- [x] 输出最终项目结构树
- [x] 输出架构决策说明
- [x] 输出安装启动方式
- [x] 运行 Backend Test 并记录结果
- [x] 检查 Frontend Build 并记录结果
- [x] 检查 Docker Compose 配置并记录结果
- [x] 列出本阶段**未实现**事项（业务 Agent、LLM、业务 Model、app 容器化等）

**验收：** 满足 `Demo.txt`「完成后」7 项输出。
