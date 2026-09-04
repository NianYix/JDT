# AI Engineering Copilot — Phase 9 Requirements（AI Debugging）

> 前置：Phase 1–8 已完成（含 AI Code Review）  
> 目标：在 Project 下交付「AI 调试辅助」最小可用闭环  
> 状态：待确认

## 1. 背景与目标

七大能力中，第六个 AI 场景：**AI Debugging**。

在已有编码、测试与审查能力之上，交付链路：

1. 用户进入某个 Project  
2. 描述问题现象（错误信息、堆栈、复现步骤等），可选关联**已成功的代码审查**或 **AI 编码记录**，或粘贴日志/代码上下文  
3. 调用 LLM 生成结构化调试分析（根因假设、排查步骤、修复建议）  
4. 结果落库并在 Frontend 展示  

仍不引入 LangChain / LangGraph；复用既有 LLM Provider 基础设施。

**本阶段「调试」指生成可审阅的排查与修复建议，不远程 attach 调试器、不向 `repo_path` 写入文件、不自动执行修复。**

## 1.1 In Scope

- `DebugSession`（或同名）业务实体，归属 `Project`
- 可选关联 `code_review_id`（引用某次成功的代码审查）
- 可选关联 `code_generation_id`（引用某次成功的 AI 编码记录）
- 必填 `problem_description`（问题/错误描述）
- 可选 `context_text`（堆栈、日志、相关代码片段）
- API：创建分析、列表、详情（按 Project）
- Service：组装 Prompt、调用 LLM、解析 JSON、持久化
- 扩展 `LLMProvider.debug_issue(context)`（或等价命名）
- Frontend：项目详情页增加「AI 调试」Tab
- pytest：Mock LLM，不依赖真实 Key
- 复用 `LLM_*` 配置与 `get_llm_provider`

## 1.2 Out of Scope

- LangChain / LangGraph / 多 Agent 编排
- Development Metrics（后续阶段）
- **远程调试器、断点、进程 attach、自动执行修复**
- **向 `repo_path` 写文件、扫描本地代码仓**
- 日志采集 Agent、APM 集成（Sentry/Datadog 等）
- 流式 SSE（本阶段同步）
- 多轮对话 / Chat 会话历史（本阶段单次请求）
- 文件上传；本阶段纯文本
- 自动 rerun 测试验证修复

---

## 2. 功能需求（EARS）

### 2.1 数据与归属

**REQ-DB-001**  
WHEN 已认证用户对其拥有的 Project 提交 AI 调试请求时，THE SYSTEM SHALL 创建一条归属该 Project 的调试会话记录。

**REQ-DB-002**  
WHEN 用户请求不属于自己的 Project 下的调试资源时，THE SYSTEM SHALL 返回 404（与 Phase 2 越权策略一致）。

**REQ-DB-003**  
THE SYSTEM SHALL 至少持久化：问题描述、可选关联审查/编码 ID、补充上下文、结构化结果（JSON）、状态、模型信息、创建/更新时间、错误信息（失败时）。

### 2.2 输入校验

**REQ-DB-004**  
WHEN 用户提交创建请求时，THE SYSTEM SHALL 要求 `problem_description` 去空白后非空；否则返回 422。

**REQ-DB-005**  
WHEN 用户提供 `code_review_id` 时，THE SYSTEM SHALL 校验该记录属于同一 Project 且 `status=succeeded`；否则返回 400，错误码 `invalid_code_review`。

**REQ-DB-006**  
WHEN 用户提供 `code_generation_id` 时，THE SYSTEM SHALL 校验该记录属于同一 Project 且 `status=succeeded`；否则返回 400，错误码 `invalid_code_generation`。

**REQ-DB-007**  
THE SYSTEM SHALL 允许仅提供 `problem_description` 发起调试分析（两个 FK 均可为空）。

### 2.3 分析执行

**REQ-DB-008**  
WHEN 输入校验通过且 LLM 可用时，THE SYSTEM SHALL 调用 LLM Provider 生成结构化调试分析。

**REQ-DB-009**  
WHEN LLM 调用成功时，THE SYSTEM SHALL 将结果解析为约定结构并保存，状态标记为 `succeeded`。

**REQ-DB-010**  
WHEN LLM 调用失败或返回无法解析的内容时，THE SYSTEM SHALL 保存失败原因，状态标记为 `failed`，且不得静默丢弃错误。

**REQ-DB-011**  
WHEN 未配置可用的 LLM Key 时，THE SYSTEM SHALL 返回明确业务错误（如 503），且**不创建**落库记录（与 Phase 4–8 一致）。

**REQ-DB-012**  
THE SYSTEM SHALL 支持同步完成一次分析（请求内等待 LLM 返回）；异步队列本阶段不做。

### 2.4 结构化结果（最小字段）

**REQ-DB-013**  
THE SYSTEM SHALL 让分析结果至少包含以下字段（允许后续扩展）：

