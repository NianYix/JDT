# AI Engineering Copilot — Phase 5 Design（Technical Planning）

> 基于已确认的 `requirements.md`  
> 已确认：analysis_id 或 context_text、400 校验、同步 OpenAI、多次历史、嵌详情页  
> 状态：待确认后生成 `tasks.md`（requirements 已确认，本文与 tasks 一并交付）

## 1. 架构概览

```text
Frontend ProjectDetail
  ├─ 需求分析（Phase 4）
  └─ 技术规划（Phase 5）
        POST/GET /api/v1/projects/{id}/technical-plans
              └─ TechnicalPlanService
                    ├─ ProjectRepository / RequirementAnalysisRepository
                    ├─ TechnicalPlanRepository
                    └─ LLMProvider.plan_technical(context)
```

复用 Phase 4 LLM 工厂与配置；扩展 Provider 协议，不新建 Provider 类。

---

## 2. 数据模型

### 2.1 表 `technical_plans`

| 列 | 类型 | 说明 |
|----|------|------|
| id | UUID PK | |
| project_id | UUID FK projects CASCADE | indexed |
| requirement_analysis_id | UUID FK requirement_analyses NULL | indexed, nullable |
| created_by | UUID FK users CASCADE | |
| context_text | Text NULL | 用户补充说明（快照） |
| status | String(32) | pending / succeeded / failed |
| result_json | JSON NULL | |
| model_name | String(128) NULL | |
| error_message | Text NULL | |
| created_at / updated_at | DateTime(tz) | |

### 2.2 结果 JSON（Pydantic `TechnicalPlanResult`）

```json
{
  "summary": "string",
  "architecture_overview": "string",
  "tech_stack": ["string"] 或 [{"name":"...", "reason":"..."}],
  "modules": [{"name":"...", "responsibility":"..."}],
  "api_outline": ["string"],
  "data_model_outline": ["string"],
  "milestones": ["string"],
  "dependencies": ["string"],
  "risks_and_mitigations": ["string"],
  "open_questions": ["string"]
}
```

`tech_stack` / `modules` 在 schema 层用宽松类型（list of str 或 dict）或固定 dict 结构；实现选定 **modules 为 `{name, responsibility}` 对象列表**，`tech_stack` 为 **字符串列表**（简单）。

---

## 3. Backend 分层

```text
app/models/technical_plan.py
app/schemas/technical_plan.py
app/repositories/technical_plan_repository.py
app/services/technical_plan_service.py
app/api/v1/technical_plans.py
app/services/llm/base.py          # + plan_technical
app/services/llm/openai_provider.py # + PLAN_SYSTEM_PROMPT
```

Alembic：`20260328_0003_create_technical_plans.py`（down_revision = Phase 4 migration）。

---

## 4. Service 逻辑

### 4.1 创建请求 `TechnicalPlanCreate`

```python
requirement_analysis_id: UUID | None = None
context_text: str | None = Field(None, max_length=100_000)
```

校验：

- 至少一项非空（`analysis_id` 或 `context_text` 去空白后非空）
- 否则 **422**

### 4.2 关联需求分析

若提供 `requirement_analysis_id`：

1. 查 `RequirementAnalysisRepository.get_by_id_for_project(id, project_id)`
2. 不存在 → **400** `invalid_requirement_analysis`
3. `status != succeeded` → **400** `invalid_requirement_analysis`

### 4.3 Prompt 上下文拼装

```text
--- Requirement Analysis (JSON) ---
{result_json 或 source_text}

--- Additional Context ---
{context_text}
```

仅 analysis：用 `result_json` 序列化 + `source_text` 兜底。  
仅 context_text：只传补充段。

### 4.4 LLM 与状态

与 Phase 4 一致：

- 无 Key → **503** 不写库
- 先 insert `pending` → 调 LLM → `succeeded` / `failed` 更新

---

## 5. API

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/v1/projects/{project_id}/technical-plans` | 201 |
| GET | `/api/v1/projects/{project_id}/technical-plans` | 分页 |
| GET | `/api/v1/projects/{project_id}/technical-plans/{id}` | 详情 |

挂载 `api/router.py`；越权 **404** `project_not_found` / `technical_plan_not_found`。

---

## 6. Frontend

### 6.1 API

`frontend/src/api/technicalPlans.ts`

### 6.2 UI

`ProjectDetailPage` 使用 **Tabs**：

- Tab「项目信息」（现有表单）
- Tab「需求分析」（Phase 4 区块移入）
- Tab「技术规划」（新建）

技术规划 Tab：

- 下拉：本项目 `status=succeeded` 的需求分析（显示 summary + 时间）
- TextArea：补充 `context_text`
- 提交按钮 + 历史 Table + 结果展示（结构同 RA）

列表 API 在进入 Tab 时加载 succeeded 分析供下拉。

---

## 7. 测试

`tests/test_technical_plans.py`：

- Mock `plan_technical` 成功
- LLM 失败 → 201 + failed
- 503 无 Key
- 越权 404
- 无效 analysis_id → 400
- 仅 context_text 创建

扩展 `LLMProvider` Mock 类。

---

## 8. ADR

1. **扩展 Provider 而非新类**：共享 OpenAI 客户端与配置。  
2. **可选 FK 到 requirement_analyses**：形成需求→规划链路。  
3. **400 而非 404 给坏 analysis_id**：同项目内 ID 存在但状态不对时更清晰。  
4. **Tabs 拆分详情页**：避免单页过长。  
5. **同步执行**：与 Phase 4 一致。

---

## 9. 待确认

本文 assumptions 已与 requirements「按推荐」对齐。下一步生成 `tasks.md`；回复 **开始执行** 后改代码。
