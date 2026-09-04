# AI Engineering Copilot

面向软件研发团队的 AI Engineering Platform。

**当前进度：** Phase 1–11 — 七大 AI 能力 + **平台硬化**（异步任务、工作流拆分、只读仓库上下文）。  
**仍不包含：** Agent / LangChain、Git/CI 真实指标采集、向工作区自动写代码、SSE/Celery。

## 项目结构

```text
JDT/
├── backend/
│   ├── app/
│   │   ├── admin/           # SQLAdmin (/admin)
│   │   ├── api/v1/          # auth / projects / repo / AI workflows
│   │   ├── core/            # config / logging / exceptions / security / repo_limits
│   │   ├── db/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   └── services/        # AI jobs + repo_service + llm/
│   ├── alembic/versions/
│   └── tests/
├── frontend/src/
│   ├── api/ auth/ layouts/ pages/project-detail/
│   └── components/workflow/ components/repo/
├── docker-compose.yml
├── .env.example
└── specs/                   # phase-1 … phase-11
```

## 架构决策（摘要）

1. Monorepo；API → Service → Repository。
2. 同步 SQLAlchemy；开发/生产用 PostgreSQL；pytest 用 SQLite 内存库。
3. JWT Access Token（Bearer）；密码 bcrypt；越权项目返回 404。
4. 业务 API 前缀 `/api/v1`；`GET /health` 仍在根路径。
5. Compose 仅 Postgres + Redis；应用本地启动；**Redis 业务未强依赖**。
6. **AI 任务异步**：POST 创建 `pending` → 进程内 `BackgroundTasks` → `running` → `succeeded`/`failed`；前端轮询详情。
7. **只读仓库**：基于 `repo_path` 浏览文件树/读文件，可选 `selected_files` 注入 Prompt；**不写回仓库**。

## 前置条件

- Python 3.12+
- Node.js 20+
- Docker / Docker Compose（跑 Postgres/Redis）

## 快速开始

### 1. 环境变量

```powershell
Copy-Item .env.example .env
```

### 2. 基础设施

```powershell
docker compose up -d
```

### 3. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health：http://localhost:8000/health  
- OpenAPI：http://localhost:8000/docs  
- **Admin 数据库控制台**：http://localhost:8000/admin  
  - 默认账号见 `.env`：`ADMIN_USERNAME` / `ADMIN_PASSWORD`（示例为 `admin` / `admin123456`）  
  - 可在页面中对 **Users / Projects** 做增删改查  
  - 生产环境若使用弱口令将自动禁用 Admin

测试：

```powershell
pytest -q
```

### 4. Frontend

```powershell
cd frontend
npm install
npm run dev
```

打开 http://localhost:5173 ，注册/登录后管理项目。

也可双击根目录 `start.bat`（需已安装依赖与 Docker）。

## 主要 API

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/v1/auth/register` | 注册 |
| POST | `/api/v1/auth/login` | 登录，返回 `access_token` |
| GET | `/api/v1/auth/me` | 当前用户（需 Bearer） |
| CRUD | `/api/v1/projects` | 项目（仅本人；越权 404） |

示例：

```http
Authorization: Bearer <access_token>
```

## 配置说明

| 变量 | 说明 |
|------|------|
| `APP_ENV` | development / test / production |
| `CORS_ORIGINS` | 逗号分隔 |
| `DATABASE_URL` | SQLAlchemy 连接串 |
| `REDIS_URL` | Redis（本阶段业务未强依赖） |
| `JWT_SECRET_KEY` | JWT 签名密钥（生产务必更换） |
| `JWT_ALGORITHM` | 默认 HS256 |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 默认 1440 |
| `ADMIN_ENABLED` | 是否启用 `/admin` |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | 管理台登录（与业务用户无关） |
| `ADMIN_SESSION_SECRET` | 可选；缺省回落 `JWT_SECRET_KEY` |
| `LLM_ENABLED` | 是否启用 LLM |
| `LLM_API_KEY` / `LLM_MODEL` / `LLM_BASE_URL` | OpenAI 兼容配置 |

## Phase 4 Requirement Analysis

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/v1/projects/{id}/requirement-analyses` | 异步分析（立即返回，后台跑 LLM） |
| GET | `/api/v1/projects/{id}/requirement-analyses` | 历史列表 |
| GET | `/api/v1/projects/{id}/requirement-analyses/{aid}` | 详情（轮询至终态） |

状态：`pending` → `running` → `succeeded` \| `failed`。

