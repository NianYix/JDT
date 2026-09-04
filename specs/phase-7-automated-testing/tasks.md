# AI Engineering Copilot — Phase 7 Tasks（Automated Testing）

> 状态：已完成

## T1 数据层

- [x] Model `TestGeneration` + `models/__init__.py`
- [x] Alembic `20260330_0005_create_test_generations.py`
- [x] Repository：create / update / get / list_by_project
- [x] Schemas：`CaseItem`、`SuiteFileItem`、`SuiteGenerationResult`、`Create`、`Public`

## T2 LLM 扩展

- [x] `LLMProvider.generate_tests(context: str)`
- [x] `OpenAICompatibleProvider` + `TEST_SYSTEM_PROMPT` + JSON parse
- [x] 复用 `_parse_json_content`

## T3 Service + API

- [x] `TestGenerationService`（上下文拼装、code_generation 校验 400）
- [x] `api/v1/test_generations.py` + `router.py` 挂载

## T4 测试

- [x] `tests/test_test_generations.py`
- [x] `pytest -q` 全绿（31 passed）

## T5 Frontend

- [x] `api/testGenerations.ts`
- [x] `ProjectDetailPage` 增加 Tab「自动化测试」
- [x] `npm run build` 通过

## T6 文档

- [x] README Phase 7 API 与说明（简要）

## 明确不做

- 执行 pytest、写 `repo_path`、LangChain、SSE、多轮 Chat
