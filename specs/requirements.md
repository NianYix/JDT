# AI Engineering Copilot — 基础工程 Requirements

> 来源：`Demo.txt`  
> 阶段：仅建立基础工程架构，不实现任何 AI Agent / 业务功能  
> 状态：待确认

## 1. 背景与范围

### 1.1 产品目标（后续阶段，本阶段不实现）

AI Engineering Copilot 面向软件研发团队，后续将支持：

1. Requirement Analysis  
2. Technical Planning  
3. AI Coding  
4. Automated Testing  
5. AI Code Review  
6. AI Debugging  
7. Development Metrics  

### 1.2 本阶段 In Scope

- 从零创建可运行的 Backend（FastAPI）与 Frontend（React + Vite）基础工程
- Docker Compose 提供 PostgreSQL 与 Redis
- 配置、CORS、健康检查、统一异常、日志、pytest、基础 Layout/Dashboard
- 清晰分层（API / Service / Repository）骨架（无业务 Model）

### 1.3 本阶段 Out of Scope

- User / Project / Agent 等业务 Model
- LangChain、LangGraph 等 Agent Framework
- 任何 LLM API 调用
- Requirement Analysis、Technical Planning、AI Coding 等业务能力
- 非必要的炫技依赖

---

## 2. 功能需求（EARS）

### 2.1 工程初始化

**REQ-INIT-001**  
WHEN 当前项目目录为空或仅有说明文件时，THE SYSTEM SHALL 从零创建 Backend、Frontend、Infrastructure 基础工程目录与文件，使项目可独立安装与启动。

**REQ-INIT-002**  
WHEN 建立基础工程时，THE SYSTEM SHALL 不一次性实现业务功能，仅提供架构骨架与可运行的基础设施能力。

### 2.2 Backend 可独立启动

**REQ-BE-001**  
WHEN 开发者仅启动 Backend 进程时，THE SYSTEM SHALL 在不依赖 Frontend 的前提下成功监听 HTTP 端口并对外提供 API。

**REQ-BE-002**  
THE SYSTEM SHALL 使用 Python 3.12、FastAPI、SQLAlchemy 2.x、Pydantic v2、Alembic 作为 Backend 技术栈。

**REQ-BE-003**  
THE SYSTEM SHALL 采用 API / Service / Repository 分层架构组织 Backend 代码，并为关键路径使用 Type Hint。

**REQ-BE-004**  
WHEN 使用 async/await 时，THE SYSTEM SHALL 仅在 I/O 等待（如数据库、HTTP、Redis）等有明确理由的场景使用异步。

### 2.3 Frontend 可独立启动

**REQ-FE-001**  
WHEN 开发者仅启动 Frontend 开发服务器时，THE SYSTEM SHALL 在不依赖 Backend 业务接口的前提下成功启动并展示基础页面。

**REQ-FE-002**  
THE SYSTEM SHALL 使用 React、TypeScript、Vite、Ant Design 作为 Frontend 技术栈。

**REQ-FE-003**  
WHEN Frontend 启动后，THE SYSTEM SHALL 提供基础 Layout 与 Dashboard 页面作为默认入口。

### 2.4 基础设施（Docker Compose）

**REQ-INFRA-001**  
WHEN 开发者执行 Docker Compose 启动命令时，THE SYSTEM SHALL 启动 PostgreSQL 与 Redis 服务。

**REQ-INFRA-002**  
THE SYSTEM SHALL 通过 Docker / Docker Compose 管理开发期数据库与缓存依赖，而不在本阶段容器化业务应用（除非为启动依赖所必需的最小配置）。

### 2.5 配置管理

**REQ-CFG-001**  
THE SYSTEM SHALL 通过环境变量读取数据库与 Redis 连接配置。

**REQ-CFG-002**  
THE SYSTEM SHALL 区分 `development` / `test` / `production` 三种运行环境配置。

**REQ-CFG-003**  
THE SYSTEM SHALL 提供 `.env.example` 作为环境变量模板，且不得包含真实密码或生产密钥。

**REQ-CFG-004**  
THE SYSTEM SHALL 将所有应用配置集中管理，并避免引入全局可变状态。

