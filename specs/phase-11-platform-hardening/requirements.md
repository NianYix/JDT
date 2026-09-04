# AI Engineering Copilot — Phase 11 Requirements（平台硬化：异步任务 / 工作流抽象 / 仓库上下文）

> 前置：Phase 1–10 已完成（七大 AI 能力同步闭环）  
> 目标：落地此前推荐的三件优化，提升可扩展性与产品可用性，**不新增第八类 AI 能力 Tab**  
> 状态：已确认（2026-08-31；待确认问题 1–4 全部按建议）

## 1. 背景与目标

Phase 4–10 以「同步 HTTP + 七套平行 CRUD + 纯文本上下文」交付了能力全集。当前主要痛点：

1. **同步阻塞 LLM**：单次请求最长约 90s，占住 worker，体验与并发差  
2. **前后端工作流样板重复**：七类能力结构高度同构，维护成本线性上升；`ProjectDetailPage` 过大  
3. **`repo_path` 几乎未使用**：编码 / 测试 / 审查 / 调试缺少真实仓库上下文  

本阶段完成三项优化，形成可演进基础：

| 优先级 | 主题 | 一句话目标 |
|--------|------|------------|
| P0 | 异步任务化 LLM | 创建即返回；后台执行；前端轮询状态 |
| P0 | 工作流公共层 | 后端与前端抽取共性，减少复制粘贴 |
| P0 | 只读仓库上下文 | 浏览文件树、选择文件内容并入 Prompt |

仍不引入 LangChain / LangGraph；不向工作区自动写文件；不接入真实 Git/CI 度量。

## 1.1 In Scope

### A. 异步任务化 LLM

- 七类既有 AI 创建接口改为：**快速创建记录（`pending`）并调度后台执行，HTTP 立即返回记录**
- 后台执行成功 → `succeeded` + `result_json`；失败 → `failed` + `error_message`
- Frontend：创建后轮询详情/列表直至终态；展示 `pending` / `running`（若引入）/ `succeeded` / `failed`
- 允许用户在 UI 看到进行中状态；本阶段**不要求**可取消已运行的 LLM 调用（可选增强见 Out of Scope 边界说明）
- pytest：覆盖「创建后为 pending/running → 后台完成后为 succeeded/failed」；Mock LLM

### B. 工作流公共层

- Backend：抽取七类 AI Job 的共性（项目归属校验、创建 pending、调用 LLM、落库状态、list/get 分页）  
- Frontend：将 `ProjectDetailPage` 拆为可复用工作流面板 + 各能力配置；按 Tab **懒加载**数据  
- 不改变对外 REST 路径与主要字段语义（兼容现有客户端）；允许新增可选字段与仓库相关 API

### C. 只读仓库上下文

- 基于 Project 的 `repo_path`（本机绝对/相对路径）提供：
  - 文件树浏览（深度/数量限制）
  - 读取所选文件内容（大小限制）
- 编码 / 测试 / 审查 / 调试（及可选：技术规划）创建请求支持附带「选中文件路径列表」；Service 将文件内容拼入 LLM Prompt
- Frontend：在相关 Tab 提供文件树选择器（仅当 `repo_path` 已配置且可读）
- 安全：路径穿越防护；禁止读出 `repo_path` 根目录之外；二进制/超大文件拒绝或截断策略明确

## 1.2 Out of Scope

- LangChain / LangGraph / 多 Agent 编排
- **向 `repo_path` 写入或修改文件**
- 真实 DORA / Git log / CI 指标采集
- Celery / 独立 Worker 进程集群（本阶段允许进程内后台任务；Redis 可选作队列，非必须）
- SSE / WebSocket 推送（本阶段用轮询即可）
- 取消正在执行的 LLM HTTP 请求（可列为后续）
- Refresh Token / SSO / 组织 RBAC
- 应用完整容器化
- 重写全部 Prompt 文案或更换模型供应商协议

---

## 2. 功能需求（EARS）

### 2.1 异步任务化 — 创建与状态

**REQ-ASYNC-001**  
WHEN 已认证用户对其拥有的 Project 提交任一类既有 AI 工作流创建请求时，THE SYSTEM SHALL 在持久化一条状态为非终态（`pending` 或 `running`）的记录后，于 LLM 完成前返回该记录的 HTTP 响应（不得同步阻塞至 LLM 结束）。

**REQ-ASYNC-002**  
WHEN 后台任务开始执行某条 AI 记录时，THE SYSTEM SHALL 将该记录状态更新为可区分的进行中状态（若仅使用 `pending` 表示排队与执行中，THE SYSTEM SHALL 在设计中明确单一状态语义；推荐引入 `running`）。

**REQ-ASYNC-003**  
WHEN 后台 LLM 调用成功时，THE SYSTEM SHALL 将对应记录更新为 `succeeded`，写入 `result_json` 与 `model_name`，并清除或置空 `error_message`。

