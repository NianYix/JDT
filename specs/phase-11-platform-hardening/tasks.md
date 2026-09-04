# AI Engineering Copilot — Phase 11 Tasks（平台硬化）

> 状态：已完成（2026-08-31）  
> 决策回放：进程内 BackgroundTasks；`pending→running→终态`；读文件失败整单 failed；技术规划挂文件选择器

## 进度总览

| ID | 任务 | 状态 |
|----|------|------|
| T1 | 状态常量与异步 runner 骨架 | 完成 |
| T2 | Code Generation 异步试点 | 完成 |
| T3 | 其余六类 AI 工作流异步化 | 完成 |
| T4 | 适配既有 pytest 异步语义 | 完成 |
| T5 | Repo 只读 Service + API + 安全测试 | 完成 |
| T6 | selected_files 字段 / 迁移 / Prompt 注入 | 完成 |
| T7 | Frontend 拆分 + 懒加载 + WorkflowPanel | 完成 |
| T8 | Frontend 轮询 + RepoFilePicker 接入 | 完成 |
| T9 | Provider `_chat_json` 小整理 | 完成 |
| T10 | README 更新 + 全量回归 | 完成 |

---

## T1 — 状态常量与异步 runner 骨架

- [ ] 新增 `app/services/ai_job/statuses.py`（`pending` / `running` / `succeeded` / `failed`）
- [ ] 新增 `app/services/ai_job/runner.py`：`schedule_ai_job(background_tasks, fn, *args)`；`with_worker_session(fn)` 打开独立 Session
- [ ] 新增 `require_owned_project`、`safe_error_message` 共享辅助
- [ ] 文档字符串标明：无 Redis；崩溃残留 `running` 本阶段不回收

**验收：** 模块可导入；无业务行为变更。

---

## T2 — Code Generation 异步试点

- [ ] `GenerationStatus`（及 Public）加入 `running`
- [ ] `CodeGenerationService.create`：落库 `pending` → `commit` → `BackgroundTasks` → 立即返回
- [ ] Worker：`running` → build context → LLM → `succeeded`/`failed`
- [ ] API `POST` 注入 `BackgroundTasks` 并下传 Service
- [ ] 单测：POST 后终态 succeeded；失败 Provider → failed

**验收：** 仅 code-generations 异步；其余类暂保持原状亦可，但优先尽快进入 T3。

---

## T3 — 其余六类 AI 工作流异步化

对以下 Service/API 套用与 T2 相同模式：

- [ ] requirement_analyses
- [ ] technical_plans
- [ ] test_generations
- [ ] code_reviews
- [ ] debug_sessions
- [ ] development_metrics

**验收：** 七类 create 均快速返回非终态记录，后台达终态。

---

## T4 — 适配既有 pytest

- [ ] 更新 `test_requirement_analyses` … `test_development_metrics` 等：不再假定「同步阻塞至成功才返回」的语义矛盾；以「请求结束后记录为 succeeded/failed」为准（TestClient 会跑完 BackgroundTasks）
- [ ] 至少一类增加「响应体初始可为 pending/running」的显式断言（若 TestClient 已跑完任务导致直接 succeeded，则改为断言终态字段完整 + worker 路径被覆盖）
- [ ] 全量 `pytest -q` 中与 AI 相关用例通过

**验收：** `cd backend && pytest -q` 相关失败清零。

---

## T5 — Repo 只读 Service + API

- [ ] `app/services/repo_service.py`：tree / read_file；limits；忽略目录；二进制黑名单
- [ ] 路径 `resolve` + root 前缀校验
- [ ] `app/api/v1/repo.py`：`GET .../repo/tree`、`GET .../repo/file`
- [ ] 挂到 `api/router`
- [ ] `tests/test_repo.py`：越权 404、未配置、路径穿越、超大文件、正常读写（用 tmp_path 作 repo_path）

**验收：** 安全用例全绿；合法树/文件可读。

---

## T6 — selected_files 与 Prompt 注入

- [ ] Create schema（plans / coding / testing / review / debug）增加 `selected_files: list[str]`
- [ ] 模型列 `selected_files_json` + Alembic revision + `init_db` 兼容
- [ ] create 阶段：数量/路径安全预校验（outside → 400，不建记录）
- [ ] worker：读文件；失败 → 整单 failed；成功则拼 `--- Repository Files ---`
- [ ] Public DTO 回显 `selected_files`（可选从 JSON 列读出）
- [ ] 测例：附带临时文件内容进入 Fake Provider 可见的 context（可通过 Fake 断言调用参数）

**验收：** 无文件行为兼容；有文件则注入；坏路径整单 failed 或 create 400。

---

## T7 — Frontend 拆分 + 懒加载

- [ ] 建立 `pages/project-detail/*` Tab 组件
- [ ] `components/workflow/WorkflowPanel.tsx`、`StatusTag.tsx`
- [ ] `ProjectDetailPage.tsx` 降为 shell（Tabs + 项目加载）
- [ ] AI Tab 首次激活再 `list*`

**验收：** 首屏不串行拉七类；页面可打开各 Tab。

---

## T8 — Frontend 轮询 + RepoFilePicker

- [ ] `useWorkflowPolling.ts`（间隔 ~1.5s，上限 ~80 次）
- [ ] 各 AI 创建改为：create → poll → 展示结果/错误
- [ ] `api/repo.ts` + `RepoFilePicker.tsx`
- [ ] Planning / Coding / Testing / Review / Debugging 表单提交 `selected_files`
- [ ] 类型：`status` 含 `running`；CreatePayload 含 `selected_files?`

**验收：** 手动：慢 LLM 下可见 running；配置 repo_path 可选文件并生成。

---

## T9 — Provider 小整理

- [ ] `OpenAICompatibleProvider` 抽 `_chat_json(system, user)`
- [ ] 七个能力方法改为调用该辅助；Prompt 文本不变

**验收：** 既有 Mock 测例仍通过（不测真实 LLM）。

---

## T10 — README 与回归

- [ ] 更新根 `README.md`：异步行为、轮询、`running`、repo API、安全限制、Out of Scope 仍成立项
- [ ] 修正「同步分析/生成」等过时表述
- [ ] `pytest -q` 全绿
- [ ] 手动清单：
  - [ ] 无 Docker SQLite 启动后 AI 创建仍可用
  - [ ] 项目信息配置本机目录 → 树可见
  - [ ] `../` 路径被拒
  - [ ] Tab 懒加载与轮询 UI

**验收：** 文档与实现一致；测试全绿。

---

## 依赖顺序

```text
T1 → T2 → T3 → T4
         ↘
T5 → T6 ──→ T8
T7 ───────→ T8 → T10
T9 可与 T3–T6 并行
```

## 不在本阶段 tasks 内

- Redis / Celery、SSE、写仓库、取消 LLM、合并七表、组织 RBAC
