# AI Engineering Copilot — Phase 11 Design（平台硬化）

> 基于已确认的 `requirements.md`（建议默认全部采纳）  
> 状态：已与 requirements 对齐；`tasks.md` 已生成；待「开始执行」后实施

## 0. 已拍板决策

| # | 决策 |
|---|------|
| 1 | 后台：**进程内** FastAPI `BackgroundTasks` + **独立 DB Session**（无 Redis 依赖；SQLite/`start.bat` 可用） |
| 2 | 状态：`pending` → `running` → `succeeded` \| `failed` |
| 3 | 选中文件读取：任一失败 → **整单 `failed`** |
| 4 | Technical Planning Tab **挂文件选择器** |

LLM 未配置：创建记录为 `pending`，后台启动后标 `running`，Provider 工厂失败则标 `failed`（有明确 `error_message`），避免「永不执行」。

---

## 1. 架构概览

```text
POST /api/v1/projects/{id}/… (AI create)
  └─ XxxService.create()
        ├─ validate owner + payload (+ optional repo files list)
        ├─ INSERT status=pending  (commit)
        ├─ BackgroundTasks.add_task(run_ai_job, record_id, …)
        └─ return Public DTO immediately

Background worker (same process)
  └─ open new Session
        ├─ status = running; commit
        ├─ build prompt (upstream refs + repo files + context)
        ├─ LLMProvider.*()
        └─ status = succeeded|failed; commit

GET list/detail — unchanged paths; status includes running

Repo (new)
  GET  /api/v1/projects/{id}/repo/tree
  GET  /api/v1/projects/{id}/repo/file?path=…

Frontend
  ProjectDetailPage (shell + Tabs)
    ├─ ProjectInfoTab
    └─ WorkflowPanel (lazy per AI tab) + RepoFilePicker
          └─ create → poll get until terminal
```

---

## 2. 异步任务化

### 2.1 状态机

```text
pending ──(worker start)──► running ──success──► succeeded
                              │
                              └──failure────────► failed
```

- 既有 `Literal` / DB `String(32)` 扩展为含 `running`。
- 旧数据仅有 `pending|succeeded|failed`：无需迁移脚本强制改写；新写入使用新语义。
- Public schema：`status: Literal["pending","running","succeeded","failed"]`。

### 2.2 调度机制

**选用：`fastapi.BackgroundTasks`，不用 Celery/Redis。**

原因：与当前单进程 `uvicorn` + SQLite 回退一致；实现成本低。

关键约束：

1. **请求 Session 与后台 Session 分离**  
   Request 的 `get_db` 在响应后关闭；后台必须 `SessionLocal()` 新开会话，按 `record_id` 重新加载行。
2. **创建路径必须在调度前 `commit`**  
   否则后台可能读不到刚插入的行（尤其 PostgreSQL）。
3. **LLM 同步阻塞放在后台线程上下文**  
   Starlette `BackgroundTasks` 在响应发送后执行；同步 LLM 调用会占用该执行点。为避免拖住整个事件循环，后台入口使用：

   ```python
   def run_ai_job(...):
       # sync function scheduled via BackgroundTasks
       ...
   ```

   若运行在纯 async 路由上，则勿在 async def 内直接 `await` 长耗时 sync LLM；本项目路由保持 **sync `def`**，BackgroundTasks 在线程池语义下执行 sync 任务（与现有 FastAPI/Starlette 行为一致）。实施时以「创建接口快速返回 + pytest 断言创建响应时 LLM 尚未必须完成」为验收。

4. **幂等与卡死**  
   Worker 仅处理 `pending`（或允许 `pending`→`running` 一次）。若进程崩溃导致永久 `running`，本阶段不自动回收（文档说明；可后续加超时清扫）。

### 2.3 Service 改造模式

```text
create():
  require_project
  validate upstream refs / selected_files (path list only; content read in worker OR pre-validate paths exist)
  row = repo.create(..., status="pending", selected_paths_json=...)
  db.commit()  # ensure visible
  background_tasks.add_task(_execute, row.id)
  return Public(row)  # still pending

_execute(record_id):
  db = SessionLocal()
  try:
    row = load; row.status = "running"; commit
    context = build_context(...)  # may raise → failed
    result = provider.xxx(context)
    row.status = "succeeded"; row.result_json = ...
  except Exception as exc:
    row.status = "failed"; row.error_message = safe_message(exc)
  finally:
    commit; db.close()
```

