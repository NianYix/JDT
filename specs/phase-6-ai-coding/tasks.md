# AI Engineering Copilot — Phase 6 Tasks（AI Coding）

> 状态：已完成

## T1 数据层

- [x] Model `CodeGeneration` + `models/__init__.py`
- [x] Alembic `20260329_0004_create_code_generations.py`
- [x] Repository：create / update / get / list_by_project
- [x] Schemas：`CodeGenerationFile`、`CodeGenerationResult`、`Create`、`Public`

## T2 LLM 扩展

- [x] `LLMProvider.generate_code(context: str)`
- [x] `OpenAICompatibleProvider` + `CODE_SYSTEM_PROMPT` + JSON parse
- [x] 复用 `_parse_json_content`

## T3 Service + API

- [x] `CodeGenerationService`（上下文拼装、technical_plan 校验 400）
- [x] `api/v1/code_generations.py` + `router.py` 挂载

## T4 测试

- [x] `tests/test_code_generations.py`
- [x] `pytest -q` 全绿（25 passed）

## T5 Frontend

- [x] `api/codeGenerations.ts`
- [x] `ProjectDetailPage` 增加 Tab「AI 编码」
- [x] `npm run build` 通过

## T6 文档

- [x] README Phase 6 API 与说明（简要）

## 明确不做

- 写 `repo_path`、扫仓库、LangChain、SSE、多轮 Chat