## Phase 5 Technical Planning

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/v1/projects/{id}/technical-plans` | 异步生成技术规划 |
| GET | `/api/v1/projects/{id}/technical-plans` | 历史列表 |
| GET | `/api/v1/projects/{id}/technical-plans/{pid}` | 详情 |

请求体：`requirement_analysis_id`、`context_text`、`selected_files` 至少一项有效输入；关联分析须同项目且 `status=succeeded`。可选 `selected_files`（仓库相对路径）注入 Prompt。

本地 SQLite（`start.bat`）会通过 `init_db` 自动建表/补列；Postgres 需执行：

```powershell
cd backend
alembic upgrade head
```

Frontend：项目详情 **Tabs** —「项目信息 / 需求分析 / 技术规划 / AI 编码 / 自动化测试 / 代码审查 / AI 调试 / 研发度量」（AI Tab **懒加载**）。

## Phase 6 AI Coding

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/v1/projects/{id}/code-generations` | 异步生成代码建议 |
| GET | `/api/v1/projects/{id}/code-generations` | 历史列表 |
| GET | `/api/v1/projects/{id}/code-generations/{gid}` | 详情 |

请求体：`task_description` 必填；可选 `technical_plan_id`、`context_text`、`selected_files`。  
**不向 `repo_path` 写入文件**。

## Phase 7 Automated Testing

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/v1/projects/{id}/test-generations` | 异步生成测试建议 |
| GET | `/api/v1/projects/{id}/test-generations` | 历史列表 |
| GET | `/api/v1/projects/{id}/test-generations/{tid}` | 详情 |

请求体：`target_description` 必填；可选 `code_generation_id`、`context_text`、`selected_files`。  
**不执行 pytest、不写 `repo_path`**。

## Phase 8 AI Code Review

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/v1/projects/{id}/code-reviews` | 异步代码审查 |
| GET | `/api/v1/projects/{id}/code-reviews` | 历史列表 |
| GET | `/api/v1/projects/{id}/code-reviews/{rid}` | 详情 |

请求体：`review_scope` 必填；可选 `code_generation_id`、`context_text`、`selected_files`。  
**不自动修改代码、不写 `repo_path`**。

## Phase 9 AI Debugging

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/v1/projects/{id}/debug-sessions` | 异步调试分析 |
| GET | `/api/v1/projects/{id}/debug-sessions` | 历史列表 |
| GET | `/api/v1/projects/{id}/debug-sessions/{sid}` | 详情 |

请求体：`problem_description` 必填；可选 `code_review_id`、`code_generation_id`、`context_text`、`selected_files`。  
**不自动修复、不写 `repo_path`**。

## Phase 10 Development Metrics

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/v1/projects/{id}/development-metrics` | 异步生成研发度量报告 |
| GET | `/api/v1/projects/{id}/development-metrics` | 历史列表 |
| GET | `/api/v1/projects/{id}/development-metrics/{mid}` | 详情 |

请求体：`metrics_focus` 必填；可选 `context_text`。Service 自动汇总本项目六类 AI 工作流统计并入 Prompt。  
**非 Git/CI 真实 DORA 指标**。

## Phase 11 Platform Hardening

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/v1/projects/{id}/repo/tree` | 只读文件树（深度/条目上限） |
| GET | `/api/v1/projects/{id}/repo/file?path=` | 只读单文件（大小/类型限制） |

- AI 创建均为异步；创建响应多为 `pending`，请轮询详情至 `succeeded`/`failed`。
- 规划 / 编码 / 测试 / 审查 / 调试支持 `selected_files`；任一文件读取失败则整单 `failed`。
- 路径须落在 `repo_path` 内，禁止 `..` 穿越；超大/二进制拒绝。
- 进程内 `BackgroundTasks`（无 Redis 队列）；进程崩溃可能导致残留 `running`（本阶段不自动回收）。

| Path | 说明 |
|------|------|
| `/login` `/register` | 公开 |
| `/` | Dashboard（需登录） |
| `/projects` `/projects/:id` | 项目列表/详情（需登录） |

## Phase 3 Admin

| URL | 说明 |
|-----|------|
| http://localhost:8000/admin | SQLAdmin 控制台（Users / Projects CRUD） |

## 尚未实现（后续增强）

- Refresh Token / OAuth / SSO
- Organization、成员、复杂 RBAC
- Agent / LangChain / 向工作区自动写代码或对接真实工程指标
- Celery / Redis 队列、SSE/WebSocket、取消进行中的 LLM
- 应用容器化、软删除、监控告警、`running` 超时清扫
- Admin Hash SPA（`/admin#/`）与任意 SQL 控制台

> 无 Docker 时可用 `start.bat` 的 SQLite 回退；Admin 同样可用。
