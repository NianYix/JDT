# AI Engineering Copilot — Phase 6 Design（AI Coding）

> 基于已确认的 `requirements.md`  
> 状态：待用户回复「开始执行」后实施

## 1. 架构概览

```text
Frontend ProjectDetail Tabs
  ├─ 项目信息
  ├─ 需求分析（Phase 4）
  ├─ 技术规划（Phase 5）
  └─ AI 编码（Phase 6）
        POST/GET /api/v1/projects/{id}/code-generations
              └─ CodeGenerationService
                    ├─ ProjectRepository / TechnicalPlanRepository
                    ├─ CodeGenerationRepository
                    └─ LLMProvider.generate_code(context)
```

复用 Phase 4/5 LLM 工厂与 `LLM_*` 配置；扩展 Provider 协议，不新建 Provider 类。

---

## 2. 数据模型

### 2.1 表 `code_generations`

| 列 | 类型 | 说明 |
|----|------|------|
| id | UUID PK | |
| project_id | UUID FK projects CASCADE | indexed |
| technical_plan_id | UUID FK technical_plans NULL | indexed, nullable |
| created_by | UUID FK users CASCADE | |
| task_description | Text | 编码任务描述（快照） |
| context_text | Text NULL | 用户补充上下文 |
| status | String(32) | pending / succeeded / failed |
| result_json | JSON NULL | |
| model_name | String(128) NULL | |
| error_message | Text NULL | |
| created_at / updated_at | DateTime(tz) | |

### 2.2 结果 JSON（Pydantic `CodeGenerationResult`）

```json
{
  "summary": "string",
  "approach": "string",
  "files": [
    {
      "path": "backend/app/api/v1/example.py",
      "language": "python",
      "description": "API route",
      "content": "..."
    }
  ],
  "dependencies": ["fastapi", "pydantic"],
  "implementation_steps": ["step 1", "step 2"],
  "testing_notes": ["pytest case ..."],
  "risks": ["security ..."],
  "open_questions": ["need OAuth?"]
}
```

`files` 每项固定 `{ path, language, description, content }`；缺省字段在 schema 层用空字符串 / 空列表。

---

## 3. Backend 分层

```text
app/models/code_generation.py
app/schemas/code_generation.py
app/repositories/code_generation_repository.py
app/services/code_generation_service.py
app/api/v1/code_generations.py
app/services/llm/base.py              # + generate_code
app/services/llm/openai_provider.py   # + CODE_SYSTEM_PROMPT
```

Alembic：`20260329_0004_create_code_generations.py`（`down_revision = 20260328_0003`）。

`app/models/__init__.py` 导出 `CodeGeneration`（供 `init_db` / Alembic autoload）。

---

## 4. Service 逻辑

### 4.1 创建请求 `CodeGenerationCreate`

```python
technical_plan_id: UUID | None = None
task_description: str = Field(..., min_length=1, max_length=100_000)
context_text: str | None = Field(None, max_length=100_000)
```

`task_description` 在 schema 层 strip 后校验非空 → 422。

### 4.2 关联技术规划

若提供 `technical_plan_id`：

1. `TechnicalPlanRepository.get_by_id_for_project(id, project_id)`
2. 不存在或 `status != succeeded` → **400** `invalid_technical_plan`

### 4.3 Prompt 上下文拼装

```text
--- Coding Task ---
{task_description}

--- Technical Plan (JSON) ---
{result_json 序列化，或规划 context_text 兜底}

--- Additional Context ---
{context_text}
```

仅任务描述时只传 Coding Task 段。

### 4.4 LLM 与状态

与 Phase 4/5 一致：

- `get_llm_provider()` 无 Key → **503** `llm_not_configured`，**不写库**
- 先 insert `pending` → 调 `generate_code` → `succeeded` / `failed` 更新

### 4.5 列表与详情

越权 Project → **404** `project_not_found`；记录不存在 → **404** `code_generation_not_found`。

---

## 5. API

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/v1/projects/{project_id}/code-generations` | 201 |
| GET | `/api/v1/projects/{project_id}/code-generations` | 分页 `page` / `page_size` |
| GET | `/api/v1/projects/{project_id}/code-generations/{id}` | 详情 |

挂载 `app/api/router.py`；标签 `code-generations`。

---

## 6. LLM Provider

### 6.1 协议扩展

```python
def generate_code(self, context: str) -> CodeGenerationResult: ...
```

### 6.2 `CODE_SYSTEM_PROMPT`

要求仅返回合法 JSON，键与 `CodeGenerationResult` 对齐；`files` 为对象数组；内容与输入语言一致。

### 6.3 解析

复用 `openai_provider._parse_json_content` → `CodeGenerationResult.model_validate(payload)`。

---

## 7. Frontend

### 7.1 API 客户端

`frontend/src/api/codeGenerations.ts`：

- `createCodeGeneration(projectId, payload)`
- `listCodeGenerations(projectId)`
- `getCodeGeneration(projectId, id)`

### 7.2 UI（`ProjectDetailPage`）

Tabs 增加第四项 **「AI 编码」**：

- TextArea：`task_description`（必填）
- Select：本项目 `status=succeeded` 的技术规划（显示 `summary` + 时间）
- TextArea：`context_text`（可选）
- 提交「生成代码建议」
- 历史 Table（状态、摘要、时间）
- 结果区：summary、approach、步骤列表、依赖、风险
- 每个 `files[]`：`Typography` 标题 + `<pre>` 展示 `content`（path / language / description）

进入 Tab 时加载 succeeded 技术规划供下拉（与 Phase 5 加载 succeeded 分析类似）。

---

## 8. 测试

`tests/test_code_generations.py`：

| 用例 | 期望 |
|------|------|
| 仅 task_description + Mock 成功 | 201 succeeded |
| 关联 succeeded technical_plan | 201 + FK 回写 |
| 无效 technical_plan_id | 400 invalid_technical_plan |
| LLM 抛错 | 201 failed |
| 越权他人 Project | 404 |
| 空 task_description | 422 |

Mock 类实现 `generate_code`；扩展既有 Fake Provider 或新建 `_FakeCodeProvider`。

`pytest -q` 全绿（预期在 19 基础上 +5～6）。

---

## 9. 依赖关系

无新增 pip/npm 依赖。复用：

- `openai`（已有）
- FastAPI / SQLAlchemy / Pydantic（已有）
- Ant Design Tabs / Form / Table（已有）

---

## 10. ADR

1. **扩展 Provider 而非新类**：共享 OpenAI 客户端与配置。  
2. **可选 FK 到 technical_plans**：形成规划→编码链路。  
3. **400 给坏 plan_id**：同项目内 ID 存在但状态不对时语义清晰。  
4. **不写盘**：Service 层无任何 `open()` / `Path.write`；验收用 grep 保障。  
5. **同步执行**：与 Phase 4/5 一致。  
6. **表名 code_generations**：避免与未来「代码审查」实体混淆。

---

## 11. 文档

- `README.md`：Phase 6 API 表 + Frontend Tab 说明  
- `specs/phase-6-ai-coding/tasks.md`：实施勾选清单  

回复 **开始执行** 后按 `tasks.md` 改代码。
