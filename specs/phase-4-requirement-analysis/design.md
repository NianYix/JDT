# AI Engineering Copilot — Phase 4 Design（Requirement Analysis）

> 基于已确认的 `specs/phase-4-requirement-analysis/requirements.md`  
> 已确认：OpenAI 兼容 API、同步执行、纯文本、多次历史、嵌项目详情页  
> 状态：待确认后生成 `tasks.md`

## 1. 架构概览

在现有 Project 域上增加「需求分析」用例；LLM 通过可替换 Provider 接入，业务层不直接绑死某一 SDK 细节。

```text
Frontend (ProjectDetail)
  └─ POST/GET /api/v1/projects/{id}/requirement-analyses
        └─ RequirementAnalysisService
              ├─ ProjectRepository (归属校验)
              ├─ RequirementAnalysisRepository
              └─ LLMProvider (OpenAI-compatible)
                    └─ chat.completions → JSON schema-ish parse
```

**原则：**

- API → Service → Repository 不变。
- 越权继续 **404**。
- 无 LangChain/LangGraph；可用官方 `openai` Python SDK（其支持 `base_url`，兼容多数中转/本地服务）。
- 同步：HTTP 请求内完成 LLM 调用并落库。

---

## 2. 数据模型

### 2.1 表 `requirement_analyses`

| 列 | 类型 | 说明 |
|----|------|------|
| id | UUID PK | |
| project_id | UUID FK → projects.id ON DELETE CASCADE | indexed |
| source_text | Text NOT NULL | 原始需求 |
| status | String(32) NOT NULL | `pending` / `succeeded` / `failed` |
| result_json | JSON/Text NULL | 成功时的结构化结果 |
| model_name | String(128) NULL | 实际使用模型 |
| error_message | Text NULL | 失败原因 |
| created_by | UUID FK → users.id | 发起人 |
| created_at / updated_at | DateTime(tz) | |

> 同步模式下 `pending` 仅短暂存在（可选：直接写 succeeded/failed，不经 pending）。  
> **设计选定：** 创建时先插 `pending`，调用后更新为 `succeeded`/`failed`，便于排障。

### 2.2 结果 JSON Schema（逻辑结构）

```json
{
  "summary": "string",
  "goals": ["string"],
  "stakeholders": ["string"],
  "functional_requirements": ["string"],
  "non_functional_requirements": ["string"],
  "assumptions": ["string"],
  "risks": ["string"],
  "open_questions": ["string"]
}
```

Pydantic：`RequirementAnalysisResult`；持久化 `model_dump()`。

---

## 3. Backend 分层

```text
app/
  models/requirement_analysis.py
  schemas/requirement_analysis.py
  repositories/requirement_analysis_repository.py
  services/requirement_analysis_service.py
  services/llm/
    base.py          # Protocol / ABC: analyze_requirements(text) -> RequirementAnalysisResult
    openai_provider.py
    factory.py       # from settings
  api/v1/requirement_analyses.py
```

Alembic：新增 revision 建表。

---

## 4. API 设计

前缀：`/api/v1`

| Method | Path | Auth | 说明 |
|--------|------|------|------|
| POST | `/projects/{project_id}/requirement-analyses` | 是 | body: `{ "source_text": "..." }`；同步返回完整记录 |
| GET | `/projects/{project_id}/requirement-analyses` | 是 | 分页列表（本人项目） |
| GET | `/projects/{project_id}/requirement-analyses/{analysis_id}` | 是 | 详情 |

**错误码：**

| 场景 | HTTP | code |
|------|------|------|
| 项目不存在/非本人 | 404 | `project_not_found` |
| 分析不存在 | 404 | `requirement_analysis_not_found` |
| 文本为空 | 422 | 校验 |
| LLM 未配置 | 503 | `llm_not_configured` |
| LLM 调用/解析失败 | 200 记录 failed **或** 502 | **选定：HTTP 200/201 返回实体且 `status=failed`**（业务可展示）；仅配置缺失用 503 |