API 层：各 create 端点增加 `background_tasks: BackgroundTasks` 并传入 Service。

### 2.4 测试策略

- Mock Provider 可注入「慢」或计数器：断言 POST 返回 `pending`/`running` 且 `result_json is null`，随后用 `TestClient` 的后台行为（Starlette 在请求结束跑 BackgroundTasks）再 GET 应为 `succeeded`。
- `TestClient` 默认同步执行 BackgroundTasks：现有「POST 后立即成功」测试改为「POST 后终态为 succeeded」（仍可在同一测试内 GET 验证），并新增显式断言状态曾可达终态。
- 失败 Provider → `failed` + `error_message`。

---

## 3. 工作流公共层（Backend）

### 3.1 新增模块

```text
app/services/ai_job/
  __init__.py
  runner.py          # schedule + execute_with_session 辅助
  statuses.py        # PENDING/RUNNING/SUCCEEDED/FAILED 常量
app/services/mixins/ 或直接放在 ai_job/
  project_access.py  # require_project_for_owner(db, user, project_id)
```

不强制一个巨型泛型基类绑死 ORM；采用 **薄共享函数 + 各 Service 变薄**：

| 共享能力 | 位置 |
|----------|------|
| owner 项目校验 | `require_owned_project` |
| 安全错误消息截断 | `safe_error_message(exc)` |
| 后台执行包装 | `run_in_background(session_factory, fn)` |
| 状态常量 | `AiJobStatus` |

各 `*Service.create` 统一调用包装；list/get 模式可保留在各 Service（已很短），或抽 `list_page(repo, …)` 小函数。

**本阶段不合并七张表为一张 `ai_jobs`**（迁移面过大）；抽象停在代码层。

### 3.2 LLM Provider 小整理（可选同阶段）

`OpenAICompatibleProvider` 七段 chat 调用抽 `_chat_json(system, user) -> dict`，减少复制。不改变 Prompt 语义。

---

## 4. 工作流公共层（Frontend）

### 4.1 目录结构

```text
frontend/src/
  pages/
    ProjectDetailPage.tsx          # shell: load project + Tabs
    project-detail/
      ProjectInfoTab.tsx
      RequirementAnalysisTab.tsx   # thin config wrappers
      TechnicalPlanTab.tsx
      CodeGenerationTab.tsx
      TestGenerationTab.tsx
      CodeReviewTab.tsx
      DebugSessionTab.tsx
      DevelopmentMetricsTab.tsx
  components/workflow/
    WorkflowPanel.tsx              # 列表 + 详情槽 + 状态 Tag
    useWorkflowPolling.ts          # create 后 poll getUntilTerminal
    StatusTag.tsx
  components/repo/
    RepoFilePicker.tsx             # tree + multi-select
  api/
    repo.ts                        # tree + file
    … existing APIs + status union + selected_files
```

### 4.2 `useWorkflowPolling`

```ts
pollUntilTerminal({ get, id, intervalMs=1500, maxAttempts=80 })
// terminal: succeeded | failed
// returns final record or throws PollTimeoutError
```

### 4.3 懒加载

- 仅「项目信息」随详情页加载。
- 各 AI Tab：`Tabs` 的 `activeKey` 变化或 `destroyInactiveTabPane` + 子组件 `useEffect` 首次激活时 `list*`。

### 4.4 状态展示

Tag 颜色：`pending` 默认 / `running` 处理中 / `succeeded` 绿 / `failed` 红。

---

## 5. 只读仓库上下文

### 5.1 配置常量（`app/core/repo_limits.py` 或 settings）

| 项 | 默认 |
|----|------|
| 树最大深度 | 6 |
| 树最大条目 | 500 |
| 单文件最大字节 | 256 KiB |
| 单次附带文件数 | 20 |
| 单次附带合计字节 | 512 KiB |
| 忽略目录名 | `.git`, `node_modules`, `.venv`, `dist`, `__pycache__`, … |
| 二进制扩展名黑名单 | `.png`, `.jpg`, `.exe`, `.dll`, `.woff`, … |

### 5.2 路径安全

```text
root = Path(repo_path).resolve()
target = (root / relative_path).resolve()
assert target == root or root in target.parents
```

拒绝 `..`、绝对路径输入、symlink 逃逸（resolve 后复检）。Windows 与 POSIX 均用 `Path.resolve()`。

