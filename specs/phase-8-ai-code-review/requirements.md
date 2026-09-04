# AI Engineering Copilot — Phase 8 Requirements（AI Code Review）

> 前置：Phase 1–7 已完成（含 Automated Testing）  
> 目标：在 Project 下交付「AI 代码审查」最小可用闭环  
> 状态：待确认

## 1. 背景与目标

七大能力中，第五个 AI 场景：**AI Code Review**。

在已有编码与测试建议能力之上，交付链路：

1. 用户进入某个 Project  
2. 描述审查范围（如「审查登录 API 实现」），可选关联**已成功的 AI 编码记录**，或粘贴待审代码片段  
3. 调用 LLM 生成结构化审查报告（问题、建议、优劣点）  
4. 结果落库并在 Frontend 展示  

仍不引入 LangChain / LangGraph；复用既有 LLM Provider 基础设施。

**本阶段「代码审查」指生成可审阅的审查报告与修改建议，不自动改代码、不向 `repo_path` 写入文件、不扫描本地仓库。**

## 1.1 In Scope

- `CodeReview`（或同名）业务实体，归属 `Project`
- 可选关联 `code_generation_id`（引用某次成功的 AI 编码记录）
- 必填 `review_scope`（审查范围/目标描述）
- 可选 `context_text`（待审代码片段、PR 说明等）
- API：创建审查、列表、详情（按 Project）
- Service：组装 Prompt、调用 LLM、解析 JSON、持久化
- 扩展 `LLMProvider.review_code(context)`（或等价命名）
- Frontend：项目详情页增加「代码审查」Tab
- pytest：Mock LLM，不依赖真实 Key
- 复用 `LLM_*` 配置与 `get_llm_provider`

## 1.2 Out of Scope

- LangChain / LangGraph / 多 Agent 编排
- AI Debugging、Development Metrics（后续阶段）
- **自动应用修改、向 `repo_path` 写文件**
- **扫描本地代码仓、对接 GitHub PR API**
- 静态分析工具集成（Ruff、ESLint、Sonar 等）本阶段不做
- 流式 SSE（本阶段同步）
- 多轮对话 / Chat 会话历史（本阶段单次请求）
- 文件上传；本阶段纯文本
- 审批流、多人 Review 协作

---

## 2. 功能需求（EARS）

### 2.1 数据与归属

**REQ-CR-001**  
WHEN 已认证用户对其拥有的 Project 提交代码审查请求时，THE SYSTEM SHALL 创建一条归属该 Project 的审查记录。

**REQ-CR-002**  
WHEN 用户请求不属于自己的 Project 下的审查资源时，THE SYSTEM SHALL 返回 404（与 Phase 2 越权策略一致）。

**REQ-CR-003**  
THE SYSTEM SHALL 至少持久化：审查范围描述、可选关联编码 ID、补充上下文、结构化结果（JSON）、状态、模型信息、创建/更新时间、错误信息（失败时）。

### 2.2 输入校验

**REQ-CR-004**  
WHEN 用户提交创建请求时，THE SYSTEM SHALL 要求 `review_scope` 去空白后非空；否则返回 422。

**REQ-CR-005**  
WHEN 用户提供 `code_generation_id` 时，THE SYSTEM SHALL 校验该记录属于同一 Project 且 `status=succeeded`；否则返回 400，错误码 `invalid_code_generation`。

**REQ-CR-006**  
THE SYSTEM SHALL 允许仅提供 `review_scope`（不关联编码记录、无补充上下文）发起审查。

### 2.3 审查执行

**REQ-CR-007**  
WHEN 输入校验通过且 LLM 可用时，THE SYSTEM SHALL 调用 LLM Provider 生成结构化审查报告。

**REQ-CR-008**  
WHEN LLM 调用成功时，THE SYSTEM SHALL 将结果解析为约定结构并保存，状态标记为 `succeeded`。

**REQ-CR-009**  
WHEN LLM 调用失败或返回无法解析的内容时，THE SYSTEM SHALL 保存失败原因，状态标记为 `failed`，且不得静默丢弃错误。

**REQ-CR-010**  
WHEN 未配置可用的 LLM Key 时，THE SYSTEM SHALL 返回明确业务错误（如 503），且**不创建**落库记录（与 Phase 4–7 一致）。

**REQ-CR-011**  
THE SYSTEM SHALL 支持同步完成一次审查（请求内等待 LLM 返回）；异步队列本阶段不做。

### 2.4 结构化结果（最小字段）