创建接口：成功调用 → `201` + `status=succeeded`；LLM 失败 → `201` + `status=failed` + `error_message`（仍创建记录）。  
配置缺失 → `503` 不写库或写 failed（**选定：503 不写库**，避免垃圾数据）。

---

## 5. LLM Provider

### 5.1 配置

| 变量 | 说明 | 示例 |
|------|------|------|
| `LLM_PROVIDER` | 目前仅 `openai_compatible` | `openai_compatible` |
| `LLM_API_KEY` | 密钥 | 占位 |
| `LLM_MODEL` | 模型名 | `gpt-4o-mini` |
| `LLM_BASE_URL` | 可选，兼容网关 | `https://api.openai.com/v1` |
| `LLM_TIMEOUT_SECONDS` | 超时 | `90` |
| `LLM_ENABLED` | 开关 | `true` |

### 5.2 调用方式

- 使用 `openai` SDK：`AsyncOpenAI` **或** 同步 `OpenAI`。  
- **选定：同步 `OpenAI`**，与当前同步 Service/SQLAlchemy 一致，避免半套 async。  
- Prompt：system 要求「只输出 JSON，字段固定」；user 放入 `source_text`。  
- 解析：`json.loads`；失败则尝试截取首尾 `{}` 再 parse；仍失败 → `failed`。

### 5.3 工厂

```python
def get_llm_provider(settings) -> LLMProvider:
    if not settings.llm_enabled or not settings.llm_api_key:
        raise AppError(..., code="llm_not_configured", status_code=503)
    return OpenAICompatibleProvider(...)
```

测试注入 Mock Provider，不走工厂真实性检查（Service 构造注入）。

---

## 6. Service 流程

```text
create(project_id, user, source_text):
  1. 校验 project 归属
  2. 校验 LLM 已配置（否则 503）
  3. insert pending 记录
  4. provider.analyze(source_text)
  5. 成功 → update succeeded + result_json + model_name
     失败 → update failed + error_message
  6. 返回 Public schema
```

列表/详情：先校验 project，再查记录。

---

## 7. Frontend

### 7.1 API 客户端

`frontend/src/api/requirementAnalyses.ts`

### 7.2 ProjectDetailPage 增强

- 区块「需求分析」  
- TextArea 输入原文 +「开始分析」按钮（loading）  
- 历史 Table/List：时间、状态、摘要；点开看详情（Drawer/下方面板展示结构化字段）  

失败状态：展示 `error_message`。

不新建独立路由（可选后续 `/projects/:id/requirement-analysis`）；**本阶段嵌详情页**。

---

## 8. 测试

- `tests/test_requirement_analyses.py`  
  - Mock Provider 成功/失败  
  - 未配置 LLM → 503  
  - 越权 404  
  - 列表仅本人项目数据  

`conftest` 可提供 `mock_llm_provider` fixture 覆盖依赖（Service 内可接受可选 provider 参数，或 monkeypatch factory）。

---

## 9. 依赖

新增：

- `openai`（官方 SDK）

不新增 langchain/langgraph。

---

## 10. ADR

1. **同步 OpenAI SDK**：与现有栈一致，实现快。  
2. **失败也落库（status=failed）**：便于产品侧展示；缺 Key 不落库。  
3. **Provider 接口**：后续可换 Azure/本地模型而不改 API。  
4. **不做流式/队列**：控制 Phase 4 范围。  
5. **结果 JSON 列**：灵活扩展字段，不必每加一列都迁移。

---

## 11. 待确认

1. 依赖使用官方包 **`openai`**？  
2. 创建失败（LLM 错）返回 **201 + status=failed**（推荐）？  
3. 缺 Key 返回 **503 且不写库**（推荐）？

请确认本 Design。确认后生成 `tasks.md`；回复「开始执行」后再改代码。