- `summary`：问题摘要  
- `root_cause_analysis`：根因分析说明  
- `likely_causes`：可能原因列表，每项含 `hypothesis`、`confidence`（如 high/medium/low）、`evidence`  
- `debugging_steps`：建议排查步骤列表  
- `fix_suggestions`：修复建议列表，每项含 `description`、`content`（建议代码或命令，可为空）  
- `verification_steps`：验证修复的步骤列表  
- `prevention_notes`：预防类似问题的说明  
- `open_questions`：待澄清问题  

### 2.5 Prompt 上下文

**REQ-DB-014**  
WHEN 关联了成功的代码审查时，THE SYSTEM SHALL 将审查 `result_json`（或 `review_scope` 兜底）纳入 LLM 上下文。

**REQ-DB-015**  
WHEN 关联了成功的 AI 编码记录时，THE SYSTEM SHALL 将编码 `result_json`（或 `task_description` 兜底）纳入 LLM 上下文。

**REQ-DB-016**  
WHEN 提供了 `context_text` 时，THE SYSTEM SHALL 将其作为日志/堆栈/代码上下文一并传入 LLM。

**REQ-DB-017**  
THE SYSTEM SHALL 将 `problem_description` 作为问题主输入写入 Prompt。

### 2.6 API

**REQ-DB-018**  
THE SYSTEM SHALL 提供：

- `POST /api/v1/projects/{project_id}/debug-sessions`  
- `GET /api/v1/projects/{project_id}/debug-sessions`（分页）  
- `GET /api/v1/projects/{project_id}/debug-sessions/{id}`  

**REQ-DB-019**  
THE SYSTEM SHALL 继续使用 API / Service / Repository 分层，并复用 JWT 鉴权。

### 2.7 Frontend

**REQ-DB-020**  
WHEN 用户打开项目详情页时，THE SYSTEM SHALL 在 Tabs 中提供「AI 调试」入口。

**REQ-DB-021**  
THE SYSTEM SHALL 提供：问题描述表单、可选代码审查/编码记录下拉（仅 `succeeded`）、可选日志/堆栈文本框、提交按钮、历史列表、结果展示。

**REQ-DB-022**  
WHEN 分析成功时，THE SYSTEM SHALL 以可读方式展示根因分析、可能原因、排查步骤、修复建议（含代码块）及验证步骤。

### 2.8 配置与安全

**REQ-DB-023**  
THE SYSTEM SHALL 复用 Phase 4 的 `LLM_*` 环境变量配置。

**REQ-DB-024**  
THE SYSTEM SHALL NOT 将 API Key 暴露给前端或提交到 Git。

---

## 3. 非功能需求

**REQ-NFR-001**  
LLM 访问 SHALL 通过扩展既有 Provider 接口实现。

**REQ-NFR-002**  
pytest SHALL Mock Provider，保证无 Key 时测试全绿。

**REQ-NFR-003**  
本阶段 SHALL 不引入 LangChain/LangGraph。

**REQ-NFR-004**  
Alembic 迁移 SHALL 为 `debug_sessions` 表提供升级路径；SQLite 本地开发通过 `init_db` 可建表。

---

## 4. 验收标准

| ID | 验收项 | 通过条件 |
|----|--------|----------|
| AC-01 | 创建分析 | 登录用户可对本人 Project 提交问题描述并生成记录 |
| AC-02 | 关联审查/编码 | 可选 FK；无效 ID → 400 |
| AC-03 | 成功结果 | Mock/真实 LLM 成功时可见根因与修复建议 |
| AC-04 | 失败可观测 | Key 缺失 → 503 无落库；调用失败 → 201 + `failed` |
| AC-05 | 隔离 | 无法读写他人 Project 的调试记录 |
| AC-06 | Frontend | 项目详情「AI 调试」Tab 可提交并查看结果 |
| AC-07 | 测试 | pytest 全绿（含 Mock LLM） |
| AC-08 | 不执行修复 | 无写盘、无远程调试逻辑 |
| AC-09 | 无 Agent 框架 | 依赖中无 langchain/langgraph |

---

## 5. 待确认默认假设

1. **实体命名**：表 `debug_sessions`，模型 `DebugSession`；API 路径 `debug-sessions`。  
2. **首个 Provider**：OpenAI 兼容 HTTP API，方法名 `debug_issue(context: str)`。  
3. **执行模式**：**同步**请求内完成。  
4. **输入**：`problem_description` 必填；`code_review_id`、`code_generation_id`、`context_text` 均可选（两个 FK 可同时为空，也可只填其一）。  
5. **历史**：保留多次记录（列表 + 详情），不做 diff。  
6. **Frontend**：Project 详情 Tabs 增加第七项「AI 调试」。  
7. **likely_causes.confidence**：schema 层为字符串，LLM 返回 high/medium/low 等自由文本。  
8. **不自动修复**：明确排除写盘与远程调试。

请确认本 Requirements（可回「确认」或修改假设）。确认后生成 `design.md` 与 `tasks.md`。