### 2.6 跨域与健康检查

**REQ-API-001**  
WHEN Frontend 开发源向 Backend 发起跨域请求时，THE SYSTEM SHALL 按配置启用 CORS 并允许约定的源访问。

**REQ-API-002**  
WHEN 客户端请求 `GET /health` 时，THE SYSTEM SHALL 返回表示服务存活的成功响应（含明确状态字段）。

### 2.7 异常处理与日志

**REQ-ERR-001**  
WHEN API 处理过程中发生可预期或未捕获异常时，THE SYSTEM SHALL 通过统一异常处理机制返回结构化错误响应，而不是泄露未处理的堆栈给客户端。

**REQ-LOG-001**  
WHEN Backend 启动或处理请求时，THE SYSTEM SHALL 输出基础结构化或可读日志，便于本地排查。

### 2.8 测试

**REQ-TEST-001**  
THE SYSTEM SHALL 集成 pytest 测试框架，并至少包含可运行的健康检查（或等价烟雾）测试。

**REQ-TEST-002**  
WHEN 开发者执行 Backend 测试命令时，THE SYSTEM SHALL 能在本阶段范围内完成测试并给出通过/失败结果。

### 2.9 明确禁止项

**REQ-NEG-001**  
THE SYSTEM SHALL NOT 实现 User、Project、Agent 等业务数据模型与对应 CRUD。

**REQ-NEG-002**  
THE SYSTEM SHALL NOT 引入 LangChain、LangGraph 或其他 Agent Framework。

**REQ-NEG-003**  
THE SYSTEM SHALL NOT 实现任何 LLM API 调用能力。

**REQ-NEG-004**  
THE SYSTEM SHALL NOT 仅为展示而添加与本阶段目标无关的额外依赖。

---

## 3. 非功能需求

**REQ-NFR-001**  
THE SYSTEM SHALL 保证 Backend 与 Frontend 代码可实际运行，不得交付伪代码或无法启动的占位实现。

**REQ-NFR-002**  
THE SYSTEM SHALL 在关键代码处提供必要注释，说明架构意图与非显而易见的决策。

**REQ-NFR-003**  
THE SYSTEM SHALL 保持依赖最小化，优先使用技术栈约定内的标准库与官方生态组件。

**REQ-NFR-004**  
WHEN 本阶段交付完成时，THE SYSTEM SHALL 支持：输出项目结构、说明架构决策、提供安装启动方式、运行 Backend Test、检查 Frontend Build、检查 Docker Compose 配置，并列出未实现事项。

---

## 4. 验收标准（本阶段）

| ID | 验收项 | 通过条件 |
|----|--------|----------|
| AC-01 | Backend 独立启动 | `uvicorn`（或等价）可启动，`GET /health` 返回成功 |
| AC-02 | Frontend 独立启动 | Vite dev server 可启动，可见 Layout + Dashboard |
| AC-03 | Compose 依赖 | `docker compose` 可启动 PostgreSQL 与 Redis |
| AC-04 | 环境配置 | 存在 `.env.example`；配置支持 development/test/production |
| AC-05 | CORS | Backend 已配置 CORS |
| AC-06 | 异常与日志 | 存在统一异常处理与基础日志 |
| AC-07 | pytest | 至少一条测试可执行通过 |
| AC-08 | Frontend build | `npm run build`（或等价）成功 |
| AC-09 | 无业务/Agent | 无 User/Project/Agent Model，无 LangChain/LLM |

---

## 5. 待确认问题

1. Backend 默认端口是否采用 `8000`，Frontend 是否采用 `5173`？  
2. CORS 允许源在 development 是否默认为 `http://localhost:5173`？  
3. Alembic 是否仅初始化迁移骨架（空 migration / 无表），确认无业务表？  
4. Docker Compose 是否仅包含 `postgres` + `redis` 两个服务（本阶段不容器化 app）？  
5. 仓库根目录布局是否采用 monorepo：`backend/`、`frontend/`、`infra/`（或根级 `docker-compose.yml`）？

请确认本 Requirements。确认后我将生成 `design.md`。
`)