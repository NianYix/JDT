# AI Engineering Copilot — Phase 5 Requirements（Technical Planning）

> 前置：Phase 1–4 已完成（含 Project、Requirement Analysis）  
> 目标：在 Project 下交付「技术规划」最小可用闭环  
> 状态：待确认

## 1. 背景与目标

七大能力中，第二个 AI 场景：**Technical Planning**。

在已有需求分析能力之上，交付链路：

1. 用户进入某个 Project  
2. 基于**已成功的需求分析**或**手动粘贴需求/上下文**发起技术规划  
3. 调用 LLM 生成结构化技术方案  
4. 结果落库并在 Frontend 展示  

仍不引入 LangChain / LangGraph；复用 Phase 4 的 LLM Provider 基础设施。

## 1.1 In Scope

- `TechnicalPlan`（或同名）业务实体，归属 `Project`
- 可选关联 `requirement_analysis_id`（引用某次成功的需求分析）
- API：创建规划、列表、详情（按 Project）
- Service：组装 Prompt（含需求分析结果或用户输入）、调用 LLM、解析 JSON、持久化
- Frontend：项目详情页增加「技术规划」区块（与需求分析并列）
- pytest：Mock LLM，不依赖真实 Key
- 复用 `LLM_*` 配置与 `get_llm_provider`

## 1.2 Out of Scope

- LangChain / LangGraph
- AI Coding、Automated Testing、Code Review、Debugging、Metrics
- 自动生成代码文件 / 改仓库
- 流式 SSE（本阶段同步）
- 多方案对比投票、审批流
- 从 `repo_path` 自动扫描代码仓（本阶段仅用文本上下文）

---

## 2. 功能需求（EARS）

### 2.1 数据与归属

**REQ-TP-001**  
WHEN 已认证用户对其拥有的 Project 提交技术规划请求时，THE SYSTEM SHALL 创建一条归属该 Project 的规划记录。

**REQ-TP-002**  
WHEN 用户请求不属于自己的 Project 下的规划资源时，THE SYSTEM SHALL 返回 404。

**REQ-TP-003**  
THE SYSTEM SHALL 持久化：输入上下文摘要、可选 `requirement_analysis_id`、结构化结果 JSON、状态、模型信息、错误信息、创建/更新时间与创建人。

**REQ-TP-004**  
WHEN 请求携带 `requirement_analysis_id` 时，THE SYSTEM SHALL 校验该分析记录属于同一 Project 且 `status=succeeded`，否则返回 400/404（设计阶段固定一种）。

### 2.2 规划执行

**REQ-TP-005**  
WHEN 用户提交有效输入（关联成功需求分析 **或** 非空 `context_text`）时，THE SYSTEM SHALL 调用 LLM 生成结构化技术规划。

**REQ-TP-006**  
WHEN LLM 成功时，THE SYSTEM SHALL 保存 `status=succeeded` 与结构化结果。

**REQ-TP-007**  
WHEN LLM 失败或 JSON 无法解析时，THE SYSTEM SHALL 保存 `status=failed` 与 `error_message`（与 Phase 4 一致：失败仍落库）。

**REQ-TP-008**  
WHEN 未配置 LLM Key 时，THE SYSTEM SHALL 返回 503 `llm_not_configured` 且不写库。

**REQ-TP-009**  
THE SYSTEM SHALL 同步完成（请求内等待 LLM），不做队列。

### 2.3 结构化结果（最小字段）

**REQ-TP-010**  
THE SYSTEM SHALL 让规划结果至少包含：

- `summary`：技术方案摘要  
- `architecture_overview`：架构概览（文字）  
- `tech_stack`：推荐技术栈列表（如 `{name, reason}` 或字符串列表）  
- `modules`：模块划分列表（名称 + 职责）  
- `api_outline`：API 设计要点列表  
- `data_model_outline`：数据模型要点列表  
- `milestones`：实施里程碑列表  
- `dependencies`：外部依赖 / 基础设施  
- `risks_and_mitigations`：技术风险与缓解  
- `open_questions`：待澄清技术问题  

### 2.4 API

**REQ-TP-011**  
THE SYSTEM SHALL 提供：

- `POST /api/v1/projects/{project_id}/technical-plans`  
- `GET /api/v1/projects/{project_id}/technical-plans`（分页）  
- `GET /api/v1/projects/{project_id}/technical-plans/{id}`  

**REQ-TP-012**  
创建请求体 SHALL 支持：

- `requirement_analysis_id`（可选 UUID）  
- `context_text`（可选，补充说明；当无 analysis_id 时必填其一）

### 2.5 Frontend

**REQ-TP-013**  
WHEN 用户打开项目详情页时，THE SYSTEM SHALL 提供技术规划入口：可选择历史**成功**的需求分析，或补充文本，提交后展示结果与历史列表。

**REQ-TP-014**  
WHEN 规划失败时，THE SYSTEM SHALL 展示 `error_message` 与失败状态。

### 2.6 测试与工程

**REQ-TP-015**  
THE SYSTEM SHALL 提供 pytest：成功、失败落库、503、越权 404、非法 analysis_id。

**REQ-TP-016**  
THE SYSTEM SHALL 延续 API / Service / Repository 分层，不引入 Agent 框架。

---

## 3. 验收标准

| ID | 验收项 | 通过条件 |
|----|--------|----------|
| AC-01 | 基于需求分析创建 | 选 succeeded 分析可生成规划 |
| AC-02 | 纯文本创建 | 仅 context_text 可生成 |
| AC-03 | 失败可观测 | failed + error_message |
| AC-04 | 无 Key | 503 不写库 |
| AC-05 | 隔离 | 无法访问他人 Project 规划 |
| AC-06 | Frontend | 项目页可提交与查看 |
| AC-07 | 测试 | pytest 全绿 |
| AC-08 | 无 Agent | 无 langchain |

---

## 4. 待确认默认假设

1. **输入方式**：`requirement_analysis_id` **或** `context_text` 至少一项；可同时提供（合并进 Prompt）。  
2. **关联校验**：analysis 必须同 Project 且 `succeeded`；否则 **400** `invalid_requirement_analysis`。  
3. **执行模式**：同步；复用 OpenAI 兼容 Provider（扩展 `plan_technical` 方法或独立 Prompt 方法）。  
4. **历史**：保留多次规划记录，不做版本 diff。  
5. **Frontend**：嵌在项目详情页「技术规划」Tab/区块，与「需求分析」并列。  
6. **SQLite**：`init_db` / Alembic 新增表；与 Phase 4 相同运维方式。

请确认本 Requirements（可回「确认」或修改假设）。确认后生成 `design.md`。
