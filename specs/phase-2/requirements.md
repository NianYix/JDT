# AI Engineering Copilot — Phase 2 Requirements（核心业务骨架）

> 前置：Phase 1 基础工程已完成（FastAPI / React / Compose / Health）  
> 阶段目标：落地 User/Auth + Project 最小业务闭环，为后续 AI 能力提供归属载体  
> 状态：待确认

## 1. 背景与范围

### 1.1 阶段目标

在现有分层架构上实现：

1. 用户注册 / 登录与鉴权
2. 项目（Project）创建 / 列表 / 详情
3. 项目与工作区元数据（仓库路径等）关联
4. 统一 `/api/v1` API 约定与首批 Alembic 业务迁移
5. Frontend 对应页面与基础鉴权态

### 1.2 In Scope

- User 模型与认证（注册、登录、获取当前用户）
- JWT 访问令牌（Access Token）鉴权
- Project CRUD 中的 Create / List / Detail（本阶段可含最小 Update/Delete）
- Project 工作区元数据字段（如 `repo_path` / `description`）
- Alembic 首批业务表迁移
- API 前缀 `/api/v1`、统一分页与错误约定扩展
- Frontend：登录/注册页、项目列表、项目详情、受保护路由
- pytest 覆盖认证与 Project 核心路径

### 1.3 Out of Scope（本阶段不做）

- LLM / Agent / LangChain / LangGraph
- Requirement Analysis 等七大 AI 业务能力
- OAuth / SSO / 第三方登录
- 复杂 RBAC（角色权限矩阵）；仅做「登录用户只能操作自己的项目」
- 团队/组织（Organization）、成员邀请、多人协作
- 文件上传、Git 远程同步、Webhook
- Redis Session 存储（Token 校验以 JWT 为主；Redis 仍仅基础设施预留）
- Backend/Frontend 容器化应用服务

---

## 2. 功能需求（EARS）

### 2.1 用户与认证

**REQ-AUTH-001**  
WHEN 客户端提交合法的注册信息（邮箱、密码、显示名）时，THE SYSTEM SHALL 创建用户账户并返回成功结果（不得明文存储密码）。

**REQ-AUTH-002**  
WHEN 注册所用邮箱已存在时，THE SYSTEM SHALL 拒绝注册并返回明确的业务错误码。

**REQ-AUTH-003**  
WHEN 客户端提交正确的邮箱与密码时，THE SYSTEM SHALL 签发 JWT Access Token，并返回用户基础信息。

**REQ-AUTH-004**  
WHEN 客户端提交错误的邮箱或密码时，THE SYSTEM SHALL 拒绝登录且不泄露具体是邮箱还是密码错误（统一认证失败信息）。

**REQ-AUTH-005**  
WHEN 客户端携带有效 Access Token 请求受保护资源时，THE SYSTEM SHALL 识别当前用户并允许访问。

**REQ-AUTH-006**  
WHEN 客户端未携带 Token、Token 无效或已过期时，THE SYSTEM SHALL 返回 401 Unauthorized。

**REQ-AUTH-007**  
WHEN 已认证用户请求「当前用户」接口时，THE SYSTEM SHALL 返回其公开资料（id、email、display_name、created_at），不得返回密码哈希。

### 2.2 项目（Project）

**REQ-PROJ-001**  
WHEN 已认证用户提交合法的项目创建请求时，THE SYSTEM SHALL 创建归属该用户的 Project，并持久化名称、可选描述与可选工作区路径（repo_path）。

**REQ-PROJ-002**  
WHEN 已认证用户请求项目列表时，THE SYSTEM SHALL 仅返回该用户拥有的项目（支持基础分页）。

**REQ-PROJ-003**  
WHEN 已认证用户请求其拥有的项目详情时，THE SYSTEM SHALL 返回完整项目字段。

**REQ-PROJ-004**  
WHEN 已认证用户请求不属于自己的项目详情时，THE SYSTEM SHALL 返回 404 或 403（实现时二选一并在设计中固定），且不得泄露他人物件存在性细节超出选定策略。

**REQ-PROJ-005**  
WHEN 未认证用户访问 Project API 时，THE SYSTEM SHALL 返回 401。

**REQ-PROJ-006**  
WHEN 已认证用户更新其项目的允许字段（名称、描述、repo_path）时，THE SYSTEM SHALL 持久化变更并返回更新后的项目。

