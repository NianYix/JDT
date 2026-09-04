# AI Engineering Copilot — Phase 9 Tasks（AI Debugging）

> 状态：已完成

## T1 数据层

- [x] Model `DebugSession` + `models/__init__.py`
- [x] Alembic `20260401_0007_create_debug_sessions.py`
- [x] Repository、Schemas（`LikelyCauseItem`、`DebugFixItem`、`DebugAnalysisResult`）

## T2 LLM 扩展

- [x] `LLMProvider.debug_issue(context: str)`
- [x] `DEBUG_SYSTEM_PROMPT`

## T3 Service + API

- [x] `DebugSessionService`（双 FK 校验）
- [x] `api/v1/debug_sessions.py` + router 挂载

## T4 测试

- [x] `tests/test_debug_sessions.py`
- [x] `pytest -q` 全绿（43 passed）

## T5 Frontend

- [x] `api/debugSessions.ts`
- [x] Tab「AI 调试」
- [x] `npm run build` 通过

## T6 文档

- [x] README Phase 9
