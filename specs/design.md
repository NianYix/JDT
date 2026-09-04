# AI Engineering Copilot — 基础工程 Design

> 基于已确认的 `requirements.md`  
> 状态：待确认后生成 `tasks.md`

## 1. 架构概览

本阶段采用 **Monorepo**，前后端与基础设施并列，业务与 AI 能力留空。

```
JDT/
├── backend/                 # FastAPI 应用（可独立启动）
├── frontend/                # React + Vite（可独立启动）
├── docker-compose.yml       # PostgreSQL + Redis
├── .env.example             # 环境变量模板（无真实密码）
├── specs/                   # 需求/设计/任务文档
└── README.md                # 安装与启动说明
```

```mermaid
flowchart LR
  subgraph Client
    FE[Frontend<br/>React + Vite :5173]
  end
  subgraph App
    API[API Layer]
    SVC[Service Layer]
    REPO[Repository Layer]
  end
  subgraph Infra
    PG[(PostgreSQL)]
    RD[(Redis)]
  end
  FE -->|HTTP + CORS| API
  API --> SVC --> REPO
  REPO -->|SQLAlchemy| PG
  SVC -.->|可选连通性预留| RD
```

**原则：**

- Backend / Frontend 各自独立启动；本阶段 Compose **仅**提供 postgres + redis。
- 分层：`API → Service → Repository`；本阶段无业务 Model，Repository 仅保留基础设施连通骨架（如 health 依赖检查可走 service，不必强绑表）。
- 配置集中、环境隔离（development / test / production），经环境变量注入。
- 不引入 Agent / LLM / 业务 CRUD。

---

## 2. Backend 设计

### 2.1 目录结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 入口：挂载路由、中间件、异常处理
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # 集中配置（Pydantic Settings）
│   │   ├── logging.py          # 基础日志配置
│   │   └── exceptions.py       # 业务/应用异常类型 + 统一处理器注册
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py           # 聚合路由
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── health.py       # GET /health（或挂在 /api/v1/health，对外文档约定根路径别名见下）
│   ├── services/
│   │   ├── __init__.py
│   │   └── health_service.py   # 健康检查编排（可选探测 DB）
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── health_repository.py # 可选：SELECT 1 探测
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py             # Declarative Base（空，无业务表）
│   │   └── session.py          # Engine / Session 工厂
│   └── schemas/
│       ├── __init__.py
│       └── health.py           # HealthResponse Pydantic 模型
├── alembic/
│   ├── env.py
│   └── versions/               # 空目录或占位，无业务 migration
├── alembic.ini
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_health.py
├── pyproject.toml              # 或 requirements.txt + requirements-dev.txt
└── .env.example                # 可与根目录共用一份，Backend 读取根或本地
```

### 2.2 分层职责

| 层 | 职责 | 本阶段内容 |
|----|------|------------|
| API | HTTP 契约、状态码、依赖注入入参 | `/health` |
| Service | 用例编排、不感知 FastAPI | 组装 health 状态 |
| Repository | 数据访问 | 可选 `SELECT 1`；无业务实体 |
| Core | 配置、日志、异常 | Settings / logging / handlers |
| Schemas | 请求/响应模型 | HealthResponse、ErrorResponse |

### 2.3 API 约定

- **健康检查**：`GET /health`  
  响应示例：`{"status":"ok","environment":"development"}`  
  （可选扩展：`database` / `redis` 连通字段；若探测失败仍返回 200 且 `status=degraded`，或按实现简化为仅进程存活——实现时优先 **进程存活即可**，DB/Redis 探测作为可选增强，避免本地无 Compose 时测试脆弱。）
- **CORS**：development 默认允许 `http://localhost:5173`；来源列表由配置 `CORS_ORIGINS` 控制。
- **统一异常**：捕获自定义 `AppError` 与未处理 `Exception`，返回 JSON：`{"detail": "...", "code": "..."}`，并写日志。
- **日志**：启动时配置 root/app logger；请求级可后续再加中间件，本阶段基础 logging 即可。

### 2.4 配置（集中管理）

使用 `pydantic-settings`，字段示例：

| 变量 | 说明 | 示例 |
|------|------|------|
| `APP_ENV` | development / test / production | `development` |
| `APP_NAME` | 应用名 | `AI Engineering Copilot` |
| `API_PREFIX` | 可选 API 前缀 | ``（health 挂根路径） |
| `CORS_ORIGINS` | 逗号分隔或 JSON 列表 | `http://localhost:5173` |
| `DATABASE_URL` | SQLAlchemy URL | `postgresql+psycopg://...` |
| `REDIS_URL` | Redis URL | `redis://localhost:6379/0` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

- **development / test / production**：由 `APP_ENV` 切换默认值与校验（如 production 拒绝弱默认密码提示仅文档级；代码侧至少按 env 加载）。
- **test**：pytest 使用独立 settings（可覆盖 `APP_ENV=test`），健康测试用 `TestClient`，不强制真实 DB。

### 2.5 数据库与 Alembic

- SQLAlchemy 2.x：`create_engine` + `sessionmaker`；本阶段 **无业务表**。
- Alembic：初始化 `env.py` 绑定 `Base.metadata`；`versions/` 为空（无业务 migration）。
- **async**：本阶段默认 **同步** SQLAlchemy + 同步 FastAPI 路由，避免无明确 I/O 收益时引入 async 复杂度。若后续需要高并发 I/O 再迁移 async session。

