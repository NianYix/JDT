# AI Engineering Copilot — Phase 7 Design（Automated Testing）

> 基于已确认的 `requirements.md`  
> 状态：待用户回复「开始执行」后实施

## 1. 架构概览

```text
Frontend ProjectDetail Tabs
  ├─ 项目信息
  ├─ 需求分析（Phase 4）
  ├─ 技术规划（Phase 5）
  ├─ AI 编码（Phase 6）
  └─ 自动化测试（Phase 7）
        POST/GET /api/v1/projects/{id}/test-generations
              └─ TestGenerationService
                    ├─ ProjectRepository / CodeGenerationRepository
                    ├─ TestGenerationRepository
                    └─ LLMProvider.generate_tests(context)
```

复用 Phase 4–6 LLM 工厂与 `LLM_*` 配置；扩展 Provider 协议，不新建 Provider 类。

---

## 2. 数据模型

### 2.1 表 `test_generations`

| 列 | 类型 | 说明 |
|----|------|------|
| id | UUID PK | |
| project_id | UUID FK projects CASCADE | indexed |
| code_generation_id | UUID FK code_generations NULL | indexed, nullable |
| created_by | UUID FK users CASCADE | |
| target_description | Text | 待测目标描述（快照） |
| context_text | Text NULL | 用户补充上下文 |
| status | String(32) | pending / succeeded / failed |
| result_json | JSON NULL | |
| model_name | String(128) NULL | |
| error_message | Text NULL | |
| created_at / updated_at | DateTime(tz) | |

### 2.2 结果 JSON（Pydantic `TestGenerationResult`）

```json
{
  "summary": "string",
  "testing_strategy": "string",
  "test_cases": [
    {
      "name": "login success",
      "type": "unit",
      "description": "string",
      "steps": ["step 1"],
      "expected": "string"
    }
  ],
  "test_files": [
    {
      "path": "backend/tests/test_auth.py",
      "language": "python",
      "description": "Auth API tests",
      "content": "..."
    }
  ],
  "fixtures_and_mocks": ["mock LLM provider"],
  "coverage_notes": ["covers login and 401"],
  "risks": ["flaky network"],
  "open_questions": ["need e2e?"]
}
```

`test_cases` 固定 `{ name, type, description, steps, expected }`；`test_files` 与 Phase 6 `files` 结构一致。

---

## 3. Backend 分层

```text
app/models/test_generation.py
app/schemas/test_generation.py
app/repositories/test_generation_repository.py
app/services/test_generation_service.py
app/api/v1/test_generations.py
app/services/llm/base.py              # + generate_tests
app/services/llm/openai_provider.py   # + TEST_SYSTEM_PROMPT
```

Alembic：`20260330_0005_create_test_generations.py`（`down_revision = 20260329_0004`）。

`app/models/__init__.py` 导出 `TestGeneration`。

---

## 4. Service 逻辑

### 4.1 创建请求 `TestGenerationCreate`

```python
code_generation_id: UUID | None = None
target_description: str = Field(..., min_length=1, max_length=100_000)
context_text: str | None = Field(None, max_length=100_000)
```

`target_description` strip 后非空 → 422。

### 4.2 关联 AI 编码

若提供 `code_generation_id`：

1. `CodeGenerationRepository.get_by_id_for_project(id, project_id)`
2. 不存在或 `status != succeeded` → **400** `invalid_code_generation`

### 4.3 Prompt 上下文拼装

```text
--- Test Target ---
{target_description}

--- Code Generation (JSON) ---
{result_json 序列化，或 task_description 兜底}

--- Additional Context ---
{context_text}
```

### 4.4 LLM 与状态

- `get_llm_provider()` 无 Key → **503** `llm_not_configured`，**不写库**
- insert `pending` → `generate_tests` → `succeeded` / `failed`

### 4.5 列表与详情

越权 Project → **404** `project_not_found`；记录不存在 → **404** `test_generation_not_found`。

---

## 5. API

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/v1/projects/{project_id}/test-generations` | 201 |
| GET | `/api/v1/projects/{project_id}/test-generations` | 分页 |
| GET | `/api/v1/projects/{project_id}/test-generations/{id}` | 详情 |

挂载 `app/api/router.py`；标签 `test-generations`。

---

## 6. LLM Provider

### 6.1 协议扩展

```python
def generate_tests(self, context: str) -> TestGenerationResult: ...
```

### 6.2 `TEST_SYSTEM_PROMPT`

要求仅返回合法 JSON，键与 `TestGenerationResult` 对齐；`test_cases` 为对象数组；`test_files` 含 `content` 代码正文。

### 6.3 解析

复用 `_parse_json_content` → `TestGenerationResult.model_validate(payload)`。

---

## 7. Frontend

### 7.1 API 客户端

`frontend/src/api/testGenerations.ts`

### 7.2 UI（`ProjectDetailPage`）

Tabs 增加 **「自动化测试」**：

- TextArea：`target_description`（必填）
- Select：本项目 `status=succeeded` 的 `code_generations`（显示 summary / 任务摘要）
- TextArea：`context_text`（可选）
- 提交「生成测试建议」
- 历史 Table + 结果区：策略、用例表（name/type/steps/expected）、`test_files` 用 `<pre>` 展示

进入 Tab 时已加载的 `generations` 列表可复用；若无则 `loadGenerations` 在页面 init 已调用，下拉用 `generations.filter(succeeded)`。

---

## 8. 测试

`tests/test_test_generations.py`：

| 用例 | 期望 |
|------|------|
| 仅 target_description + Mock 成功 | 201 succeeded |
| 关联 succeeded code_generation | 201 + FK |
| 无效 code_generation_id | 400 invalid_code_generation |
| 空 target_description | 422 |
| LLM 抛错 | 201 failed |
| 越权 | 404 |

`pytest -q` 预期在 25 基础上 +6。

---

## 9. 依赖关系

无新增 pip/npm 依赖。

---

## 10. ADR

1. **扩展 Provider**：共享 OpenAI 客户端。  
2. **FK 到 code_generations**：编码→测试链路。  
3. **400 给坏 code_generation_id**：语义清晰。  
4. **不执行 pytest**：Service 无 subprocess / 无 Path.write。  
5. **表名 test_generations**：与 pytest 测试文件 `test_*.py` 命名空间分离（模型 `TestGeneration` 在 `app.models`）。

---

## 11. 文档

- `README.md` Phase 7 段落  
- `specs/phase-7-automated-testing/tasks.md`  

回复 **开始执行** 后按 tasks 改代码。