**REQ-ASYNC-004**  
WHEN 后台 LLM 调用失败时，THE SYSTEM SHALL 将对应记录更新为 `failed`，写入可读的 `error_message`，且不得因未捕获异常导致记录永久卡在非终态而不落库。

**REQ-ASYNC-005**  
WHEN 客户端查询某条 AI 记录详情或项目下列表时，THE SYSTEM SHALL 返回当前持久化状态与已有结果字段，使客户端可通过轮询观察到从非终态到终态的变迁。

**REQ-ASYNC-006**  
THE SYSTEM SHALL 保持七类工作流既有 REST 路径与主要资源 ID 语义不变（创建仍为 POST 同路径；列表/详情仍为既有 GET）。

**REQ-ASYNC-007**  
WHEN `LLM` 未配置或 Provider 初始化失败时，THE SYSTEM SHALL 仍创建记录并将该次执行标记为 `failed`（或在调度前失败并返回明确错误）；行为须在 design 中二选一并在测试中固定，避免「创建成功但永不执行」。

### 2.2 异步任务化 — Frontend

**REQ-ASYNC-010**  
WHEN 用户在 Frontend 触发 AI 生成且响应记录为非终态时，THE SYSTEM SHALL 自动轮询该记录（或刷新列表）直至状态为 `succeeded` 或 `failed`，并展示进行中反馈。

**REQ-ASYNC-011**  
WHEN 轮询得到 `succeeded` 时，THE SYSTEM SHALL 展示结构化结果；WHEN 得到 `failed` 时，THE SYSTEM SHALL 展示错误信息。

**REQ-ASYNC-012**  
THE SYSTEM SHALL 为轮询设置合理上限（次数或总时长）；超时后提示用户可手动刷新，且不得无限请求压垮后端。

### 2.3 工作流公共层 — Backend

**REQ-WF-001**  
THE SYSTEM SHALL 提供可复用的后端抽象（基类、泛型服务、或共享模块），覆盖至少：项目归属校验、创建非终态记录、调度执行、成功/失败落库、按项目分页列表、按项目取详情。

**REQ-WF-002**  
WHEN 实现或修改任一类 AI 工作流时，THE SYSTEM SHALL 使该类仅保留自身差异（输入字段、Prompt/Provider 方法、结果 Schema、可选上游引用校验），而非复制整套 create/list/get 样板。

**REQ-WF-003**  
THE SYSTEM SHALL 在抽取公共层后保持既有 API 契约与越权策略（非 owner → 404）不变。

### 2.4 工作流公共层 — Frontend

**REQ-WF-010**  
THE SYSTEM SHALL 将项目详情页中七类 AI Tab 的共性 UI（触发表单区、历史列表、选中详情、状态 Tag、加载/轮询）抽取为可复用组件或 hooks。

**REQ-WF-011**  
WHEN 用户打开项目详情页时，THE SYSTEM SHALL **不**在首屏强制串行加载全部七类工作流数据；WHEN 用户切换到某一 AI Tab 时，THE SYSTEM SHALL 再加载该 Tab 所需数据（懒加载）。

**REQ-WF-012**  
THE SYSTEM SHALL 将 `ProjectDetailPage` 拆分为更小模块，使单文件职责清晰（目标：详情页入口显著短于当前约 1500+ 行；具体拆分目录在 design 中规定）。

### 2.5 只读仓库上下文 — API 与安全

**REQ-REPO-001**  
WHEN 已认证用户请求其拥有的 Project 的仓库文件树，且该 Project 配置了非空 `repo_path` 且路径存在且为目录时，THE SYSTEM SHALL 返回受深度与条目数限制的目录树（含相对路径、是否目录、可选文件大小）。

**REQ-REPO-002**  
WHEN `repo_path` 为空、不存在、不是目录、或当前进程不可读时，THE SYSTEM SHALL 返回明确错误码（如 `repo_not_configured` / `repo_unavailable`），不得泄露服务器其他路径信息。

**REQ-REPO-003**  
WHEN 用户请求读取仓库内某一相对路径文件时，THE SYSTEM SHALL 仅允许解析后的绝对路径落在该 Project `repo_path` 规范化根目录之内；否则返回 400（如 `path_outside_repo`）。

**REQ-REPO-004**  
WHEN 目标路径为目录、不存在、或为符号链接逃逸风险无法安全解析时，THE SYSTEM SHALL 拒绝读取并返回明确错误。

**REQ-REPO-005**  
THE SYSTEM SHALL 限制单文件读取的最大字节数；超过限制时拒绝或截断（design 中固定一种），并在响应或错误中可识别。

**REQ-REPO-006**  
THE SYSTEM SHALL 跳过或拒绝明显二进制文件（如按扩展名黑名单或内容抽样检测），避免将无意义二进制塞进 Prompt。

**REQ-REPO-007**  
THE SYSTEM SHALL 提供至少以下 API（具体路径在 design 中确定，前缀保持 `/api/v1`）：

