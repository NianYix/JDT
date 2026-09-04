# AI Engineering Copilot — Phase 7 Requirements（Automated Testing）

> 前置：Phase 1–6 已完成（含 Requirement Analysis、Technical Planning、AI Coding）  
> 目标：在 Project 下交付「自动化测试建议」最小可用闭环  
> 状态：待确认

## 1. 背景与目标

七大能力中，第四个 AI 场景：**Automated Testing**。

在已有编码建议能力之上，交付链路：

1. 用户进入某个 Project  
2. 描述待测目标（如「用户登录 API 的单元测试」），可选关联**已成功的 AI 编码记录**或补充上下文  
3. 调用 LLM 生成结构化测试方案（用例 + 测试代码建议）  
4. 结果落库并在 Frontend 展示  

仍不引入 LangChain / LangGraph；复用既有 LLM Provider 基础设施。

**本阶段「自动化测试」指生成可审阅的测试用例与测试代码建议，不在本地执行 pytest、不向 `repo_path` 写入文件。**

## 1.1 In Scope

- `TestGeneration`（或同名）业务实体，归属 `Project`
- 可选关联 `code_generation_id`（引用某次成功的 AI 编码记录）
- 必填 `target_description`（待测目标描述）
- 可选 `context_text`（补充说明、被测代码片段等）
- API：创建生成、列表、详情（按 Project）
- Service：组装 Prompt、调用 LLM、解析 JSON、持久化
- 扩展 `LLMProvider.generate_tests(context)`（或等价命名）
- Frontend：项目详情页增加「自动化测试」Tab
- pytest：Mock LLM，不依赖真实 Key
- 复用 `LLM_*` 配置与 `get_llm_provider`

## 1.2 Out of Scope

- LangChain / LangGraph / 多 Agent 编排
- Code Review、Debugging、Metrics（后续阶段）
- **在 `repo_path` 执行 pytest / 写入测试文件**
- **扫描或索引本地代码仓**
- CI/CD 集成、测试覆盖率采集、Allure 报告
- 流式 SSE（本阶段同步）
- 多轮对话 / Chat 会话历史（本阶段单次请求）
- 文件上传；本阶段纯文本
- 自动修复失败用例

---

## 2. 功能需求（EARS）

### 2.1 数据与归属

**REQ-TG-001**  
WHEN 已认证用户对其拥有的 Project 提交自动化测试生成请求时，THE SYSTEM SHALL 创建一条归属该 Project 的测试生成记录。

**REQ-TG-002**  
WHEN 用户请求不属于自己的 Project 下的测试生成资源时，THE SYSTEM SHALL 返回 404（与 Phase 2 越权策略一致）。

**REQ-TG-003**  
THE SYSTEM SHALL 至少持久化：待测目标描述、可选关联编码 ID、补充上下文、结构化结果（JSON）、状态、模型信息、创建/更新时间、错误信息（失败时）。

### 2.2 输入校验

**REQ-TG-004**  
WHEN 用户提交创建请求时，THE SYSTEM SHALL 要求 `target_description` 去空白后非空；否则返回 422。

**REQ-TG-005**  
WHEN 用户提供 `code_generation_id` 时，THE SYSTEM SHALL 校验该记录属于同一 Project 且 `status=succeeded`；否则返回 400，错误码 `invalid_code_generation`。

**REQ-TG-006**  
THE SYSTEM SHALL 允许仅提供 `target_description`（不关联编码记录、无补充上下文）发起生成。

### 2.3 生成执行

**REQ-TG-007**  
WHEN 输入校验通过且 LLM 可用时，THE SYSTEM SHALL 调用 LLM Provider 生成结构化测试建议。

**REQ-TG-008**  
WHEN LLM 调用成功时，THE SYSTEM SHALL 将结果解析为约定结构并保存，状态标记为 `succeeded`。

**REQ-TG-009**  
WHEN LLM 调用失败或返回无法解析的内容时，THE SYSTEM SHALL 保存失败原因，状态标记为 `failed`，且不得静默丢弃错误。

**REQ-TG-010**  
WHEN 未配置可用的 LLM Key 时，THE SYSTEM SHALL 返回明确业务错误（如 503），且**不创建**落库记录（与 Phase 4–6 一致）。

**REQ-TG-011**  
THE SYSTEM SHALL 支持同步完成一次生成（请求内等待 LLM 返回）；异步队列本阶段不做。

### 2.4 结构化结果（最小字段）

**REQ-TG-012**  
THE SYSTEM SHALL 让生成结果至少包含以下字段（允许后续扩展）：

