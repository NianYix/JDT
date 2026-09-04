# AI Engineering Copilot — Phase 6 Requirements（AI Coding）

> 前置：Phase 1–5 已完成（含 Requirement Analysis、Technical Planning）  
> 目标：在 Project 下交付「AI 编码建议」最小可用闭环  
> 状态：待确认

## 1. 背景与目标

七大能力中，第三个 AI 场景：**AI Coding**。

在已有需求分析与技术规划之上，交付链路：

1. 用户进入某个 Project  
2. 描述编码任务（如「实现用户登录 API」），可选关联**已成功的技术规划**或补充上下文  
3. 调用 LLM 生成结构化编码建议（含代码片段与文件建议）  
4. 结果落库并在 Frontend 展示  

仍不引入 LangChain / LangGraph；复用 Phase 4/5 的 LLM Provider 基础设施。

**本阶段「编码」指生成可审阅的代码建议与实现说明，不向磁盘写入、不修改 `repo_path` 指向的仓库。**

## 1.1 In Scope

- `CodeGeneration`（或同名）业务实体，归属 `Project`
- 可选关联 `technical_plan_id`（引用某次成功的技术规划）
- 必填 `task_description`（编码任务描述）
- 可选 `context_text`（补充约束、现有代码片段等）
- API：创建生成、列表、详情（按 Project）
- Service：组装 Prompt、调用 LLM、解析 JSON、持久化
- 扩展 `LLMProvider.generate_code(context)`（或等价命名）
- Frontend：项目详情页增加「AI 编码」Tab
- pytest：Mock LLM，不依赖真实 Key
- 复用 `LLM_*` 配置与 `get_llm_provider`

## 1.2 Out of Scope

- LangChain / LangGraph / 多 Agent 编排
- Automated Testing、Code Review、Debugging、Metrics（后续阶段）
- **向 `repo_path` 写入文件、执行 git、运行构建**
- **扫描或索引本地代码仓**
- 流式 SSE（本阶段同步）
- 多轮对话 / Chat 会话历史（本阶段单次请求）
- 文件上传（PDF/图片）；本阶段纯文本
- 代码 diff 应用、IDE 插件

---

## 2. 功能需求（EARS）

### 2.1 数据与归属

**REQ-CG-001**  
WHEN 已认证用户对其拥有的 Project 提交 AI 编码请求时，THE SYSTEM SHALL 创建一条归属该 Project 的编码生成记录。

**REQ-CG-002**  
WHEN 用户请求不属于自己的 Project 下的编码资源时，THE SYSTEM SHALL 返回 404（与 Phase 2 越权策略一致）。

**REQ-CG-003**  
THE SYSTEM SHALL 至少持久化：任务描述、可选关联规划 ID、补充上下文、结构化结果（JSON）、状态、模型信息、创建/更新时间、错误信息（失败时）。

### 2.2 输入校验

**REQ-CG-004**  
WHEN 用户提交创建请求时，THE SYSTEM SHALL 要求 `task_description` 去空白后非空；否则返回 422。

**REQ-CG-005**  
WHEN 用户提供 `technical_plan_id` 时，THE SYSTEM SHALL 校验该记录属于同一 Project 且 `status=succeeded`；否则返回 400，错误码 `invalid_technical_plan`。

**REQ-CG-006**  
THE SYSTEM SHALL 允许仅提供 `task_description`（不关联技术规划、无补充上下文）发起生成。

### 2.3 生成执行

**REQ-CG-007**  
WHEN 输入校验通过且 LLM 可用时，THE SYSTEM SHALL 调用 LLM Provider 生成结构化编码建议。

**REQ-CG-008**  
WHEN LLM 调用成功时，THE SYSTEM SHALL 将结果解析为约定结构并保存，状态标记为 `succeeded`。

**REQ-CG-009**  
WHEN LLM 调用失败或返回无法解析的内容时，THE SYSTEM SHALL 保存失败原因，状态标记为 `failed`，且不得静默丢弃错误。

**REQ-CG-010**  
WHEN 未配置可用的 LLM Key 时，THE SYSTEM SHALL 返回明确业务错误（如 503），且**不创建**落库记录（与 Phase 4/5 一致）。

**REQ-CG-011**  
THE SYSTEM SHALL 支持同步完成一次生成（请求内等待 LLM 返回）；异步队列本阶段不做。

### 2.4 结构化结果（最小字段）

**REQ-CG-012**  
THE SYSTEM SHALL 让生成结果至少包含以下字段（允许后续扩展）：