**REQ-CR-012**  
THE SYSTEM SHALL 让审查结果至少包含以下字段（允许后续扩展）：

- `summary`：审查摘要  
- `overall_assessment`：总体评价（文字说明，可含严重级别倾向）  
- `issues`：问题列表，每项含 `severity`（如 critical/major/minor/info）、`location`（文件或模块）、`category`（security/performance/style/logic 等）、`description`、`suggestion`  
- `strengths`：优点列表  
- `security_notes`：安全相关说明  
- `performance_notes`：性能相关说明  
- `maintainability_notes`：可维护性说明  
- `suggested_fixes`：修改建议列表，每项含 `path`、`description`、`content`（建议代码片段，可为空）  
- `open_questions`：待澄清问题  

### 2.5 Prompt 上下文

**REQ-CR-013**  
WHEN 关联了成功的 AI 编码记录时，THE SYSTEM SHALL 将编码结果的 `result_json`（或任务描述兜底）纳入 LLM 上下文。

**REQ-CR-014**  
WHEN 提供了 `context_text` 时，THE SYSTEM SHALL 将其作为待审代码或补充说明一并传入 LLM。

**REQ-CR-015**  
THE SYSTEM SHALL 将 `review_scope` 作为审查目标的主输入写入 Prompt。

### 2.6 API

**REQ-CR-016**  
THE SYSTEM SHALL 提供：

- `POST /api/v1/projects/{project_id}/code-reviews`  
- `GET /api/v1/projects/{project_id}/code-reviews`（分页）  
- `GET /api/v1/projects/{project_id}/code-reviews/{id}`  

**REQ-CR-017**  
THE SYSTEM SHALL 继续使用 API / Service / Repository 分层，并复用 JWT 鉴权。

### 2.7 Frontend

**REQ-CR-018**  
WHEN 用户打开项目详情页时，THE SYSTEM SHALL 在 Tabs 中提供「代码审查」入口。

**REQ-CR-019**  
THE SYSTEM SHALL 提供：审查范围表单、可选 AI 编码记录下拉（仅 `succeeded`）、可选代码/说明文本框、提交按钮、历史列表、结果展示。

**REQ-CR-020**  
WHEN 审查成功时，THE SYSTEM SHALL 以可读方式展示摘要、问题列表（含严重级别）、优点及建议修改（含代码块）。

### 2.8 配置与安全

**REQ-CR-021**  
THE SYSTEM SHALL 复用 Phase 4 的 `LLM_*` 环境变量配置。

**REQ-CR-022**  
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
Alembic 迁移 SHALL 为 `code_reviews` 表提供升级路径；SQLite 本地开发通过 `init_db` 可建表。

---

## 4. 验收标准

| ID | 验收项 | 通过条件 |
|----|--------|----------|
| AC-01 | 创建审查 | 登录用户可对本人 Project 提交审查范围并生成记录 |
| AC-02 | 关联编码 | 可选关联 succeeded 编码记录；无效 ID → 400 |
| AC-03 | 成功结果 | Mock/真实 LLM 成功时可见问题列表与建议 |
| AC-04 | 失败可观测 | Key 缺失 → 503 无落库；调用失败 → 201 + `failed` |
| AC-05 | 隔离 | 无法读写他人 Project 的审查记录 |
| AC-06 | Frontend | 项目详情「代码审查」Tab 可提交并查看结果 |
| AC-07 | 测试 | pytest 全绿（含 Mock LLM） |
| AC-08 | 不改盘 | 无文件写入与自动修复逻辑 |
| AC-09 | 无 Agent 框架 | 依赖中无 langchain/langgraph |

---

## 5. 待确认默认假设

1. **实体命名**：表 `code_reviews`，模型 `CodeReview`；API 路径 `code-reviews`。  
2. **首个 Provider**：OpenAI 兼容 HTTP API，方法名 `review_code(context: str)`。  
3. **执行模式**：**同步**请求内完成。  
4. **输入**：`review_scope` 必填；`code_generation_id`、`context_text` 可选。  
5. **历史**：保留多次审查记录（列表 + 详情），不做 diff。  
6. **Frontend**：Project 详情 Tabs 增加第六项「代码审查」。  
7. **问题 severity**：schema 层为字符串，LLM 自由返回 critical/major/minor/info 等。  
8. **不自动修复**：明确排除写盘与自动 apply patch。

请确认本 Requirements（可回「确认」或修改假设）。确认后生成 `design.md` 与 `tasks.md`。