- 获取项目仓库文件树  
- 读取项目仓库内单个文件内容（或批量读取，须有总大小上限）

### 2.6 只读仓库上下文 — 注入 Prompt

**REQ-REPO-010**  
WHEN 用户创建 **AI Coding / Automated Testing / AI Code Review / AI Debugging** 记录且请求体包含选中文件相对路径列表时，THE SYSTEM SHALL 在调度 LLM 前读取这些文件（受安全与大小限制），并将内容拼入 Prompt 上下文。

**REQ-REPO-011**  
WHEN 选中路径列表为空或未提供时，THE SYSTEM SHALL 保持与现有行为兼容（仅任务描述 + 可选上游结果 + `context_text`）。

**REQ-REPO-012**  
WHEN 部分选中文件读取失败时，THE SYSTEM SHALL 采用 design 中规定的策略（整单失败 **或** 跳过失败文件并在 Prompt/结果中注明）；不得静默丢弃全部上下文却仍声称已附带仓库文件。

**REQ-REPO-013**  
THE SYSTEM SHALL 限制单次请求可附带的文件数量与合计字符/字节上限，防止 Prompt 爆炸。

**REQ-REPO-014**  
THE SYSTEM SHALL 允许 **Technical Planning** 可选附带仓库文件（若实现成本可控）；需求分析与研发度量**不强制**绑定仓库文件选择器。

### 2.7 只读仓库上下文 — Frontend

**REQ-REPO-020**  
WHEN 项目已配置可用的 `repo_path` 时，THE SYSTEM SHALL 在 Coding / Testing / Review / Debugging（及若启用的 Planning）Tab 提供文件树多选，并将所选相对路径随创建请求提交。

**REQ-REPO-021**  
WHEN `repo_path` 不可用时，THE SYSTEM SHALL 隐藏或禁用文件选择器，并简短提示用户先在项目信息中配置有效路径。

### 2.8 测试与文档

**REQ-QA-001**  
THE SYSTEM SHALL 为异步创建→终态、路径穿越拒绝、超限拒绝、Mock LLM 成功/失败提供 pytest 覆盖。

**REQ-QA-002**  
THE SYSTEM SHALL 更新根 README：说明异步行为、轮询、仓库只读 API 与安全限制，并修正「同步」相关过时描述。

**REQ-QA-003**  
THE SYSTEM SHALL 不要求本阶段新增 Frontend 自动化 E2E；手动验证清单列入 tasks。

---

## 3. 非功能需求

**REQ-NFR-001**  
THE SYSTEM SHALL 保证单个 HTTP 创建 AI 任务的接口响应时间在正常负载下显著短于 LLM 调用时长（目标：通常 &lt; 2s 返回记录，不含 LLM）。

**REQ-NFR-002**  
THE SYSTEM SHALL 避免因同步 LLM 调用长期占用 ASGI worker；后台执行机制须在 design 中明确（如 FastAPI `BackgroundTasks`、线程池、或轻量队列）。

**REQ-NFR-003**  
THE SYSTEM SHALL 在日志中记录任务开始/结束与失败原因，且不对客户端默认返回完整上游堆栈。

**REQ-NFR-004**  
THE SYSTEM SHALL 保持 SQLite（`start.bat`）与 PostgreSQL 均可运行本阶段功能；若使用 Redis，则须提供无 Redis 时的降级路径（进程内执行）。

---

## 4. 验收标准（摘要）

1. 七类 AI「创建」接口在 Mock/真实 LLM 慢响应场景下均可快速返回非终态记录，随后变为 `succeeded`/`failed`。  
2. Frontend 创建后自动轮询并展示终态结果；Tab 懒加载，详情页模块化拆分完成。  
3. 配置合法 `repo_path` 后可浏览文件树、多选文件；Coding 等创建请求能将文件内容注入 Prompt；路径穿越用例被拒绝。  
4. 既有 pytest 适配异步语义后通过；新增仓库安全与异步相关测试通过。  
5. README 与本阶段事实一致。

---

## 5. 待确认问题（请回复时一并拍板）

1. **后台机制**：优先 **进程内 BackgroundTasks/线程池（无 Redis 依赖）**，还是 **Redis 队列**？  
   - 建议默认：**进程内 + 无 Redis 也可跑**（与当前 `start.bat` SQLite 一致）。  
2. **状态枚举**：是否新增 `running`（`pending`→`running`→终态），还是继续只用 `pending` 表示未完成？  
   - 建议默认：**引入 `running`**。  
3. **选中文件读取失败策略**：整单 `failed`，还是跳过坏文件继续？  
   - 建议默认：**任一必需文件失败则整单 failed**（更清晰）。  
4. **技术规划是否也挂文件选择器**？  
   - 建议默认：**挂上**（与编码同一套组件）。

> 已确认：全部按建议。见同目录 `design.md` / `tasks.md`。回复「开始执行」后开始改代码。
