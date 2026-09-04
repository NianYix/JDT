# AI Engineering Copilot — Phase 10 Requirements（Development Metrics）

> 前置：Phase 1–9 已完成（七大 AI 能力前六项）  
> 目标：在 Project 下交付「研发度量报告」最小可用闭环，完成七大能力全集  
> 状态：待确认

## 1. 背景与目标

七大能力中，第七个 AI 场景：**Development Metrics**。

在 Project 内已积累需求分析、技术规划、编码、测试、审查、调试等 AI 工作记录之上，交付链路：

1. 用户进入某个 Project  
2. 描述度量关注点（如「评估研发流程健康度与风险」），可选补充团队/流程上下文  
3. Service **自动汇总本项目既有 AI 工作流数据**（各阶段记录数量、成功率、近期摘要）并入 Prompt  
4. 调用 LLM 生成结构化研发度量报告  
5. 结果落库并在 Frontend 展示  

仍不引入 LangChain / LangGraph；复用既有 LLM Provider 基础设施。

**本阶段度量基于平台内 AI 工作流数据与 LLM 综合解读，不接入 Git 提交统计、Jira、CI 流水线真实指标。**

## 1.1 In Scope

- `DevelopmentMetric`（或同名）业务实体，归属 `Project`
- 必填 `metrics_focus`（度量关注点/目标描述）
- 可选 `context_text`（团队规模、迭代节奏等补充说明）
- Service：查询本项目各阶段 Repository 汇总统计 + 近期成功记录摘要，拼装 Prompt
- API：创建报告、列表、详情（按 Project）
- 扩展 `LLMProvider.generate_metrics(context)`（或等价命名）
- Frontend：项目详情页增加「研发度量」Tab
- pytest：Mock LLM，不依赖真实 Key
- 复用 `LLM_*` 配置与 `get_llm_provider`

## 1.2 Out of Scope

- LangChain / LangGraph / 多 Agent 编排
- **真实 DORA/Git/CI/Jira 数据采集**
- **扫描 `repo_path`、读取 git log**
- 时序图表、Grafana 集成、定时自动报表
- 流式 SSE（本阶段同步）
- 多轮对话 / Chat 会话历史（本阶段单次请求）
- 文件上传；本阶段纯文本
- 跨 Project 组织级仪表盘

---

## 2. 功能需求（EARS）

### 2.1 数据与归属

**REQ-DM-001**  
WHEN 已认证用户对其拥有的 Project 提交研发度量请求时，THE SYSTEM SHALL 创建一条归属该 Project 的度量报告记录。

**REQ-DM-002**  
WHEN 用户请求不属于自己的 Project 下的度量资源时，THE SYSTEM SHALL 返回 404（与 Phase 2 越权策略一致）。

**REQ-DM-003**  
THE SYSTEM SHALL 至少持久化：度量关注点、补充上下文、结构化结果（JSON）、状态、模型信息、创建/更新时间、错误信息（失败时）。

### 2.2 输入校验

**REQ-DM-004**  
WHEN 用户提交创建请求时，THE SYSTEM SHALL 要求 `metrics_focus` 去空白后非空；否则返回 422。

**REQ-DM-005**  
THE SYSTEM SHALL 允许仅提供 `metrics_focus`（无 `context_text`）发起度量生成。

### 2.3 工作流数据汇总

**REQ-DM-006**  
WHEN 生成度量报告前，THE SYSTEM SHALL 查询本项目以下实体的统计并纳入 Prompt：

- `requirement_analyses`：总数、成功/失败数、最近成功摘要（若有）  
- `technical_plans`：同上  
- `code_generations`：同上  
- `test_generations`：同上  
- `code_reviews`：同上  
- `debug_sessions`：同上  

**REQ-DM-007**  
THE SYSTEM SHALL 将上述汇总以结构化文本（计数 + 可选 JSON 摘要片段）写入 LLM 上下文，而非要求用户手动粘贴历史记录。

### 2.4 生成执行

**REQ-DM-008**  
WHEN 输入校验通过且 LLM 可用时，THE SYSTEM SHALL 调用 LLM Provider 生成结构化度量报告。

**REQ-DM-009**  
WHEN LLM 调用成功时，THE SYSTEM SHALL 将结果解析为约定结构并保存，状态标记为 `succeeded`。

**REQ-DM-010**  
WHEN LLM 调用失败或返回无法解析的内容时，THE SYSTEM SHALL 保存失败原因，状态标记为 `failed`。

**REQ-DM-011**  
WHEN 未配置可用的 LLM Key 时，THE SYSTEM SHALL 返回明确业务错误（如 503），且**不创建**落库记录（与 Phase 4–9 一致）。

