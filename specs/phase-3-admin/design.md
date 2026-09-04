# AI Engineering Copilot — Phase 3 Design（SQLAdmin 管理端）

> 基于已确认的 `specs/phase-3-admin/requirements.md`  
> 方案：SQLAdmin；原生 `/admin` URL；独立管理员账号；仅 users / projects  
> 状态：待确认后生成 `tasks.md`

## 1. 架构概览

在现有 FastAPI 进程内挂载 SQLAdmin，复用同一 SQLAlchemy Engine / Session 与 ORM Model。

```text
Browser
  └─ http://localhost:8000/admin
        └─ SQLAdmin (Starlette templates)
              ├─ authentication_backend (ADMIN_USERNAME / ADMIN_PASSWORD)
              ├─ UserAdmin  → app.models.User
              └─ ProjectAdmin → app.models.Project
                    └─ Session / Engine (与业务 API 共用)
```

**原则：**

- 管理端与业务 API 同端口、同进程，无需单独前端工程。
- Admin 直接基于 ORM ModelView，不经过业务 Service（可接受：运维通道）；业务 API 语义不变。
- 普通用户 JWT **不能**进入 `/admin`。

---

## 2. 依赖

Backend 新增：

- `sqladmin`（及传递依赖，如其模板引擎）

不新增 React Admin、不新增 LLM 相关包。

---

## 3. 集成点

### 3.1 挂载

在 `create_app()` 中：

1. 创建 `Admin(app, engine=get_engine(), authentication_backend=...)`
2. `admin.add_view(UserAdmin)`
3. `admin.add_view(ProjectAdmin)`

建议抽到：

```text
backend/app/admin/
  __init__.py          # setup_admin(app) 
  auth.py              # AdminAuth(AuthenticationBackend)
  views.py             # UserAdmin, ProjectAdmin
```

### 3.2 Engine

- 调用已有 `get_engine()`，兼容 Postgres 与 SQLite fallback。
- SQLAdmin 使用同步 engine（与当前一致）。

### 3.3 路径

| URL | 说明 |
|-----|------|
| `/admin` | 控制台主页（登录后可见模型列表） |
| `/admin/...` | SQLAdmin 生成的 list/create/edit/detail（原生路径） |

不实现 `/admin#/`、`/admin/db#/` Hash SPA。

---

## 4. 鉴权设计

### 4.1 配置项

| 变量 | 说明 | 示例 |
|------|------|------|
| `ADMIN_USERNAME` | 管理端用户名 | `admin` |
| `ADMIN_PASSWORD` | 管理端密码 | 开发占位，生产必改 |
| `ADMIN_ENABLED` | 可选开关，默认 `true` | `true` / `false` |

写入 Settings + `.env.example`。

### 4.2 AuthenticationBackend

实现 SQLAdmin `AuthenticationBackend`：

- `login`：校验表单用户名密码与配置一致 → 写入 session
- `logout`：清 session
- `authenticate`：校验 session

**生产约束：**

- 当 `APP_ENV=production` 且 `ADMIN_PASSWORD` 为空或仍为明显占位（如 `admin` / `change-me`）时：  
  - **禁用** admin 挂载，并打 warning 日志；或  
  - 启动失败（设计选定：**禁用挂载 + warning**，避免误伤本地 prod 试跑）。

### 4.3 Session 中间件

SQLAdmin 登录依赖 Starlette SessionMiddleware。若应用尚未安装，在 `setup_admin` 时添加：

- `SessionMiddleware(secret_key=JWT_SECRET_KEY 或独立 ADMIN_SESSION_SECRET)`
- 推荐新增 `ADMIN_SESSION_SECRET`（可默认回落到 `JWT_SECRET_KEY` 以减少配置负担）

---

## 5. ModelView 设计

### 5.1 UserAdmin

- Model：`User`
- 列表列：`id`, `email`, `display_name`, `created_at`（**不展示** `hashed_password`）
- 创建/编辑：
  - 可编辑：`email`, `display_name`
  - 额外表单字段：`password`（可选；创建时必填）
  - 保存时若提供 password → `hash_password` 写入 `hashed_password`
  - **禁止**在表单中直接编辑 `hashed_password`
- 可搜索：`email`, `display_name`
- 可删除：是

### 5.2 ProjectAdmin

- Model：`Project`
- 列：`id`, `name`, `owner_id`, `repo_path`, `created_at`, `updated_at`
- 可编辑：`name`, `description`, `repo_path`, `owner_id`
- 可搜索：`name`, `repo_path`
- 可删除：是

---

## 6. 与现有功能关系

| 能力 | 影响 |
|------|------|
| `/health`、`/api/v1/*` | 不变 |
| Frontend React | 不变；管理台为独立后端页面 |
| `start.bat` | 无需改流程；文档补充打开 `/admin` |
| pytest | 增加少量冒烟：未登录访问 admin 被拦；可选登录页 200 |

测试注意：SessionMiddleware + TestClient cookie；至少断言 `/admin/login` 可访问或未认证跳转。

---

## 7. 安全说明（文档需写明）

- Admin 可直接改库，权限高于普通 API。
- 默认仅建议本机开发使用；生产必须强密码并限制网络暴露。
- 不提供任意 SQL 执行入口。

---

## 8. ADR

1. **SQLAdmin 而非自研 SPA**：最快交付表级 CRUD，符合当前阶段。  
2. **独立 Admin 账号**：与业务用户隔离。  
3. **密码只写哈希**：避免管理台泄露/篡改哈希字段。  
4. **生产弱口令则禁用 Admin**：降低误部署风险。  
5. **Admin 直连 ORM**：运维通道；复杂业务规则仍走 Service/API。

---

## 9. 待确认

1. 生产弱口令策略：按本文 **禁用挂载 + warning**？  
2. Session 密钥：回落 `JWT_SECRET_KEY`，或单独 `ADMIN_SESSION_SECRET`？（推荐：单独变量，缺省回落 JWT）  
3. `ADMIN_ENABLED` 开关是否需要？（推荐：要）

请确认本 Design。确认后生成 `tasks.md`；回复「开始执行」后再改代码。
