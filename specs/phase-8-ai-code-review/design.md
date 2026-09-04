# AI Engineering Copilot — Phase 8 Design（AI Code Review）

> 基于已确认的 `requirements.md`  
> 状态：待用户回复「开始执行」后实施

## 1. 架构概览

```text
Frontend ProjectDetail Tabs
  ├─ 项目信息 … 自动化测试（Phase 7）
  └─ 代码审查（Phase 8）
        POST/GET /api/v1/projects/{id}/code-reviews
              └─ CodeReviewService
                    ├─ ProjectRepository / CodeGenerationRepository
                    ├─ CodeReviewRepository
                    └─ LLMProvider.review_code(context)
```

复用 Phase 4–7 LLM 工厂与 `LLM_*` 配置；扩展 Provider 协议。

---

## 2. 数据模型

### 2.1 表 `code_reviews`

| 列 | 类型 | 说明 |
|----|------|------|
| id | UUID PK | |
| project_id | UUID FK projects CASCADE | indexed |
| code_generation_id | UUID FK code_generations NULL | indexed, nullable |
| created_by | UUID FK users CASCADE | |
| review_scope | Text | 审查范围描述（快照） |
| context_text | Text NULL | 待审代码/补充说明 |
| status | String(32) | pending / succeeded / failed |
| result_json | JSON NULL | |
| model_name | String(128) NULL | |
| error_message | Text NULL | |
| created_at / updated_at | DateTime(tz) | |

### 2.2 结果 JSON（Pydantic `ReviewResult`）

```json
{
  "summary": "string",
  "overall_assessment": "string",
  "issues": [
    {
      "severity": "major",
      "location": "backend/app/api/v1/auth.py",
      "category": "security",
      "description": "string",
      "suggestion": "string"
    }
  ],
  "strengths": ["clear layering"],
  "security_notes": ["..."],
  "performance_notes": ["..."],
  "maintainability_notes": ["..."],
  "suggested_fixes": [
    {
      "path": "backend/app/api/v1/auth.py",
      "description": "hash password",
      "content": "..."
    }
  ],
  "open_questions": ["..."]
}
```

Schema 类命名避免 pytest 误收集 `Test*` 前缀：`IssueItem`、`FixSuggestion`、`ReviewResult`。

---

## 3. Backend 分层

```text
app/models/code_review.py
app/schemas/code_review.py
app/repositories/code_review_repository.py
app/services/code_review_service.py
app/api/v1/code_reviews.py
app/services/llm/base.py              # + review_code
app/services/llm/openai_provider.py   # + REVIEW_SYSTEM_PROMPT
```

Alembic：`20260331_0006_create_code_reviews.py`（`down_revision = 20260330_0005`）。

---

## 4. Service 逻辑

### 4.1 创建请求 `CodeReviewCreate`

```python
code_generation_id: UUID | None = None
review_scope: str = Field(..., min_length=1, max_length=100_000)
context_text: str | None = Field(None, max_length=100_000)
```

`review_scope` strip 后非空 → 422。

### 4.2 关联 AI 编码

若提供 `code_generation_id`：

1. `CodeGenerationRepository.get_by_id_for_project(id, project_id)`
2. 不存在或 `status != succeeded` → **400** `invalid_code_generation`

### 4.3 Prompt 上下文

```text
--- Review Scope ---
{review_scope}

--- Code Generation (JSON) ---
{result_json 或 task_description 兜底}

--- Code / Context to Review ---
{context_text}
```

### 4.4 LLM 与状态

- 无 Key → **503**，不写库
- insert `pending` → `review_code` → `succeeded` / `failed`

### 4.5 错误码

| 场景 | 状态 | code |
|------|------|------|
| 越权 Project | 404 | `project_not_found` |
| 记录不存在 | 404 | `code_review_not_found` |
| 无效 code_generation | 400 | `invalid_code_generation` |

---

## 5. API

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/v1/projects/{project_id}/code-reviews` | 201 |
| GET | `/api/v1/projects/{project_id}/code-reviews` | 分页 |
| GET | `/api/v1/projects/{project_id}/code-reviews/{id}` | 详情 |

挂载 `app/api/router.py`；标签 `code-reviews`。

---

## 6. LLM Provider

### 6.1 协议扩展

```python
def review_code(self, context: str) -> ReviewResult: ...
```

### 6.2 `REVIEW_SYSTEM_PROMPT`

JSON 键与 `ReviewResult` 对齐；`issues` 为对象数组；`suggested_fixes` 含可选 `content`。

### 6.3 解析

复用 `_parse_json_content` → `ReviewResult.model_validate(payload)`。

---

## 7. Frontend

### 7.1 API 客户端

`frontend/src/api/codeReviews.ts`

### 7.2 UI（`ProjectDetailPage`）

Tabs 增加 **「代码审查」**：

- TextArea：`review_scope`（必填）
- Select：本项目 `status=succeeded` 的 `code_generations`
- TextArea：`context_text`（待审代码，可选）
- 提交「开始审查」
- 历史 Table + 结果：摘要、总体评价、问题 Table（severity/location/category）、优点、各类 notes、`suggested_fixes` 用 `<pre>`

复用页面已加载的 `generations` 列表作下拉（`succeededCodeGens`）。

---

## 8. 测试

`tests/test_code_reviews.py`：

| 用例 | 期望 |
|------|------|
| 仅 review_scope + Mock 成功 | 201 succeeded |
| 关联 succeeded code_generation | 201 + FK |
| 无效 code_generation_id | 400 |
| 空 review_scope | 422 |
| LLM 抛错 | 201 failed |
| 越权 | 404 |

`pytest -q` 预期在 31 基础上 +6。

---

## 9. 依赖关系

无新增 pip/npm 依赖。

---

## 10. ADR

1. **扩展 Provider**：共享 OpenAI 客户端。  
2. **FK 到 code_generations**：编码→审查链路。  
3. **表名 code_reviews**：与业务语义一致。  
4. **不自动修复**：Service 无写盘逻辑。  
5. **Schema 命名**：`ReviewResult` 而非 `CodeReviewResult`，避免与 ORM `CodeReview` 混淆；issues 用 `IssueItem`。

---

## 11. 文档

- `README.md` Phase 8 段落  
- `specs/phase-8-ai-code-review/tasks.md`  

回复 **开始执行** 后实施。
