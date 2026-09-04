# AI Engineering Copilot — Phase 10 Design（Development Metrics）

> 基于已确认的 `requirements.md`  
> 状态：待用户回复「开始执行」后实施

## 1. 架构概览

```text
Frontend ProjectDetail Tabs（八大 Tab，七大 AI 能力全集）
  └─ 研发度量（Phase 10）
        POST/GET /api/v1/projects/{id}/development-metrics
              └─ DevelopmentMetricService
                    ├─ ProjectRepository
                    ├─ 六类 Repository（汇总统计 + 近期摘要）
                    ├─ DevelopmentMetricRepository
                    └─ LLMProvider.generate_metrics(context)
```

复用 Phase 4–9 LLM 工厂；扩展 Provider 协议。

---

## 2. 数据模型

### 2.1 表 `development_metrics`

| 列 | 类型 | 说明 |
|----|------|------|
| id | UUID PK | |
| project_id | UUID FK projects CASCADE | indexed |
| created_by | UUID FK users CASCADE | |
| metrics_focus | Text | 度量关注点（快照） |
| context_text | Text NULL | 补充说明 |
| status | String(32) | pending / succeeded / failed |
| result_json | JSON NULL | |
| model_name | String(128) NULL | |
| error_message | Text NULL | |
| created_at / updated_at | DateTime(tz) | |

无 FK 到其他 AI 实体；上下文由 Service 实时汇总。

### 2.2 结果 JSON（Pydantic `MetricsReportResult`）

```json
{
  "summary": "string",
  "overall_health": "string",
  "workflow_coverage": [
    { "stage": "requirement_analysis", "status": "covered", "notes": "..." }
  ],
  "quality_indicators": [
    { "name": "test coverage mindset", "assessment": "...", "evidence": "..." }
  ],
  "velocity_indicators": ["..."],
  "risk_indicators": ["..."],
  "recommendations": ["..."],
  "open_questions": ["..."]
}
```

- `WorkflowCoverageItem`：`stage`, `status`, `notes`  
- `QualityIndicatorItem`：`name`, `assessment`, `evidence`  

避免 `Test*` 前缀类名。

---

## 3. Backend 分层

```text
app/models/development_metric.py
app/schemas/development_metric.py
app/repositories/development_metric_repository.py
app/services/development_metric_service.py   # + _build_workflow_summary()
app/api/v1/development_metrics.py
app/services/llm/base.py                     # + generate_metrics
app/services/llm/openai_provider.py          # + METRICS_SYSTEM_PROMPT
```

Alembic：`20260402_0008_create_development_metrics.py`（`down_revision = 20260401_0007`）。

---

## 4. Service 逻辑

### 4.1 创建请求 `DevelopmentMetricCreate`

```python
metrics_focus: str = Field(..., min_length=1, max_length=100_000)
context_text: str | None = Field(None, max_length=100_000)
```

### 4.2 工作流汇总 `_build_workflow_summary(project_id)`

对各 Repository 调用 `list_by_project(project_id, page=1, page_size=100)`（或专用 count 查询）：

| 阶段 | stage 键 | 摘要字段来源 |
|------|----------|--------------|
| requirement_analyses | requirement_analysis | result_json.summary |
| technical_plans | technical_planning | result_json.summary |
| code_generations | ai_coding | result_json.summary |
| test_generations | automated_testing | result_json.summary |
| code_reviews | code_review | result_json.summary |
| debug_sessions | ai_debugging | result_json.summary |

输出文本块示例：

```text
--- Workflow Statistics ---
requirement_analysis: total=5, succeeded=4, failed=1
recent_summaries: ["...", "..."]
...
```

每阶段 `recent_summaries` 最多 3 条（成功记录、按 created_at 已倒序）。

### 4.3 Prompt 拼装

```text
--- Metrics Focus ---
{metrics_focus}

--- Workflow Statistics ---
{汇总块}

--- Additional Context ---
{context_text}
```

### 4.4 LLM 与状态

与 Phase 4–9 一致：503 无 Key 不落库；`pending` → `generate_metrics` → 更新。

### 4.5 错误码

| 场景 | code |
|------|------|
| 越权 Project | `project_not_found` |
| 记录不存在 | `development_metric_not_found` |

---

## 5. API

| Method | Path |
|--------|------|
| POST | `/api/v1/projects/{project_id}/development-metrics` |
| GET | `/api/v1/projects/{project_id}/development-metrics` |
| GET | `/api/v1/projects/{project_id}/development-metrics/{id}` |

---

## 6. LLM Provider

```python
def generate_metrics(self, context: str) -> MetricsReportResult: ...
```

`METRICS_SYSTEM_PROMPT`：要求 JSON 键与 schema 对齐；`workflow_coverage` 应覆盖七大阶段名称（含本报告阶段 development_metrics 的 meta 解读）。

---

## 7. Frontend

### 7.1 `frontend/src/api/developmentMetrics.ts`

### 7.2 Tab「研发度量」

- TextArea：`metrics_focus`（必填）
- TextArea：`context_text`（可选）
- 提交「生成度量报告」
- 历史 Table
- 结果：summary、overall_health、workflow_coverage Table、quality_indicators Table、列表类指标、recommendations

---

## 8. 测试

`tests/test_development_metrics.py`：

- 空项目 + Mock → 201 succeeded（workflow 统计为 0）
- 先创建若干 Mock 分析记录后生成 → 201 且 result 有 workflow_coverage
- 空 metrics_focus → 422
- LLM 失败 → 201 failed
- 越权 → 404

`pytest -q` 预期在 43 基础上 +5～6。

---

## 9. ADR

1. **无 FK**：度量基于实时汇总，不快照关联 ID。  
2. **平台内指标**：明确非 Git/CI 真实数据。  
3. **list_by_project 复用**：不新增 count SQL，本阶段数据量小可接受。  
4. **完成七大 Tab**：项目详情页 AI 能力 UI 闭环。

---

回复 **开始执行** 后实施。
