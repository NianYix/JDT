# AI Engineering Copilot — Phase 8 Tasks（AI Code Review）

> 状态：已完成

## T1 数据层

- [x] Model `CodeReview` + `models/__init__.py`
- [x] Alembic `20260331_0006_create_code_reviews.py`
- [x] Repository：create / update / get / list_by_project
- [x] Schemas：`IssueItem`、`FixSuggestion`、`ReviewResult`、`Create`、`Public`

## T2 LLM 扩展

- [x] `LLMProvider.review_code(context: str)`
- [x] `OpenAICompatibleProvider` + `REVIEW_SYSTEM_PROMPT` + JSON parse
- [x] 复用 `_parse_json_content`

## T3 Service + API

- [x] `CodeReviewService`（上下文拼装、code_generation 校验 400）
- [x] `api/v1/code_reviews.py` + `router.py` 挂载

## T4 测试

- [x] `tests/test_code_reviews.py`
- [x] `pytest -q` 全绿（37 passed）

## T5 Frontend

- [x] `api/codeReviews.ts`
- [x] `ProjectDetailPage` 增加 Tab「代码审查」
- [x] `npm run build` 通过

## T6 文档

- [x] README Phase 8 API 与说明（简要）

## 明确不做

- 自动改代码、写 `repo_path`、静态分析工具、LangChain、SSE
