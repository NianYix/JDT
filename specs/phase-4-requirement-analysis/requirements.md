# AI Engineering Copilot — Phase 4 Requirements（Requirement Analysis）

> 前置：Phase 1–3 已完成（基础工程、User/Auth/Project、SQLAdmin）  
> 目标：在 Project 下交付「需求分析」最小可用闭环（非完整 Agent 平台）  
> 状态：待确认

## 1. 背景与目标

七大能力中，优先落地第一个 AI 场景：**Requirement Analysis**。

本阶段交付一条可演示链路：

1. 用户登录后进入某个 Project  
2. 粘贴/提交需求原文  
3. 调用 LLM 生成结构化分析结果  
4. 结果落库并在 Frontend 展示  

仍不引入 LangChain / LangGraph；优先用官方 SDK 直连（或可插拔 Provider）。

## 1.1 In Scope

- `RequirementAnalysis`（或同名）业务实体，归属 `Project`
- API：创建分析任务、查询详情/列表（按 Project）
- Service：组装 Prompt、调用 LLM、解析结构化输出、持久化
- Frontend：在项目详情页增加「需求分析」入口与结果展示
- 配置：通过环境变量管理 LLM Provider / API Key / Model（`.env.example` 占位，无真实密钥）
- pytest：对 Service 使用 Mock LLM，不依赖真实外网调用

## 1.2 Out of Scope

- LangChain / LangGraph / 多 Agent 编排
- Technical Planning、AI Coding、Code Review、Debugging、Metrics
- 流式输出（SSE）可作为增强，本阶段默认非必须
- 文件上传解析（PDF/Word）；本阶段仅纯文本
- 多人协作评论、工作流审批
- 自动改写代码仓

---

## 2. 功能需求（EARS）

### 2.1 数据与归属

**REQ-RA-001**  
WHEN 已认证用户对其拥有的 Project 提交需求分析请求时，THE SYSTEM SHALL 创建一条归属该 Project 的分析记录。

**REQ-RA-002**  
WHEN 用户请求不属于自己的 Project 下的分析资源时，THE SYSTEM SHALL 返回 404（与 Phase 2 越权策略一致）。

**REQ-RA-003**  
THE SYSTEM SHALL 至少持久化：原始需求文本、结构化结果（JSON）、状态、模型信息、创建/更新时间、错误信息（失败时）。

### 2.2 分析执行

**REQ-RA-004**  
WHEN 用户提交非空需求文本时，THE SYSTEM SHALL 调用配置的 LLM Provider 生成结构化分析结果。

**REQ-RA-005**  
WHEN LLM 调用成功时，THE SYSTEM SHALL 将结果解析为约定结构并保存，状态标记为成功（如 `succeeded`）。

**REQ-RA-006**  
WHEN LLM 调用失败或返回无法解析的内容时，THE SYSTEM SHALL 保存失败原因，状态标记为失败（如 `failed`），且不得静默丢弃错误。

**REQ-RA-007**  
THE SYSTEM SHALL 支持同步完成一次分析（请求内等待 LLM 返回）；异步队列本阶段不做。

### 2.3 结构化结果（最小字段）

**REQ-RA-008**  
THE SYSTEM SHALL 让分析结果至少包含以下字段（允许后续扩展）：

- `summary`：需求摘要  
- `goals`：目标列表  
- `stakeholders`：干系人列表  
- `functional_requirements`：功能需求列表  
- `non_functional_requirements`：非功能需求列表  
- `assumptions`：假设  
- `risks`：风险  
- `open_questions`：待澄清问题  

### 2.4 API

**REQ-RA-009**  
THE SYSTEM SHALL 提供（路径可微调，设计阶段固定）：

- `POST /api/v1/projects/{project_id}/requirement-analyses`  
- `GET /api/v1/projects/{project_id}/requirement-analyses`（分页）  
- `GET /api/v1/projects/{project_id}/requirement-analyses/{id}`  

**REQ-RA-010**  
THE SYSTEM SHALL 继续使用 API / Service / Repository 分层，并复用 JWT 鉴权。

### 2.5 Frontend

**REQ-RA-011**  
WHEN 用户打开项目详情页时，THE SYSTEM SHALL 提供需求分析入口（表单提交原文 + 历史列表/最新结果展示）。

**REQ-RA-012**  
WHEN 分析成功返回时，THE SYSTEM SHALL 以可读结构化方式展示结果（不必过度设计）。

### 2.6 配置与安全

**REQ-RA-013**  
THE SYSTEM SHALL 通过环境变量配置 LLM（如 `LLM_PROVIDER`、`LLM_API_KEY`、`LLM_MODEL`、`LLM_BASE_URL` 可选）。

**REQ-RA-014**  
THE SYSTEM SHALL NOT 将 API Key 写入前端或提交到 Git；`.env.example` 仅占位。

**REQ-RA-015**  
WHEN 未配置可用的 LLM Key 时，THE SYSTEM SHALL 返回明确业务错误（而非含糊 500）。

---

## 3. 非功能需求

**REQ-NFR-001**  
LLM 访问 SHALL 封装在独立 Provider 接口后，便于后续切换 OpenAI / Azure / 本地兼容 API。

**REQ-NFR-002**  
pytest SHALL Mock Provider，保证 CI/本地无 Key 也可绿。

**REQ-NFR-003**  
本阶段 SHALL 不引入 LangChain/LangGraph。

---

## 4. 验收标准

| ID | 验收项 | 通过条件 |
|----|--------|----------|
| AC-01 | 创建分析 | 登录用户可对本人 Project 提交文本并生成记录 |
| AC-02 | 成功结果 | Mock/真实 LLM 成功时可见结构化字段 |
| AC-03 | 失败可观测 | Key 缺失或调用失败时状态 failed + 错误信息 |
| AC-04 | 隔离 | 无法读写他人 Project 的分析 |
| AC-05 | Frontend | 项目页可提交并查看结果 |
| AC-06 | 测试 | pytest 全绿（含 Mock LLM） |
| AC-07 | 无 Agent 框架 | 依赖中无 langchain/langgraph |

---

## 5. 待确认默认假设

1. **首个 Provider**：OpenAI 兼容 HTTP API（可用官方 OpenAI，或任何兼容 `base_url` 的服务）。  
2. **执行模式**：**同步**请求内完成（不做 Celery/队列）。  
3. **输入**：**纯文本** only（不做文件上传）。  
4. **历史**：保留多次分析记录（列表 + 详情），不做版本 diff。  
5. **Frontend**：嵌在现有 Project 详情页，不新建独立复杂工作台。

请确认本 Requirements（可回「确认」或改假设）。确认后生成 `design.md`。
