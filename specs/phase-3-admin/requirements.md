# AI Engineering Copilot — Phase 3 Requirements（管理端数据库控制台）

> 前置：Phase 2 已具备 User / Project 与 JWT  
> 目标：提供类似服务器控制台的 Web 管理页，可在浏览器中对数据库表做增删改查  
> 状态：待确认

## 1. 背景与目标

希望在后端提供管理入口，大致体验为：

1. 打开管理主页（例如 `http://localhost:8000/admin`）
2. 进入数据库管理（查看表、行数据）
3. 对数据执行 **增 / 删 / 改 / 查**

本阶段优先交付 **可用的管理端 CRUD**，不重复造一套完整运维平台。

## 1.1 推荐技术方案（待确认）

采用 **SQLAdmin**（面向 FastAPI + SQLAlchemy 的管理后台）：

- 挂载路径：`/admin`
- 自动为已有 ORM 模型生成列表 / 详情 / 创建 / 编辑 / 删除页面
- 与当前同步 SQLAlchemy Session 兼容
- 依赖少，符合「不炫技」原则

> 说明：SQLAdmin 默认是服务端渲染页面（路径形如 `/admin`、`/admin/user/list`），**不一定**带前端 Hash 路由（`/admin#/`、`/admin/db#/`）。  
> 若必须严格复刻 Hash 风格 URL，需要自研 SPA，工作量显著更大。  
> **默认建议**：接受 SQLAdmin 原生 URL，功能等价（控制台主页 + 按表 CRUD）。

## 1.2 In Scope

- 管理后台入口与基础控制台主页
- 对业务表提供浏览器端 CRUD（至少 `users`、`projects`）
- 管理端访问保护（开发环境可用环境变量密码 / Basic Auth 或简易登录）
- 从 Backend 独立启动即可访问（仍为 FastAPI 同一进程挂载）
- 文档说明访问地址与账号配置

## 1.3 Out of Scope

- 自研完整前端 SPA 管理台（除非否决 SQLAdmin 方案）
- 任意 SQL 查询控制台 / 执行原始 SQL（安全风险高，本阶段不做）
- Redis 数据管理
- 多租户运维、审计日志大盘、监控告警
- LLM / Agent 相关能力
- 修改 Phase 2 业务 API 语义（仅新增 admin 能力）

---

## 2. 功能需求（EARS）

### 2.1 管理入口

**REQ-ADM-001**  
WHEN 开发者在浏览器访问管理根路径时，THE SYSTEM SHALL 展示管理控制台主页（或可进入各数据模型的导航入口）。

**REQ-ADM-002**  
THE SYSTEM SHALL 将管理端挂载在 Backend 同源端口（默认 `http://localhost:8000/admin`），无需单独前端工程启动管理台。

### 2.2 数据库表 CRUD

**REQ-ADM-003**  
WHEN 管理员进入用户（users）管理视图时，THE SYSTEM SHALL 支持列表查询、查看详情、创建、编辑、删除。

**REQ-ADM-004**  
WHEN 管理员进入项目（projects）管理视图时，THE SYSTEM SHALL 支持列表查询、查看详情、创建、编辑、删除。

**REQ-ADM-005**  
WHEN 列表数据量较大时，THE SYSTEM SHALL 提供分页（或等价分批浏览）能力。

**REQ-ADM-006**  
THE SYSTEM SHALL NOT 在管理界面以明文展示或回填用户密码；编辑用户密码时仅允许写入新密码并存储哈希（或禁止直接改 `hashed_password` 字段，二选一在设计中固定）。

### 2.3 访问控制

**REQ-ADM-007**  
WHEN 未通过管理端鉴权的请求访问 `/admin` 下受保护页面时，THE SYSTEM SHALL 拒绝访问并引导登录或返回 401/403。

**REQ-ADM-008**  
THE SYSTEM SHALL 通过环境变量配置管理端凭证（如 `ADMIN_USERNAME` / `ADMIN_PASSWORD`），并在 `.env.example` 提供占位值（非真实生产密码）。

**REQ-ADM-009**  
WHEN `APP_ENV=production` 且未配置强管理凭证时，THE SYSTEM SHALL 拒绝以空密码启用管理端（或启动时明确失败/禁用 admin）。

### 2.4 工程约束

**REQ-ADM-010**  
THE SYSTEM SHALL 复用现有 SQLAlchemy Model / Engine，不另行维护第二套表结构定义。

**REQ-ADM-011**  
THE SYSTEM SHALL 保持 API / Service / Repository 业务链路不被 admin 视图绕过破坏（admin 可直接操作 ORM，但业务 API 行为保持不变）。

**REQ-ADM-012**  
THE SYSTEM SHALL 不引入 LangChain 等无关依赖；仅增加实现管理台所需的最小依赖（如 `sqladmin`）。

---

## 3. 验收标准

| ID | 验收项 | 通过条件 |
|----|--------|----------|
| AC-01 | 打开 `/admin` | 可见管理主页/导航 |
| AC-02 | users CRUD | 可在页面增删改查用户（密码安全处理符合设计） |
| AC-03 | projects CRUD | 可在页面增删改查项目 |
| AC-04 | 鉴权 | 无凭证无法使用管理功能 |
| AC-05 | 配置 | `.env.example` 含管理端变量说明 |
| AC-06 | 启动 | `start.bat` / uvicorn 启动后即可访问，无需另开管理前端 |

---

## 4. 待确认默认假设

1. **实现方案**：采用 **SQLAdmin**（接受其原生 URL，不强制 `/admin#/`、`/admin/db#/` Hash 路由）。  
2. **鉴权**：管理端独立账号密码（环境变量），**不**复用普通用户 JWT（避免普通用户进后台）。  
3. **可管理表**：本阶段仅 `users`、`projects`。  
4. **密码字段**：管理端创建/编辑用户时提供「新密码」输入，后端写入 bcrypt 哈希；列表不展示哈希。  
5. **开放范围**：默认仅建议本地开发使用；生产需强密码。

请确认本 Requirements（可回「确认」或提出修改，例如必须自研 Hash 路由 SPA）。确认后生成 `design.md`。