**REQ-DM-012**  
THE SYSTEM SHALL 支持同步完成一次生成；异步队列本阶段不做。

### 2.5 结构化结果（最小字段）

**REQ-DM-013**  
THE SYSTEM SHALL 让生成结果至少包含以下字段（允许后续扩展）：

- `summary`：报告摘要  
- `overall_health`：整体健康度评价（文字说明，可含 qualitative 等级）  
- `workflow_coverage`：七大工作流覆盖评价，每项含 `stage`（字符串）、`status`（如 covered/weak/missing）、`notes`  
- `quality_indicators`：质量指标列表，每项含 `name`、`assessment`、`evidence`  
- `velocity_indicators`：效率/节奏相关指标列表（基于平台数据的解读）  
- `risk_indicators`：风险信号列表  
- `recommendations`：改进建议列表  
- `open_questions`：待澄清问题  

### 2.6 Prompt 上下文

**REQ-DM-014**  
THE SYSTEM SHALL 将 `metrics_focus` 作为用户度量目标的主输入写入 Prompt。

**REQ-DM-015**  
WHEN 提供了 `context_text` 时，THE SYSTEM SHALL 将其作为团队/流程补充上下文一并传入 LLM。

### 2.7 API

**REQ-DM-016**  
THE SYSTEM SHALL 提供：

- `POST /api/v1/projects/{project_id}/development-metrics`  
- `GET /api/v1/projects/{project_id}/development-metrics`（分页）  
- `GET /api/v1/projects/{project_id}/development-metrics/{id}`  

**REQ-DM-017**  
THE SYSTEM SHALL 继续使用 API / Service / Repository 分层，并复用 JWT 鉴权。

### 2.8 Frontend

**REQ-DM-018**  
WHEN 用户打开项目详情页时，THE SYSTEM SHALL 在 Tabs 中提供「研发度量」入口。

**REQ-DM-019**  
THE SYSTEM SHALL 提供：度量关注点表单、可选补充上下文、提交按钮、历史列表、结果展示（含工作流覆盖表、指标与建议）。

**REQ-DM-020**  
WHEN 生成成功时，THE SYSTEM SHALL 以可读方式展示摘要、健康度评价与各维度指标。

### 2.9 配置与安全

**REQ-DM-021**  
THE SYSTEM SHALL 复用 Phase 4 的 `LLM_*` 环境变量配置。

**REQ-DM-022**  
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
Alembic 迁移 SHALL 为 `development_metrics` 表提供升级路径；SQLite 本地开发通过 `init_db` 可建表。

---

## 4. 验收标准

| ID | 验收项 | 通过条件 |
|----|--------|----------|
| AC-01 | 创建报告 | 登录用户可对本人 Project 提交 metrics_focus 并生成记录 |
| AC-02 | 自动汇总 | Service Prompt 包含各阶段计数（可通过 Mock + 断言上下文或集成测试间接验证） |
| AC-03 | 成功结果 | Mock/真实 LLM 成功时可见 workflow_coverage 与 recommendations |
| AC-04 | 失败可观测 | Key 缺失 → 503 无落库；调用失败 → 201 + `failed` |
| AC-05 | 隔离 | 无法读写他人 Project 的度量记录 |
| AC-06 | Frontend | 项目详情「研发度量」Tab 可提交并查看结果 |
| AC-07 | 测试 | pytest 全绿（含 Mock LLM） |
| AC-08 | 无外部采集 | 无 git/CI/Jira 调用逻辑 |
| AC-09 | 七大能力齐全 | 七大 AI Tab 均可在项目详情访问 |

---

## 5. 待确认默认假设

1. **实体命名**：表 `development_metrics`，模型 `DevelopmentMetric`；API 路径 `development-metrics`。  
2. **首个 Provider**：OpenAI 兼容 HTTP API，方法名 `generate_metrics(context: str)`。  
3. **执行模式**：**同步**请求内完成。  
4. **输入**：`metrics_focus` 必填；`context_text` 可选。  
5. **历史**：保留多次报告（列表 + 详情）。  
6. **Frontend**：Project 详情 Tabs 增加第八项「研发度量」（完成七大能力 UI 全集）。  
7. **汇总深度**：每阶段最多取最近 3 条成功记录的 summary 字段（或等价）注入 Prompt，避免超长。  
8. **无真实 DORA**：指标为 LLM 基于平台数据的解读，非实时工程系统指标。

请确认本 Requirements（可回「确认」或修改假设）。确认后生成 `design.md` 与 `tasks.md`。