**REQ-PROJ-007**  
WHEN 已认证用户删除其拥有的项目时，THE SYSTEM SHALL 删除该项目记录（本阶段硬删除即可）。

### 2.3 API 与数据约定

**REQ-API-001**  
THE SYSTEM SHALL 将业务 API 挂载在 `/api/v1` 前缀下；`GET /health` 保持根路径不变。

**REQ-API-002**  
THE SYSTEM SHALL 对列表接口提供统一分页参数（如 `page` + `page_size`）与包含 `items` / `total` 的响应结构。

**REQ-API-003**  
THE SYSTEM SHALL 通过 Alembic 迁移创建 `users` 与 `projects` 表，禁止仅依赖运行时 `create_all` 作为生产路径。

**REQ-API-004**  
THE SYSTEM SHALL 继续使用 API / Service / Repository 分层，User 与 Project 均不得在 API 层直接操作 Session 拼业务逻辑。

### 2.4 Frontend

**REQ-FE-001**  
WHEN 未登录用户访问受保护页面时，THE SYSTEM SHALL 重定向至登录页。

**REQ-FE-002**  
WHEN 用户在登录/注册页提交成功时，THE SYSTEM SHALL 保存 Access Token 并进入项目列表页。

**REQ-FE-003**  
THE SYSTEM SHALL 提供项目列表页与项目详情页，并支持创建项目的最小表单交互。

**REQ-FE-004**  
WHEN 用户点击退出时，THE SYSTEM SHALL 清除本地 Token 并回到登录页。

### 2.5 测试与质量

**REQ-TEST-001**  
THE SYSTEM SHALL 提供 pytest 用例覆盖：注册、登录、鉴权失败、创建项目、列表仅本人、越权访问拒绝。

**REQ-TEST-002**  
THE SYSTEM SHALL 在测试环境使用独立配置（`APP_ENV=test`），测试不得依赖开发者本机手工数据。

---

## 3. 非功能需求

**REQ-NFR-001**  
密码哈希 SHALL 使用经过实践验证的算法（如 bcrypt / argon2），不得自研哈希。

**REQ-NFR-002**  
JWT 密钥、过期时间 SHALL 通过环境变量配置，并在 `.env.example` 中提供占位说明（无真实密钥）。

**REQ-NFR-003**  
THE SYSTEM SHALL 保持依赖最小化：仅增加认证与密码哈希所必需的库，不引入 Agent/LLM 相关包。

**REQ-NFR-004**  
关键代码 SHALL 保持 Type Hint，并延续现有日志与统一异常处理风格。

---

## 4. 验收标准

| ID | 验收项 | 通过条件 |
|----|--------|----------|
| AC-01 | 注册登录 | 可注册新用户并登录拿到 Token |
| AC-02 | 鉴权 | 无 Token / 坏 Token 访问受保护 API 返回 401 |
| AC-03 | 当前用户 | `GET /api/v1/auth/me`（或等价）返回资料且无密码字段 |
| AC-04 | 项目 CRUD | 可创建、列表、详情、更新、删除自己的项目 |
| AC-05 | 数据隔离 | 用户 A 无法读取用户 B 的项目 |
| AC-06 | 迁移 | Alembic 可 upgrade 出 users/projects 表 |
| AC-07 | Frontend | 登录后可见项目列表；未登录进保护页会跳转登录 |
| AC-08 | 测试 | 相关 pytest 全部通过 |
| AC-09 | 无 AI | 无 LLM/Agent 依赖与接口 |

---

## 5. 待确认默认假设

1. **鉴权方式**：JWT Access Token（Bearer），本阶段不做 Refresh Token。  
2. **越权策略**：访问他人项目返回 **404**（防枚举）。  
3. **登录标识**：使用 **email + password**（不用用户名登录）。  
4. **Project 归属**：仅 `owner_id` 单用户拥有；无成员表。  
5. **Frontend Token 存储**：`localStorage`（本阶段简单实现；后续可改为更安全方案）。  
6. **测试 DB**：优先 SQLite 内存库或独立 test Postgres（设计阶段选定一种并写死）。

请确认本 Requirements（可直接回复「确认」或修改上述假设）。确认后我将生成 `specs/phase-2/design.md`。