### 2.6 Redis

- 配置项 `REDIS_URL` 预留；本阶段可不在请求路径强制连接 Redis。
- 可选：在 health service 中惰性探测（失败不阻断进程启动）。

### 2.7 依赖（最小化）

**运行时：**

- fastapi, uvicorn[standard]
- sqlalchemy, psycopg[binary]（或 psycopg2-binary，优先 psycopg3）
- pydantic, pydantic-settings
- alembic
- redis（客户端库，预留）
- python-dotenv（若 settings 需要）

**开发/测试：**

- pytest, httpx（TestClient 依赖）

**禁止：** langchain, langgraph, openai SDK（业务 LLM）等。

---

## 3. Frontend 设计

### 3.1 目录结构

```
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── vite.config.ts
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── vite-env.d.ts
│   ├── layouts/
│   │   └── MainLayout.tsx      # Ant Design Layout：侧栏/顶栏骨架
│   ├── pages/
│   │   └── Dashboard.tsx       # 占位 Dashboard
│   └── styles/
│       └── global.css          # 最小全局样式（可极少）
└── .env.example                # 可选 VITE_API_BASE_URL
```

### 3.2 页面与路由

- 使用 `react-router-dom` 最小路由：`/` → Dashboard。
- `MainLayout`：Header 显示产品名「AI Engineering Copilot」；Content 渲染子路由；侧栏可仅「Dashboard」一项。
- Dashboard：标题 + 简短说明「基础工程已就绪，业务能力后续迭代」；不调用 LLM，可不强制调 `/health`（可选展示 API 地址说明）。

### 3.3 依赖（最小化）

- react, react-dom, react-router-dom
- antd
- typescript, vite, @vitejs/plugin-react

不引入状态管理库、图表库、Agent SDK。

### 3.4 端口与代理

- Dev server：`5173`
- 可选 `vite` proxy：`/health` → `http://localhost:8000`（非必须；本阶段 Dashboard 可不请求后端）

---

## 4. Infrastructure 设计

### 4.1 docker-compose.yml（根目录）

服务：

| Service | Image | 端口 | 说明 |
|---------|-------|------|------|
| postgres | postgres:16-alpine | 5432 | 用户/库/密码来自 env |
| redis | redis:7-alpine | 6379 | 无密码开发默认 |

- 命名 volume 持久化 postgres 数据。
- **不**在本阶段定义 backend/frontend 容器服务。
- healthcheck：postgres `pg_isready`；redis `redis-cli ping`。

### 4.2 环境变量文件

根目录 `.env.example`（可被 compose 与 backend 共用约定）：

```
APP_ENV=development
CORS_ORIGINS=http://localhost:5173
DATABASE_URL=postgresql+psycopg://aec:aec@localhost:5432/aec
REDIS_URL=redis://localhost:6379/0
POSTGRES_USER=aec
POSTGRES_PASSWORD=aec
POSTGRES_DB=aec
```

真实 `.env` gitignore；示例中仅占位口令。

---

## 5. 测试与验收映射

| 验收 | 设计对应 |
|------|----------|
| AC-01 Backend 启动 + /health | `main.py` + `health` 路由 + uvicorn |
| AC-02 Frontend Layout + Dashboard | `MainLayout` + `Dashboard` |
| AC-03 Compose | `docker-compose.yml` 两服务 |
| AC-04 配置三环境 | `Settings` + `.env.example` |
| AC-05 CORS | FastAPI CORSMiddleware |
| AC-06 异常与日志 | `exceptions` + `logging` |
| AC-07 pytest | `tests/test_health.py` |
| AC-08 Frontend build | `npm run build` |
| AC-09 无业务/Agent | 目录与依赖清单审查 |

---

## 6. 架构决策记录（ADR 摘要）

1. **Monorepo**：前后端同仓，便于一份 Compose 与文档对齐。  
2. **同步 SQLAlchemy**：本阶段无高并发 I/O 诉求，降低复杂度；async 留待后续。  
3. **Health 挂根路径 `/health`**：运维与 Compose 探测习惯；与未来 `/api/v1/*` 业务前缀分离。  
4. **Repository 仍保留**：即使无业务表，用 health 探测体现分层，避免日后推倒重来。  
5. **Compose 不含应用容器**：满足「前后端可独立启动」与最小基建。  
6. **不实现业务 Model / LLM**：严格本阶段范围，防止范围蔓延。

---

## 7. 交付物（实现完成后输出）

1. 项目结构树  
2. 架构决策说明（本节 ADR）  
3. 安装与启动方式（README）  
4. 运行 Backend Test 结果  
5. Frontend Build 结果  
6. Docker Compose 配置检查结果  
7. 未实现事项清单  

---

## 8. 待确认

1. 依赖清单与「同步 SQLAlchemy、Compose 不含 app」是否按本文落地？  
2. Health 是否仅进程存活（推荐），还是必须探测 DB/Redis？  
3. 包管理：Backend 用 `pyproject.toml` + pip，还是 `requirements.txt`？

请确认本 Design。确认后我将生成 `tasks.md`；你回复「开始执行」后才会改代码。
`)