### 5.3 API

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/v1/projects/{project_id}/repo/tree` | Query 可选 `max_depth`（封顶） |
| GET | `/api/v1/projects/{project_id}/repo/file` | Query `path` 相对路径 |

**Tree 节点：**

```json
{
  "path": "backend/app/main.py",
  "name": "main.py",
  "is_dir": false,
  "size": 1234
}
```

返回 `{ "root": "<repo_path display>", "entries": [ ... ] }`（扁平列表或嵌套树二选一；**采用扁平列表 + `path` 前缀**，前端更好建树）。

**File：**

```json
{ "path": "...", "content": "...", "size": 1234, "truncated": false }
```

本阶段超限：**拒绝**（400 `file_too_large`），不截断。

错误码：`repo_not_configured` | `repo_unavailable` | `path_outside_repo` | `path_not_file` | `file_too_large` | `binary_file_not_allowed` | `file_read_failed`

### 5.4 创建请求扩展字段

对 **technical-plans / code-generations / test-generations / code-reviews / debug-sessions** 的 Create schema 增加：

```python
selected_files: list[str] = Field(default_factory=list, max_length=20)
```

- 相对路径；去空白；去重保序。
- 持久化：各表新增可空列 `selected_files_json` JSON（路径列表快照），便于详情回显。  
  - SQLite：`init_db` / `create_all` 覆盖本地；Postgres：Alembic 新 revision。

**需求分析、研发度量**：本阶段 **不**加 `selected_files`（REQ-REPO-014）。

### 5.5 Prompt 拼装

在 worker `build_context` 末尾追加：

```text
--- Repository Files ---
### path/to/a.py
```
<content>
```

### path/to/b.ts
...
```

读取失败（不存在/越权/过大/二进制）→ 整单 `failed`，`error_message` 指明路径与原因。

预校验：create 时可只校验路径字符串形式；**真实读文件放在 worker**，与异步一致。可选 create 时快速 `resolve` 存在性——为减少无效排队，**create 阶段做路径安全解析与存在性检查**；内容读取仍在 worker（避免请求线程读大文件过久，但小文件预检可接受）。折中：**create 校验 path 安全与数量上限；worker 读内容**。若 create 时发现 path outside → 400，不建记录。

### 5.6 Frontend RepoFilePicker

- 调用 tree API；Tree 多选文件（不可选目录）。
- 将 `selected_files: string[]` 并入 create payload。
- `repo` 不可用时 Alert + 禁用选择器。

---

## 6. 数据库与迁移

1. 七类相关表中需附带文件的五类：加 `selected_files_json` JSON NULL。  
2. `status` 列无需 DDL 变更（已是 String）。  
3. Alembic：`xxxx_phase11_selected_files.py`。  
4. `scripts/init_db.py`：继续 `create_all` / 文档说明 SQLite 用户重启即可；若已有旧 SQLite 文件缺列，init 脚本增加简单 `ALTER` 或提示删除 db（实施时选 **兼容 ALTER IF 缺列**，与现有 init 风格对齐）。

---

## 7. 依赖

- **不新增** Python/Node 强制依赖。  
- Redis：**仍不接入**业务。  
- 可选：无。

---

## 8. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 进程重启丢失未跑完的 pending | 文档说明；后续可加启动扫描 |
| SQLite 多线程写锁 | 后台短事务；测试用 StaticPool |
| Prompt 过大 | 文件数/合计字节硬限制 |
| 路径穿越 | resolve + root 前缀校验 + 测试 |
| TestClient 与 BackgroundTasks | 用官方 TestClient；断言终态 |

---

## 9. 明确不做

- Celery / Redis Queue  
- SSE/WebSocket  
- 写回仓库  
- 合并七表  
- 取消进行中的 LLM HTTP  

---

## 10. 实施顺序（对应 tasks）

1. 状态枚举 + 异步 runner 骨架 + 一类工作流试点（建议 **code-generations**）  
2. 推广到其余六类 + 测例适配  
3. Repo service/API + 安全测试  
4. Create schema / 列 / Prompt 注入（五类）  
5. Frontend：拆分 + polling + RepoFilePicker + 懒加载  
6. README + 全量 pytest  

请确认本 `design.md`。确认后我将生成 `tasks.md`；你回复「开始执行」后才改代码。