- `summary`：测试方案摘要  
- `testing_strategy`：整体测试策略说明  
- `test_cases`：用例列表，每项含 `name`、`type`（如 unit/integration/e2e）、`description`、`steps`、`expected`  
- `test_files`：建议测试文件列表，每项含 `path`、`language`、`description`、`content`（测试代码正文）  
- `fixtures_and_mocks`：夹具与 Mock 建议列表  
- `coverage_notes`：覆盖范围说明列表  
- `risks`：风险与注意事项  
- `open_questions`：待澄清问题  

### 2.5 Prompt 上下文

**REQ-TG-013**  
WHEN 关联了成功的 AI 编码记录时，THE SYSTEM SHALL 将编码结果的 `result_json`（或任务描述兜底）纳入 LLM 上下文。

**REQ-TG-014**  
WHEN 提供了 `context_text` 时，THE SYSTEM SHALL 将其作为补充上下文一并传入 LLM。

**REQ-TG-015**  
THE SYSTEM SHALL 将 `target_description` 作为待测目标的主输入写入 Prompt。

### 2.6 API

**REQ-TG-016**  
THE SYSTEM SHALL 提供：

- `POST /api/v1/projects/{project_id}/test-generations`  
- `GET /api/v1/projects/{project_id}/test-generations`（分页）  
- `GET /api/v1/projects/{project_id}/test-generations/{id}`  

**REQ-TG-017**  
THE SYSTEM SHALL 继续使用 API / Service / Repository 分层，并复用 JWT 鉴权。

### 2.7 Frontend

**REQ-TG-018**  
WHEN 用户打开项目详情页时，THE SYSTEM SHALL 在 Tabs 中提供「自动化测试」入口。

**REQ-TG-019**  
THE SYSTEM SHALL 提供：待测目标表单、可选 AI 编码记录下拉（仅 `succeeded`）、可选补充上下文、提交按钮、历史列表、结果展示。

**REQ-TG-020**  
WHEN 生成成功时，THE SYSTEM SHALL 以可读方式展示用例列表、测试策略、建议测试文件（含代码块）及覆盖说明。

### 2.8 配置与安全

**REQ-TG-021**  
THE SYSTEM SHALL 复用 Phase 4 的 `LLM_*` 环境变量配置。

**REQ-TG-022**  
THE SYSTEM SHALL NOT 将 API Key 暴露给前端或提交到 Git。

---

## 3. 非功能需求

**REQ-NFR-001**  
LLM 访问 SHALL 通过扩展既有 Provider 接口实现，与 `analyze_requirements`、`plan_technical`、`generate_code` 共用客户端。

**REQ-NFR-002**  
pytest SHALL Mock Provider，保证无 Key 时测试全绿。

**REQ-NFR-003**  
本阶段 SHALL 不引入 LangChain/LangGraph。

**REQ-NFR-004**  
Alembic 迁移 SHALL 为 `test_generations` 表提供升级路径；SQLite 本地开发通过 `init_db` 可建表。

---

## 4. 验收标准

| ID | 验收项 | 通过条件 |
|----|--------|----------|
| AC-01 | 创建生成 | 登录用户可对本人 Project 提交待测目标并生成记录 |
| AC-02 | 关联编码 | 可选关联 succeeded 编码记录；无效 ID → 400 |
| AC-03 | 成功结果 | Mock/真实 LLM 成功时可见用例与测试代码片段 |
| AC-04 | 失败可观测 | Key 缺失 → 503 无落库；调用失败 → 201 + `failed` |
| AC-05 | 隔离 | 无法读写他人 Project 的测试生成记录 |
| AC-06 | Frontend | 项目详情「自动化测试」Tab 可提交并查看结果 |
| AC-07 | 测试 | pytest 全绿（含 Mock LLM） |
| AC-08 | 不执行/不写盘 | 无 pytest 执行与文件写入逻辑 |
| AC-09 | 无 Agent 框架 | 依赖中无 langchain/langgraph |

---

## 5. 待确认默认假设

1. **实体命名**：表 `test_generations`，模型 `TestGeneration`；API 路径 `test-generations`。  
2. **首个 Provider**：OpenAI 兼容 HTTP API，方法名 `generate_tests(context: str)`。  
3. **执行模式**：**同步**请求内完成。  
4. **输入**：`target_description` 必填；`code_generation_id`、`context_text` 可选。  
5. **历史**：保留多次生成记录（列表 + 详情），不做 diff。  
6. **Frontend**：Project 详情 Tabs 增加第五项「自动化测试」。  
7. **用例 type**：schema 层为字符串，LLM 返回 unit / integration / e2e 等自由文本。  
8. **不写盘、不跑测**：明确排除文件系统写入与 subprocess pytest。

请确认本 Requirements（可回「确认」或修改假设）。确认后生成 `design.md` 与 `tasks.md`。