- `summary`：实现摘要  
- `approach`：实现思路说明  
- `files`：建议文件列表，每项含 `path`、`language`、`description`、`content`（代码正文）  
- `dependencies`：建议新增依赖（如 pip/npm 包名）  
- `implementation_steps`：实现步骤列表  
- `testing_notes`：测试建议  
- `risks`：风险与注意事项  
- `open_questions`：待澄清问题  

### 2.5 Prompt 上下文

**REQ-CG-013**  
WHEN 关联了成功的技术规划时，THE SYSTEM SHALL 将规划的 `result_json`（或兜底 `context_text`）纳入 LLM 上下文。

**REQ-CG-014**  
WHEN 提供了 `context_text` 时，THE SYSTEM SHALL 将其作为补充上下文一并传入 LLM。

**REQ-CG-015**  
THE SYSTEM SHALL 将 `task_description` 作为用户编码任务的主输入写入 Prompt。

### 2.6 API

**REQ-CG-016**  
THE SYSTEM SHALL 提供：

- `POST /api/v1/projects/{project_id}/code-generations`  
- `GET /api/v1/projects/{project_id}/code-generations`（分页）  
- `GET /api/v1/projects/{project_id}/code-generations/{id}`  

**REQ-CG-017**  
THE SYSTEM SHALL 继续使用 API / Service / Repository 分层，并复用 JWT 鉴权。

### 2.7 Frontend

**REQ-CG-018**  
WHEN 用户打开项目详情页时，THE SYSTEM SHALL 在 Tabs 中提供「AI 编码」入口。

**REQ-CG-019**  
THE SYSTEM SHALL 提供：任务描述表单、可选技术规划下拉（仅 `succeeded`）、可选补充上下文、提交按钮、历史列表、结果展示。

**REQ-CG-020**  
WHEN 生成成功时，THE SYSTEM SHALL 以可读方式展示摘要、步骤、建议文件（含代码块）及测试建议。

### 2.8 配置与安全

**REQ-CG-021**  
THE SYSTEM SHALL 复用 Phase 4 的 `LLM_*` 环境变量配置。

**REQ-CG-022**  
THE SYSTEM SHALL NOT 将 API Key 暴露给前端或提交到 Git。

---

## 3. 非功能需求

**REQ-NFR-001**  
LLM 访问 SHALL 通过扩展既有 Provider 接口实现，便于与 `analyze_requirements`、`plan_technical` 共用客户端。

**REQ-NFR-002**  
pytest SHALL Mock Provider，保证无 Key 时测试全绿。

**REQ-NFR-003**  
本阶段 SHALL 不引入 LangChain/LangGraph。

**REQ-NFR-004**  
Alembic 迁移 SHALL 为 `code_generations` 表提供升级路径；SQLite 本地开发通过 `init_db` 可建表。

---

## 4. 验收标准

| ID | 验收项 | 通过条件 |
|----|--------|----------|
| AC-01 | 创建生成 | 登录用户可对本人 Project 提交任务描述并生成记录 |
| AC-02 | 关联规划 | 可选关联 succeeded 技术规划；无效 ID → 400 |
| AC-03 | 成功结果 | Mock/真实 LLM 成功时可见结构化字段与代码片段 |
| AC-04 | 失败可观测 | Key 缺失 → 503 无落库；调用失败 → 201 + `failed` + 错误信息 |
| AC-05 | 隔离 | 无法读写他人 Project 的编码记录 |
| AC-06 | Frontend | 项目详情「AI 编码」Tab 可提交并查看结果 |
| AC-07 | 测试 | pytest 全绿（含 Mock LLM） |
| AC-08 | 不写盘 | 无任何向 `repo_path` 写文件的逻辑 |
| AC-09 | 无 Agent 框架 | 依赖中无 langchain/langgraph |

---

## 5. 待确认默认假设

1. **实体命名**：表 `code_generations`，模型 `CodeGeneration`；API 路径 `code-generations`。  
2. **首个 Provider**：OpenAI 兼容 HTTP API，方法名 `generate_code(context: str)`。  
3. **执行模式**：**同步**请求内完成。  
4. **输入**：`task_description` 必填；`technical_plan_id`、`context_text` 可选。  
5. **历史**：保留多次生成记录（列表 + 详情），不做版本 diff。  
6. **Frontend**：在现有 Project 详情 Tabs 增加第四项「AI 编码」。  
7. **代码展示**：Frontend 用 `<pre>` 或 Ant Design 代码块样式展示 `files[].content`，不做语法高亮库（除非已有依赖可复用）。  
8. **不写仓库**：明确排除任何文件系统写入与 git 操作。

请确认本 Requirements（可回「确认」或修改假设）。确认后生成 `design.md` 与 `tasks.md`。
